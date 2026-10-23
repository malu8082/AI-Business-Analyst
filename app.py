import io
import os
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------

st.set_page_config(
    page_title="AI Business Analyst",
    page_icon="📊",
    layout="wide"
)

DEFAULT_FILE = Path(__file__).parent / "Data" / "business_data.csv"
PROFIT_COL = "Profit_Calculated"

MISSING_TOKENS = ["", "na", "n/a", "nan", "null", "none", "-", "--", "?"]
NUMBER_PATTERN = r"^-?\s*(?:rs\.?|inr|[₹$€£])?\s*-?[\d,]*\.?\d+\s*%?$"
DATE_PATTERN = r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}"


# ---------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------

def get_secret(name, default=None):
    """Read a key from Streamlit secrets, or from environment variables."""
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, default)


def read_table(file_bytes, file_name):
    """Read a CSV or Excel file, whatever the delimiter or encoding."""
    buffer = io.BytesIO(file_bytes)

    if file_name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(buffer)

    for encoding in ("utf-8-sig", "latin-1"):
        for sep in (None, ","):
            try:
                buffer.seek(0)
                return pd.read_csv(
                    buffer, sep=sep, engine="python", encoding=encoding
                )
            except Exception:
                continue

    raise ValueError("The file could not be read as a CSV or Excel file.")


def text_columns(df):
    """Columns that are not numbers and not dates."""
    return [
        c for c in df.columns
        if not pd.api.types.is_numeric_dtype(df[c])
        and not pd.api.types.is_datetime64_any_dtype(df[c])
    ]


def is_id_like(df, column):
    """ID columns (order id, customer code...) should not be analysed as values."""
    series = df[column]
    name_hint = bool(
        re.search(r"(^|_)(id|index|code)($|_)", column.lower())
    )
    unique_integers = (
        len(df) > 20
        and series.nunique() == len(df)
        and bool((series.dropna() % 1 == 0).all())
    )
    return name_hint or unique_integers


def find_col(columns, keywords):
    """First column whose name contains one of the keywords."""
    for keyword in keywords:
        for column in columns:
            if keyword in column.lower():
                return column
    return None


def fmt(value):
    if abs(value) >= 100:
        return f"{value:,.0f}"
    return f"{value:,.2f}"


# ---------------------------------------------------
# DATA CLEANING
# ---------------------------------------------------

