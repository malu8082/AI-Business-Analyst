import streamlit as st
import pandas as pd

# ---------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------

st.set_page_config(
    page_title="AI Business Analyst",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("📊 AI Business Analyst Agent")

st.write(
    "Analyze business performance, identify trends, "
    "and discover potential process problems."
)

# ---------------------------------------------------
# LOAD BUSINESS DATA
# ---------------------------------------------------

file_path = "Data/business_data.csv"

try:
    df = pd.read_csv(file_path)

    st.success("Business data loaded successfully!")

except Exception as e:
    st.error(f"Could not load the business data: {e}")
    st.stop()

# ---------------------------------------------------
# DATA PREPARATION
# ---------------------------------------------------

df["Order_Date"] = pd.to_datetime(df["Order_Date"])

df["Profit"] = df["Revenue"] - df["Cost"]

df["Profit_Margin"] = (
    df["Profit"] / df["Revenue"] * 100
)

# ---------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------

total_revenue = df["Revenue"].sum()

total_cost = df["Cost"].sum()

total_profit = df["Profit"].sum()

total_orders = len(df)

average_order_value = df["Revenue"].mean()

delayed_orders = (df["Order_Status"] == "Delayed").sum()

cancelled_orders = (df["Order_Status"] == "Cancelled").sum()

delayed_percentage = delayed_orders / total_orders * 100

cancelled_percentage = cancelled_orders / total_orders * 100

average_processing_time = df["Processing_Time"].mean()

average_delivery_time = df["Delivery_Time"].mean()

# ---------------------------------------------------
# KPI DASHBOARD
# ---------------------------------------------------

st.header("📈 Business Performance")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    f"₹{total_revenue:,.0f}"
)

col2.metric(
    "Total Profit",
    f"₹{total_profit:,.0f}"
)

col3.metric(
    "Total Orders",
    f"{total_orders:,}"
)

col4.metric(
    "Average Order Value",
    f"₹{average_order_value:,.0f}"
)

col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Delayed Orders",
    f"{delayed_percentage:.1f}%"
)

col6.metric(
    "Cancelled Orders",
    f"{cancelled_percentage:.1f}%"
)

col7.metric(
    "Avg Processing Time",
    f"{average_processing_time:.1f} hrs"
)

col8.metric(
    "Avg Delivery Time",
    f"{average_delivery_time:.1f} days"
)

# ---------------------------------------------------
# RAW DATA
# ---------------------------------------------------

st.header("📋 Business Data")

st.dataframe(
    df,
    use_container_width=True
)

# ---------------------------------------------------
# REVENUE BY REGION
# ---------------------------------------------------

st.header("🌍 Revenue by Region")

