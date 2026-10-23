# 🤖 AI Business Analyst

An AI-powered business analytics application that helps users explore business data, identify potential issues, and generate actionable recommendations through an interactive dashboard and conversational AI assistant.

## 📌 Project Overview

Business teams often need to understand performance data, identify operational problems, and decide what actions to take.

The **AI Business Analyst** combines data analysis and generative AI to help users explore business datasets, understand key findings, and ask follow-up questions in a conversational interface.

This project demonstrates how data analytics, business analysis, and AI can work together to support better business decisions.

## 🎯 Project Objectives

- Analyze uploaded business datasets.
- Identify important business metrics and trends.
- Help users investigate potential operational issues.
- Generate AI-powered business insights and recommendations.
- Support follow-up questions through conversational memory.
- Present findings through an interactive dashboard.

## ✨ Key Features

### 📂 1. Business Data Upload
Upload a supported business dataset for analysis.

### 🧹 2. Data Preparation
Prepare uploaded data for analysis and handle common data-quality issues.

### 📊 3. Interactive Dashboard
Explore business performance using metrics, charts, and summaries.

### 🔎 4. Business Analysis
Investigate business questions and explore potential causes of performance issues.

### 🤖 5. Conversational AI Assistant
Ask questions about the uploaded data and ask follow-up questions within the current session.

### 💡 6. AI-Generated Recommendations
Receive structured business analysis, including key findings, possible root causes, business impact, recommended actions, and KPIs to monitor.

## 🛠️ Technologies Used

- **Python** — application logic and data processing
- **Streamlit** — interactive web application
- **Pandas** — data preparation and analysis
- **Google Gemini API** — AI-powered business analysis
- **Git and GitHub** — version control and project hosting

## ⚙️ Run the Project Locally

### Prerequisites

- Python installed
- Git (optional, for cloning the repository)
- A Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/malu8082/AI-Business-Analyst.git
cd AI-Business-Analyst
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the API key

Create a `.env` file in the project root, alongside `app.py`.

Add your own API key:

```text
GEMINI_API_KEY=your_gemini_api_key_here
```

If your application uses a configurable model, you can also add:

```text
GEMINI_MODEL=your_supported_gemini_model
```

Replace the placeholder with a model supported by your Gemini API access.

**Security:** Never commit your real API key or `.env` file to GitHub.

### 5. Start the application

```bash
streamlit run app.py
```

Streamlit will provide a local address to open in your browser.

## 💼 Business Analyst Skills Demonstrated

This project demonstrates practical experience with:

- Business problem investigation
- Exploratory data analysis
- Data preparation and quality checks
- KPI interpretation
- Root-cause investigation
- Requirements-oriented questioning
- Data-driven recommendations
- AI-assisted business analysis
- Communicating insights to business stakeholders

## 🚀 Future Improvements

- Add more robust data-quality validation.
- Support additional business datasets and column structures.
- Introduce downloadable business analysis reports.
- Add configurable analysis templates for different business functions.
- Improve error handling and response-time monitoring.
- Add automated tests for data preparation and analysis logic.

## 👩‍💻 Author

**Malavika P. S.**

Aspiring Business Analyst | Data Analytics | AI-Powered Business Solutions

---

*This project is intended as a portfolio demonstration of data analytics, business analysis, and generative AI.*