def clean_data(raw):
    """Clean any table. Returns the cleaned data, a log, and some statistics."""

    df = raw.copy()
    log = []
    stats = {
        "rows_before": len(df),
        "cols_before": df.shape[1],
        "missing_filled": 0,
        "duplicates_removed": 0,
        "outliers": {},
    }

    # 1. Standardise column names
    new_names = []
    for column in df.columns:
        name = re.sub(r"[^0-9a-zA-Z]+", "_", str(column).strip()).strip("_")
        new_names.append(name or "Column")

    counts = {}
    unique_names = []
    for name in new_names:
        if name in counts:
            counts[name] += 1
            unique_names.append(f"{name}_{counts[name]}")
        else:
            counts[name] = 0
            unique_names.append(name)

    if unique_names != [str(c) for c in df.columns]:
        log.append(
            "Standardised column names "
            "(spaces and symbols replaced with underscores)."
        )
    df.columns = unique_names

    # 2. Remove completely empty rows and columns
    rows, cols = df.shape
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if rows - len(df):
        log.append(f"Removed {rows - len(df)} completely empty rows.")
    if cols - df.shape[1]:
        log.append(f"Removed {cols - df.shape[1]} completely empty columns.")

    # 3. Clean text: extra spaces and fake blanks such as "N/A" or "-"
    for column in text_columns(df):
        cleaned = (
            df[column].astype(str).str.strip()
            .str.replace(r"\s+", " ", regex=True)
        )
        df[column] = cleaned.where(
            ~cleaned.str.lower().isin(MISSING_TOKENS), other=np.nan
        )

    # 4. Numbers stored as text (for example "₹1,200" or "15%")
    for column in text_columns(df):
        values = df[column].dropna().astype(str)
        if len(values) == 0:
            continue
        looks_numeric = values.str.match(NUMBER_PATTERN, case=False)
        if looks_numeric.mean() >= 0.8:
            digits_only = (
                df[column].astype(str)
                .str.replace(r"[^\d.\-]", "", regex=True)
            )
            df[column] = pd.to_numeric(digits_only, errors="coerce")
            log.append(f"Converted '{column}' from text to numbers.")

    # 5. Dates stored as text
    for column in text_columns(df):
        values = df[column].dropna().astype(str)
        if len(values) == 0:
            continue
        date_like = values.str.contains(DATE_PATTERN).mean() >= 0.8
        if date_like or "date" in column.lower():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    parsed = pd.to_datetime(
                        df[column], errors="coerce", format="mixed"
                    )
                except (TypeError, ValueError):
                    parsed = pd.to_datetime(df[column], errors="coerce")
            if parsed.notna().sum() >= 0.8 * df[column].notna().sum():
                df[column] = parsed
                log.append(f"Converted '{column}' to a date column.")

    # 6. Drop columns that are mostly empty
    missing_share = df.isna().mean()
    too_empty = missing_share[missing_share > 0.6].index.tolist()
    if too_empty:
        df = df.drop(columns=too_empty)
        log.append(
            "Dropped columns with more than 60% missing values: "
            + ", ".join(too_empty) + "."
        )

    # 7. Fill missing values
    for column in df.columns:
        missing = int(df[column].isna().sum())
        if missing == 0:
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].fillna(df[column].median())
            stats["missing_filled"] += missing
            log.append(
                f"Filled {missing} missing values in '{column}' "
                f"with the median."
            )
        elif pd.api.types.is_datetime64_any_dtype(df[column]):
            log.append(
                f"'{column}' has {missing} missing dates "
                f"(left empty, ignored in trend charts)."
            )
        else:
            df[column] = df[column].fillna("Unknown")
            stats["missing_filled"] += missing
            log.append(
                f"Filled {missing} missing values in '{column}' "
                f"with 'Unknown'."
            )

    # 8. Make category spelling consistent ("kerala", "KERALA" -> "Kerala")
    for column in text_columns(df):
        if df[column].nunique() > 50:
            continue
        lowered = df[column].str.lower()
        most_common = df[column].groupby(lowered).agg(
            lambda x: x.value_counts().idxmax()
        )
        unified = lowered.map(most_common)
        changed = int((unified != df[column]).sum())
        if changed:
            df[column] = unified
            log.append(
                f"Made spelling and capital letters consistent "
                f"in '{column}' ({changed} values)."
            )

    # 9. Remove duplicate rows
    duplicates = int(df.duplicated().sum())
    if duplicates:
        df = df.drop_duplicates().reset_index(drop=True)
        stats["duplicates_removed"] = duplicates
        log.append(f"Removed {duplicates} duplicate rows.")

    # 10. Flag possible outliers (reported only, never deleted)
    for column in df.columns:
        if (
            pd.api.types.is_numeric_dtype(df[column])
            and not is_id_like(df, column)
        ):
            q1, q3 = df[column].quantile([0.25, 0.75])
            spread = q3 - q1
            if spread > 0:
                outside = (
                    (df[column] < q1 - 1.5 * spread)
                    | (df[column] > q3 + 1.5 * spread)
                ).sum()
                if outside:
                    stats["outliers"][column] = int(outside)

    stats["rows_after"] = len(df)
    stats["cols_after"] = df.shape[1]

    if not log:
        log.append("The data was already clean. No changes were needed.")

    return df, log, stats


@st.cache_data(show_spinner=False)
def load_and_clean(file_bytes, file_name):
    return clean_data(read_table(file_bytes, file_name))


# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("📊 AI Business Analyst Agent")

st.write(
    "Upload any business data file. The agent cleans it, builds a "
    "dashboard, identifies trends, and finds potential process problems."
)

