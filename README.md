# 🛒 AI-Powered Retail Intelligence Copilot

An AI-powered Retail Intelligence System that enables non-technical business users to query retail datasets using natural language and receive grounded, traceable business insights. The system leverages LLMs, SQL analytics, and AI agents to perform forecasting, anomaly detection, inventory analysis, trend analysis, and store performance evaluation.

---

## 🚀 Features

✅ Natural Language → SQL Analytics  
✅ Retail Data Querying using AI Agents  
✅ Store Performance Analysis  
✅ Quarter-over-Quarter (QoQ) Trend Detection  
✅ Inventory Risk & Stockout Detection  
✅ Promotion/Event Analysis  
✅ Revenue Forecasting  
✅ Anomaly Detection using Z-Score  
✅ Multi-table SQL Query Support  
✅ Row-level Traceability (source_row_id citations)  
✅ Persistent Chat Memory using SQLite  
✅ AI Tool Calling with LangGraph + LangChain  

---

# 📌 Problem Statement

Business stakeholders often depend on technical teams to generate SQL reports or analyze retail data. This project removes that dependency by allowing users to ask questions in natural language such as:

- Why did Mumbai electronics revenue drop?
- Which stores are at highest risk next quarter?
- Show promotions during Diwali week.
- Compare top-performing stores.
- Detect unusual sales spikes or drops.

The AI agent converts these questions into analytical workflows and provides evidence-backed answers.

---

# 🏗️ Architecture

```plaintext
User Query
      ↓
OpenAI GPT-4o-mini (LLM)
      ↓
LangGraph Agent Workflow
      ↓
Tool Selection
      ↓
DuckDB SQL Queries
      ↓
Retail Dataset Analysis
      ↓
Business Insight Generation
      ↓
Evidence + Citations
```

---

# 🛠️ Tech Stack

## Programming Language
- Python

## AI / LLM
- OpenAI GPT-4o-mini
- LangChain
- LangGraph

## Database
- DuckDB
- SQLite

## Data Processing
- CSV datasets
- SQL Analytics

## Utilities
- dotenv
- Regex
- OS module

---

# 📂 Project Structure

```plaintext
AI-Powered-Retail-Intelligence-Copilot/
│
├── data/
│      sales.csv
│      stores.csv
│      inventory.csv
│      promotions.csv
│
├── chatbot.py
├── retail.duckdb
├── chatbot.db
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

---

# ⚙️ Installation

Clone repository:

```bash
git clone https://github.com/your-username/AI-Powered-Retail-Intelligence-Copilot.git

cd AI-Powered-Retail-Intelligence-Copilot
```

Create virtual environment:

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create `.env`

Example:

```env
OPENAI_API_KEY=your_openai_api_key
DATASET_FOLDER=data
```

---

# ▶️ Run Project

Run:

```bash
python chatbot.py
```

---

# 📊 Example Queries

Users can ask:

```plaintext
Why did Mumbai electronics revenue drop?

Show top-performing stores.

Forecast next quarter revenue.

Find inventory risks.

Which promotions overlapped during Diwali?

Detect unusual revenue spikes.
```

---

# 🧠 AI Tools Implemented

The project includes custom AI tools:

| Tool | Purpose |
|------|----------|
| list_available_tables() | Shows schema and tables |
| query_retail_data() | Runs SQL queries |
| resolve_business_entity() | Resolves business terms |
| get_qoq_trend() | Calculates QoQ growth |
| get_store_performance() | Ranks stores |
| find_store_events() | Detects promotions |
| get_inventory_health() | Finds stock risks |
| detect_retail_anomalies() | Detects anomalies |
| forecast_next_quarter() | Forecasting |
| run_anomaly_investigation() | Root cause analysis |
| calculator() | Basic calculations |

---

# 📈 Workflow

1. Load CSV datasets
2. Convert CSV → DuckDB tables
3. Extract schema
4. User asks natural language question
5. LLM interprets intent
6. LangGraph selects appropriate tool
7. SQL executed on DuckDB
8. Results analyzed
9. Evidence-backed answer generated

---

# 🔍 Example Use Cases

### Revenue Analysis
Identify revenue decline across regions.

### Inventory Monitoring
Detect low-stock SKUs.

### Promotion Analysis
Analyze event impacts.

### Forecasting
Predict next quarter performance.

### Anomaly Detection
Detect unusual spikes or drops.

---

# 📌 Future Improvements

- Real-time dashboard
- Multi-agent workflow
- Fine-tuned forecasting models
- Advanced ML forecasting
- Interactive Streamlit UI
- Automated recommendation engine

---

# 🎯 Key Learnings

- AI Agent Development
- LangGraph Workflows
- LLM Tool Calling
- SQL Analytics
- Business Intelligence
- Forecasting Techniques
- Anomaly Detection

---

# 👩‍💻 Author

**Ritika Kumari**