region_revenue = (
    df.groupby("Region")["Revenue"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(region_revenue)

# ---------------------------------------------------
# PROFIT BY REGION
# ---------------------------------------------------

st.header("💰 Profit by Region")

region_profit = (
    df.groupby("Region")["Profit"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(region_profit)

# ---------------------------------------------------
# REVENUE BY PRODUCT
# ---------------------------------------------------

st.header("📦 Revenue by Product")

product_revenue = (
    df.groupby("Product")["Revenue"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(product_revenue)

# ---------------------------------------------------
# ORDER STATUS
# ---------------------------------------------------

st.header("🚚 Order Status")

order_status = df["Order_Status"].value_counts()

st.bar_chart(order_status)

# ---------------------------------------------------
# BASIC BUSINESS INSIGHTS
# ---------------------------------------------------

st.header("💡 Initial Business Insights")

best_region = region_revenue.idxmax()

best_product = product_revenue.idxmax()

worst_region = region_revenue.idxmin()

highest_delay_region = (
    df.groupby("Region")["Processing_Time"]
    .mean()
    .idxmax()
)

st.write(
    f"🏆 **Highest revenue region:** {best_region}"
)

st.write(
    f"📦 **Highest revenue product:** {best_product}"
)

st.write(
    f"📉 **Lowest revenue region:** {worst_region}"
)

st.write(
    f"⚠️ **Highest average processing time:** "
    f"{highest_delay_region}"
)

# ---------------------------------------------------
# DELAY ANALYSIS
# ---------------------------------------------------

st.header("⚠️ Process Delay Analysis")

delay_by_region = (
    df.groupby("Region")["Processing_Time"]
    .mean()
    .sort_values(ascending=False)
)

st.write("Average processing time by region:")

st.bar_chart(delay_by_region)

st.info(
    "The regions with higher processing times should be "
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

# Average processing time by region
processing_by_region = (
    df.groupby("Region")["Processing_Time"]
    .mean()
    .sort_values(ascending=False)
)

# Region with highest processing time
worst_processing_region = processing_by_region.idxmax()

worst_processing_time = processing_by_region.max()

# Average processing time by product
processing_by_product = (
    df.groupby("Product")["Processing_Time"]
    .mean()
    .sort_values(ascending=False)
)

worst_processing_product = processing_by_product.idxmax()

worst_product_processing_time = processing_by_product.max()

# Delayed orders by region
delayed_by_region = (
    df[df["Order_Status"] == "Delayed"]
    .groupby("Region")
    .size()
    .sort_values(ascending=False)
)

if len(delayed_by_region) > 0:

    worst_delay_region = delayed_by_region.idxmax()

    worst_delay_count = delayed_by_region.max()

else:

    worst_delay_region = "None"

    worst_delay_count = 0


# Display analysis
st.subheader("📍 Processing Time by Region")

st.bar_chart(processing_by_region)


st.subheader("📦 Processing Time by Product")

st.bar_chart(processing_by_product)


# Root-cause findings

st.subheader("⚠️ Findings")

st.write(
    f"🔴 **Highest processing-time region:** "
    f"{worst_processing_region} "
    f"({worst_processing_time:.1f} hours)"
)

st.write(
    f"📦 **Highest processing-time product:** "
    f"{worst_processing_product} "
    f"({worst_product_processing_time:.1f} hours)"
)

st.write(
    f"🚨 **Region with the most delayed orders:** "
    f"{worst_delay_region} "
    f"({worst_delay_count} delayed orders)"
)


# Business interpretation

st.subheader("💼 Business Interpretation")

if worst_processing_time > average_processing_time:

    st.warning(
        f"The {worst_processing_region} region has a "
        f"higher-than-average processing time. "
        f"This region should be investigated for "
        f"potential process bottlenecks."
    )

else:

    st.success(
        "No significant regional processing bottleneck "
        "was detected."
    )


if worst_product_processing_time > average_processing_time:

    st.warning(
        f"{worst_processing_product} orders have the "
        f"highest average processing time. "
        f"The business should investigate the workflow "
        f"for this product."
    )


# Recommendation

st.subheader("💡 Initial Recommendation")

st.info(
    "Investigate the highest-delay region and product "
    "combination first. Review approval, inventory, "
    "manual processing, and fulfillment steps to "
    "identify the underlying cause."
)

# ==========================================
# AI BUSINESS ANALYST
# ==========================================

st.divider()

st.subheader("🤖 AI Business Analyst")

st.write(
    "Ask Gemini to analyze the business data and provide "
    "business-focused insights and recommendations."
)

user_question = st.text_input(
    "What would you like the AI Business Analyst to investigate?",
    placeholder="Example: Why are orders being delayed?"
)

if st.button("🔍 Analyze with AI"):

    if user_question:

        from google import genai

        client = genai.Client()

        # Convert the important business information into text
        business_summary = f"""
Business Performance Summary:

Total Revenue: ₹{df['Revenue'].sum():,.0f}
Total Profit: ₹{df['Profit'].sum():,.0f}
Total Orders: {len(df)}

Delayed Orders: {(df['Order_Status'] == 'Delayed').sum()}
Cancelled Orders: {(df['Order_Status'] == 'Cancelled').sum()}

Average Processing Time:
{df['Processing_Time'].mean():.1f} hours

Average Delivery Time:
{df['Delivery_Time'].mean():.1f} days

Highest Processing-Time Region:
{df.groupby('Region')['Processing_Time'].mean().idxmax()}

Highest Processing-Time Product:
{df.groupby('Product')['Processing_Time'].mean().idxmax()}
"""

        prompt = f"""
You are an experienced Business Analyst.

Analyze the following business data:

{business_summary}

The stakeholder asks:

{user_question}

Provide a professional business analysis.

Your response should include:

1. Key Finding
2. Possible Root Cause
3. Business Impact
4. Recommended Action
5. KPI to Monitor

Use the available data and do not invent statistics.
Keep the explanation clear and suitable for a business stakeholder.
"""

        with st.spinner("AI Business Analyst is analyzing the data..."):

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

        st.subheader("📊 AI Analysis")

        st.write(response.text)

    else:

        st.warning("Please enter a question first.")