# ---------------------------------------------------
# LOAD BUSINESS DATA
# ---------------------------------------------------

st.sidebar.header("📁 Data")

uploaded = st.sidebar.file_uploader(
    "Upload a CSV or Excel file",
    type=["csv", "xlsx", "xls"]
)

if uploaded is not None:
    file_bytes, file_name = uploaded.getvalue(), uploaded.name

elif DEFAULT_FILE.exists():
    file_bytes, file_name = DEFAULT_FILE.read_bytes(), DEFAULT_FILE.name
    st.sidebar.caption(
        "Showing the sample data. Upload a file to analyse your own."
    )

else:
    st.info("Upload a CSV or Excel file in the sidebar to begin.")
    st.stop()

try:
    df, clean_log, stats = load_and_clean(file_bytes, file_name)
except Exception as e:
    st.error(f"Could not load the business data: {e}")
    st.stop()

if df.empty:
    st.error("The file has no usable rows after cleaning.")
    st.stop()

st.success(f"Business data loaded successfully: {file_name}")

# ---------------------------------------------------
# DATA CLEANING REPORT
# ---------------------------------------------------

st.header("🧹 Data Cleaning Report")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows (before → after)",
          f"{stats['rows_before']:,} → {stats['rows_after']:,}")
c2.metric("Columns (before → after)",
          f"{stats['cols_before']} → {stats['cols_after']}")
c3.metric("Duplicates Removed", f"{stats['duplicates_removed']:,}")
c4.metric("Missing Values Filled", f"{stats['missing_filled']:,}")

with st.expander("What the agent cleaned", expanded=True):
    for item in clean_log:
        st.write(f"• {item}")

    if stats["outliers"]:
        st.write(
            "**Possible outliers (kept in the data, please review):** "
            + ", ".join(f"{c} ({n})" for c, n in stats["outliers"].items())
        )

# ---------------------------------------------------
# DETECT COLUMNS AUTOMATICALLY
# ---------------------------------------------------

numeric_cols = [
    c for c in df.columns
    if pd.api.types.is_numeric_dtype(df[c])
    and not pd.api.types.is_bool_dtype(df[c])
    and not is_id_like(df, c)
]
date_cols = [
    c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])
]
category_cols = [
    c for c in text_columns(df) if 2 <= df[c].nunique() <= 30
]

if not numeric_cols:
    st.header("📋 Business Data")
    st.dataframe(df)
    st.error(
        "No numeric columns were found, so a dashboard cannot be built. "
        "Check that the file contains numbers such as revenue or quantity."
    )
    st.stop()

# ---------------------------------------------------
# SIDEBAR: COLUMN SELECTION (auto-detected, can be changed)
# ---------------------------------------------------

st.sidebar.header("⚙️ Column Selection")
st.sidebar.caption("The agent guessed these from your data. Change if needed.")

default_metric = (
    find_col(numeric_cols, ["revenue", "sales", "amount", "income", "price", "total"])
    or numeric_cols[0]
)
metric = st.sidebar.selectbox(
    "Main value column",
    numeric_cols,
    index=numeric_cols.index(default_metric)
)

agg_choice = st.sidebar.radio(
    "Combine values by", ["Sum", "Average"], horizontal=True
)
agg_func = "sum" if agg_choice == "Sum" else "mean"

currency = st.sidebar.text_input("Currency symbol (optional)", value="₹")

cost_options = ["None"] + [c for c in numeric_cols if c != metric]
default_cost = find_col(cost_options[1:], ["cost", "expense"])
cost_choice = st.sidebar.selectbox(
    "Cost column (to calculate profit)",
    cost_options,
    index=cost_options.index(default_cost) if default_cost else 0
)
cost_col = None if cost_choice == "None" else cost_choice

status_options = ["None"] + category_cols
default_status = find_col(category_cols, ["status"])
status_choice = st.sidebar.selectbox(
    "Status column",
    status_options,
    index=status_options.index(default_status) if default_status else 0
)
status_col = None if status_choice == "None" else status_choice

group_options = [c for c in category_cols if c != status_col]
default_groups = [
    c for c in group_options
    if any(k in c.lower() for k in [
        "region", "product", "category", "department",
        "segment", "city", "state", "type"
    ])
][:2] or group_options[:2]
group_cols = st.sidebar.multiselect(
    "Group by (max 2)", group_options, default=default_groups,
    max_selections=2
)

time_options = [c for c in numeric_cols if c not in (metric, cost_col)]
default_times = [
    c for c in time_options
    if any(k in c.lower() for k in [
        "time", "duration", "days", "hours", "delay", "lead"
    ])
][:2]
time_cols = st.sidebar.multiselect(
    "Time / duration columns (max 2)", time_options, default=default_times,
    max_selections=2
)

date_options = ["None"] + date_cols
default_date = find_col(date_cols, ["date"]) or (date_cols[0] if date_cols else None)
date_choice = st.sidebar.selectbox(
    "Date column",
    date_options,
    index=date_options.index(default_date) if default_date else 0
)
date_col = None if date_choice == "None" else date_choice

# ---------------------------------------------------
# DATA PREPARATION
# ---------------------------------------------------

if cost_col:
    df[PROFIT_COL] = df[metric] - df[cost_col]

# ---------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------

total_records = len(df)
metric_total = df[metric].sum()
metric_value = df[metric].sum() if agg_func == "sum" else df[metric].mean()
value_label = "Total" if agg_func == "sum" else "Average"

kpis = [
    ("Total Records", f"{total_records:,}"),
    (f"{value_label} {metric}", f"{currency}{fmt(metric_value)}"),
    (f"Average {metric} per Record", f"{currency}{fmt(df[metric].mean())}"),
]

if cost_col:
    total_profit = df[PROFIT_COL].sum()
    margin = total_profit / metric_total * 100 if metric_total else 0
    kpis.append(("Total Profit", f"{currency}{fmt(total_profit)}"))
    kpis.append(("Profit Margin", f"{margin:.1f}%"))
else:
    kpis.append((f"Highest {metric}", f"{currency}{fmt(df[metric].max())}"))

delay_values = []
if status_col:
    shares = df[status_col].value_counts(normalize=True) * 100
    for status_value, share in shares.head(3).items():
        kpis.append((f"{status_value} Records", f"{share:.1f}%"))
    delay_values = [
        v for v in df[status_col].unique() if "delay" in str(v).lower()
    ]

for t in time_cols:
    kpis.append((f"Avg {t}", f"{df[t].mean():.1f}"))

# ---------------------------------------------------
# KPI DASHBOARD
# ---------------------------------------------------

st.header("📈 Business Performance")

for start in range(0, len(kpis), 4):
    columns = st.columns(4)
    for column, (label, value) in zip(columns, kpis[start:start + 4]):
        column.metric(label, value)

# ---------------------------------------------------
# CLEANED DATA
# ---------------------------------------------------

st.header("📋 Business Data (cleaned)")

st.dataframe(df)

st.download_button(
    "⬇️ Download cleaned data (CSV)",
    df.to_csv(index=False).encode("utf-8"),
    file_name="cleaned_data.csv",
    mime="text/csv"
)

# ---------------------------------------------------
# VALUE AND PROFIT BY GROUP
# ---------------------------------------------------

for group in group_cols:

    st.header(f"🌍 {metric} by {group}")

    by_group = df.groupby(group)[metric].agg(agg_func).sort_values(ascending=False)
    st.bar_chart(by_group)

    if cost_col:
        st.subheader(f"💰 Profit by {group}")
        profit_by_group = (
            df.groupby(group)[PROFIT_COL].agg(agg_func)
            .sort_values(ascending=False)
        )
        st.bar_chart(profit_by_group)

# ---------------------------------------------------
# TREND OVER TIME
# ---------------------------------------------------

trend = None

if date_col:
    dated = df.dropna(subset=[date_col])

    if len(dated) > 1:
        span_days = (dated[date_col].max() - dated[date_col].min()).days
        frequency = "D" if span_days <= 62 else "MS"

        trend = (
            dated.set_index(date_col)[metric]
            .resample(frequency).agg(agg_func)
        )

        st.header("📅 Trend Over Time")
        st.caption(
            f"{metric} per {'day' if frequency == 'D' else 'month'}"
        )
        st.line_chart(trend)

# ---------------------------------------------------
# STATUS
# ---------------------------------------------------

if status_col:
    st.header(f"🚚 {status_col}")
    st.bar_chart(df[status_col].value_counts())

# ---------------------------------------------------
# BASIC BUSINESS INSIGHTS
# ---------------------------------------------------

st.header("💡 Initial Business Insights")

if not group_cols:
    st.info("Select a 'Group by' column in the sidebar to see insights.")

for group in group_cols:
    by_group = df.groupby(group)[metric].agg(agg_func)

    st.write(
        f"🏆 **Highest {metric} by {group}:** "
        f"{by_group.idxmax()} ({fmt(by_group.max())})"
    )
    st.write(
        f"📉 **Lowest {metric} by {group}:** "
        f"{by_group.idxmin()} ({fmt(by_group.min())})"
    )

for t in time_cols:
    for group in group_cols:
        by_time = df.groupby(group)[t].mean()
        st.write(
            f"⚠️ **Highest average {t} by {group}:** "
            f"{by_time.idxmax()} ({by_time.max():.1f})"
        )

# ---------------------------------------------------
# DELAY ANALYSIS
# ---------------------------------------------------

st.header("⚠️ Process Delay Analysis")

if not time_cols or not group_cols:
    st.info(
        "Select at least one time / duration column and one 'Group by' "
        "column in the sidebar to see the process analysis."
    )
else:
    for t in time_cols:
        for group in group_cols:
            st.write(f"Average {t} by {group}:")
            st.bar_chart(
                df.groupby(group)[t].mean().sort_values(ascending=False)
            )

    st.info(
        "Groups with higher processing or delivery times should be "
        "investigated further for potential process bottlenecks."
    )

# ---------------------------------------------------
# ROOT-CAUSE ANALYSIS
# ---------------------------------------------------

st.header("🔎 Root-Cause Analysis")

st.write(
    "The system investigates which business areas "
    "are associated with longer processing times."
)

flagged = []

if time_cols and group_cols:

    st.subheader("⚠️ Findings")

    for t in time_cols:
        overall = df[t].mean()

        for group in group_cols:
            by_time = df.groupby(group)[t].mean()
            worst = by_time.idxmax()
            gap = (by_time.max() / overall - 1) * 100 if overall else 0

            st.write(
                f"🔴 **Highest average {t} by {group}:** {worst} "
                f"({by_time.max():.1f}, {gap:.0f}% above the "
                f"overall average of {overall:.1f})"
            )

            if gap >= 20:
                flagged.append((t, group, worst, gap))

        if len(group_cols) == 2:
            combined = df.groupby(group_cols)[t].mean()
            worst_pair = combined.idxmax()
            st.write(
                f"🎯 **Slowest combination for {t}:** "
                f"{worst_pair[0]} + {worst_pair[1]} "
                f"({combined.max():.1f})"
            )

    if status_col and delay_values:
        delayed = df[df[status_col].isin(delay_values)]

        for group in group_cols:
            delayed_by_group = (
                delayed.groupby(group).size().sort_values(ascending=False)
            )
            if len(delayed_by_group) > 0:
                st.write(
                    f"🚨 **{group} with the most delayed records:** "
                    f"{delayed_by_group.idxmax()} "
                    f"({delayed_by_group.max()} records)"
                )

    st.subheader("💼 Business Interpretation")

    if flagged:
        for t, group, worst, gap in flagged:
            st.warning(
                f"{worst} ({group}) has an average {t} that is "
                f"{gap:.0f}% above the overall average. "
                f"This should be investigated for potential "
                f"process bottlenecks."
            )
    else:
        st.success(
            "No group is more than 20% above the overall average, "
            "so no significant bottleneck was detected."
        )

    st.subheader("💡 Initial Recommendation")

    st.info(
        "Investigate the slowest group and combination first. "
        "Review approval, inventory, manual processing, and "
        "fulfillment steps to identify the underlying cause."
    )

else:
    st.info(
        "Root-cause analysis needs a time / duration column and a "
        "'Group by' column. Select them in the sidebar."
    )

# ==========================================
# AI BUSINESS ANALYST
# ==========================================


def build_summary():
    """Turn the cleaned data and results into text for the AI."""

    lines = [
        f"Dataset: {file_name}",
        f"Rows after cleaning: {len(df)}",
        f"Columns: {', '.join(df.columns)}",
        f"Main value column: {metric} (combined by {agg_choice.lower()})",
        "",
        "Data cleaning performed:",
    ]
    lines += [f"- {item}" for item in clean_log]

    lines += ["", "Key figures:"]
    lines += [f"- {label}: {value}" for label, value in kpis]

    for group in group_cols:
        columns = [metric] + ([PROFIT_COL] if cost_col else [])
        table = (
            df.groupby(group)[columns].agg(agg_func)
            .sort_values(metric, ascending=False).head(10).round(1)
        )
        lines += ["", f"{metric} by {group}:", table.to_string()]

        if time_cols:
            times = df.groupby(group)[time_cols].mean().round(2).head(10)
            lines += [f"Average time columns by {group}:", times.to_string()]

    if status_col:
        lines += [
            "",
            f"{status_col} counts:",
            df[status_col].value_counts().head(10).to_string()
        ]

    if trend is not None:
        lines += ["", f"{metric} trend (latest periods):",
                  trend.tail(12).round(1).to_string()]

    others = [c for c in numeric_cols if c != metric][:8]
    if others:
        lines += ["", "Other numeric columns:",
                  df[others].describe().round(2).T.to_string()]

    return "\n".join(lines)


st.divider()

st.divider()

st.subheader("🤖 AI Business Analyst")

st.write(
    "Chat with your AI Business Analyst about your business data. "
    "It remembers previous questions during the current session."
)

# Initialize conversation history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_question = st.chat_input(
    "Ask a question about your business data..."
)

if user_question:
    question = user_question.strip()[:500]

    if question:
        # Display the user's question
        st.session_state.chat_history.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        api_key = get_secret("GEMINI_API_KEY")

        if not api_key:
            st.error(
                "Gemini API key not found. Please check your "
                "local .env file or Streamlit secrets."
            )

        else:
            try:
                from google import genai

                client = genai.Client(api_key=api_key)
                model_name = get_secret(
                    "GEMINI_MODEL",
                    "gemini-3.5-flash-lite"
                )

                # Include recent conversation history
                conversation = st.session_state.chat_history[-4:]

                conversation_text = "\n".join(
                    f'{message["role"].upper()}: {message["content"]}'
                    for message in conversation
                )

                prompt = f"""
You are an experienced Business Analyst.

Analyze the business data and answer the stakeholder's questions
clearly and professionally.

BUSINESS DATA SUMMARY:
{build_summary()}

CONVERSATION HISTORY:
{conversation_text}

INSTRUCTIONS:
- Answer the latest user question.
- Use the conversation history to understand follow-up questions.
- Use only the business data provided for data-related claims.
- Do not invent statistics or unsupported facts.
- If the data cannot answer a question, explain why.
- Recommend practical actions when appropriate.
- Keep the response clear and suitable for a business stakeholder.

Provide a useful answer to the latest question.
"""

                with st.chat_message("assistant"):
                    with st.spinner(
                        "AI Business Analyst is thinking..."
                    ):
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config={
                                "max_output_tokens": 250,
                                "temperature": 0.3
                            }
                        )

                    answer = (
                        response.text
                        or "The AI returned an empty answer."
                    )

                    st.markdown(answer)

                # Save the assistant's response
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as e:
                st.error(f"AI request failed: {e}")