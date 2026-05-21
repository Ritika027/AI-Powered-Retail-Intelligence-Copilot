# from __future__ import annotations

# import os
# import sqlite3
# import tempfile
# from typing import Annotated, Any, Dict, Optional, TypedDict
# import duckdb
# import pandas as pd

# from dotenv import load_dotenv
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_community.tools import DuckDuckGoSearchRun
# from langchain_community.vectorstores import FAISS
# from langchain_core.messages import BaseMessage, SystemMessage
# from langchain_core.tools import tool
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.graph import START, StateGraph
# from langgraph.graph.message import add_messages
# from langgraph.prebuilt import ToolNode, tools_condition
# import requests

# load_dotenv()

# # -------------------
# # 1. LLM + embeddings
# # -------------------
# llm = ChatOpenAI(model="gpt-4o-mini")
# embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# # -------------------
# # 2. PDF retriever store (per thread)
# # -------------------
# _THREAD_RETRIEVERS: Dict[str, Any] = {}
# _THREAD_METADATA: Dict[str, dict] = {}


# def _get_retriever(thread_id: Optional[str]):
#     """Fetch the retriever for a thread if available."""
#     if thread_id and thread_id in _THREAD_RETRIEVERS:
#         return _THREAD_RETRIEVERS[thread_id]
#     return None


# def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
#     """
#     Build a FAISS retriever for the uploaded PDF and store it for the thread.

#     Returns a summary dict that can be surfaced in the UI.
#     """
#     if not file_bytes:
#         raise ValueError("No bytes received for ingestion.")

#     with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
#         temp_file.write(file_bytes)
#         temp_path = temp_file.name

#     try:
#         loader = PyPDFLoader(temp_path)
#         docs = loader.load()

#         splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
#         )
#         chunks = splitter.split_documents(docs)

#         vector_store = FAISS.from_documents(chunks, embeddings)
#         retriever = vector_store.as_retriever(
#             search_type="similarity", search_kwargs={"k": 4}
#         )

#         _THREAD_RETRIEVERS[str(thread_id)] = retriever
#         _THREAD_METADATA[str(thread_id)] = {
#             "filename": filename or os.path.basename(temp_path),
#             "documents": len(docs),
#             "chunks": len(chunks),
#         }

#         return {
#             "filename": filename or os.path.basename(temp_path),
#             "documents": len(docs),
#             "chunks": len(chunks),
#         }
#     finally:
#         # The FAISS store keeps copies of the text, so the temp file is safe to remove.
#         try:
#             os.remove(temp_path)
#         except OSError:
#             pass


# # -------------------
# # 3. Tools
# # -------------------
# search_tool = DuckDuckGoSearchRun(region="us-en")


# @tool
# def calculator(first_num: float, second_num: float, operation: str) -> dict:
#     """
#     Perform a basic arithmetic operation on two numbers.
#     Supported operations: add, sub, mul, div
#     """
#     try:
#         if operation == "add":
#             result = first_num + second_num
#         elif operation == "sub":
#             result = first_num - second_num
#         elif operation == "mul":
#             result = first_num * second_num
#         elif operation == "div":
#             if second_num == 0:
#                 return {"error": "Division by zero is not allowed"}
#             result = first_num / second_num
#         else:
#             return {"error": f"Unsupported operation '{operation}'"}

#         return {
#             "first_num": first_num,
#             "second_num": second_num,
#             "operation": operation,
#             "result": result,
#         }
#     except Exception as e:
#         return {"error": str(e)}


# @tool
# def get_stock_price(symbol: str) -> dict:
#     """
#     Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
#     using Alpha Vantage with API key in the URL.
#     """
#     url = (
#         "https://www.alphavantage.co/query"
#         f"?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
#     )
#     r = requests.get(url)
#     return r.json()


# @tool
# def rag_tool(query: str, thread_id: Optional[str] = None) -> dict:
#     """
#     Retrieve relevant information from the uploaded PDF for this chat thread.
#     Always include the thread_id when calling this tool.
#     """
#     retriever = _get_retriever(thread_id)
#     if retriever is None:
#         return {
#             "error": "No document indexed for this chat. Upload a PDF first.",
#             "query": query,
#         }

#     result = retriever.invoke(query)
#     context = [doc.page_content for doc in result]
#     metadata = [doc.metadata for doc in result]

#     return {
#         "query": query,
#         "context": context,
#         "metadata": metadata,
#         "source_file": _THREAD_METADATA.get(str(thread_id), {}).get("filename"),
#     }


# tools = [search_tool, get_stock_price, calculator, rag_tool]
# llm_with_tools = llm.bind_tools(tools)

# # -------------------
# # 4. State
# # -------------------
# class ChatState(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]


# # -------------------
# # 5. Nodes
# # -------------------
# def chat_node(state: ChatState, config=None):
#     """LLM node that may answer or request a tool call."""
#     thread_id = None
#     if config and isinstance(config, dict):
#         thread_id = config.get("configurable", {}).get("thread_id")

#     system_message = SystemMessage(
#         content=(
#             "You are a helpful assistant. For questions about the uploaded PDF, call "
#             "the `rag_tool` and include the thread_id "
#             f"`{thread_id}`. You can also use the web search, stock price, and "
#             "calculator tools when helpful. If no document is available, ask the user "
#             "to upload a PDF."
#         )
#     )

#     messages = [system_message, *state["messages"]]
#     response = llm_with_tools.invoke(messages, config=config)
#     return {"messages": [response]}


# tool_node = ToolNode(tools)

# # -------------------
# # 6. Checkpointer
# # -------------------
# conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
# checkpointer = SqliteSaver(conn=conn)

# # -------------------
# # 7. Graph
# # -------------------
# graph = StateGraph(ChatState)
# graph.add_node("chat_node", chat_node)
# graph.add_node("tools", tool_node)

# graph.add_edge(START, "chat_node")
# graph.add_conditional_edges("chat_node", tools_condition)
# graph.add_edge("tools", "chat_node")

# chatbot = graph.compile(checkpointer=checkpointer)

# # -------------------
# # 8. Helpers
# # -------------------
# def retrieve_all_threads():
#     all_threads = set()
#     for checkpoint in checkpointer.list(None):
#         all_threads.add(checkpoint.config["configurable"]["thread_id"])
#     return list(all_threads)


# def thread_has_document(thread_id: str) -> bool:
#     return str(thread_id) in _THREAD_RETRIEVERS


# def thread_document_metadata(thread_id: str) -> dict:
#     return _THREAD_METADATA.get(str(thread_id), {})














from __future__ import annotations

import os
import re
import sqlite3
from typing import Annotated, TypedDict

import duckdb
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")

DB_PATH = "retail.duckdb"
DATASET_FOLDER = os.getenv("DATASET_FOLDER", "data")
duck_conn = duckdb.connect(DB_PATH)


def safe_table_name(filename: str) -> str:
    name = os.path.splitext(filename)[0].lower()
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def get_table_names() -> list[str]:
    try:
        tables = duck_conn.execute("SHOW TABLES").fetchall()
        return [table[0] for table in tables]
    except Exception:
        return []


def load_retail_dataset() -> None:
    """
    Loads each CSV as a separate DuckDB table.
    Example:
    data/sales.csv -> sales
    data/stores.csv -> stores
    """
    try:
        if not os.path.exists(DATASET_FOLDER):
            print(f"Dataset folder not found: {DATASET_FOLDER}")
            return

        csv_files = [
            file for file in os.listdir(DATASET_FOLDER)
            if file.lower().endswith(".csv")
        ]

        if not csv_files:
            print("No CSV files found in data folder.")
            return

        for file in csv_files:
            table_name = safe_table_name(file)
            file_path = os.path.join(DATASET_FOLDER, file).replace("\\", "/")

            duck_conn.execute(
                f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT
                    row_number() OVER () AS source_row_id,
                    *
                FROM read_csv_auto('{file_path}', union_by_name=True)
                """
            )

            print(f"Loaded {file_path} as table: {table_name}")

        print("Loaded tables:", get_table_names())

    except Exception as e:
        print("ERROR loading datasets:", e)


load_retail_dataset()


def get_table_schema() -> str:
    try:
        tables = get_table_names()

        if not tables:
            return "No tables loaded. Add CSV files inside data folder."

        schema_text = ""

        for table_name in tables:
            schema_df = duck_conn.execute(f"DESCRIBE {table_name}").fetchdf()
            schema_text += f"\n\nTable: {table_name}\n"
            schema_text += schema_df.to_string(index=False)

        return schema_text

    except Exception as e:
        return f"Could not load schema: {e}"


@tool
def list_available_tables() -> dict:
    """
    Use when user asks what data/tables are available.
    """
    return {
        "tables": get_table_names(),
        "schema": get_table_schema(),
    }


@tool
def query_retail_data(sql_query: str) -> dict:
    """
    Run SELECT SQL query on loaded retail tables.
    Use this for custom joins, aggregations, filtering, and grounded answers.
    """
    try:
        cleaned_query = sql_query.strip().lower()

        if not cleaned_query.startswith("select"):
            return {"error": "Only SELECT queries are allowed.", "sql": sql_query}

        blocked_words = [
            "drop ",
            "delete ",
            "update ",
            "insert ",
            "alter ",
            "create ",
            "truncate ",
        ]

        if any(word in cleaned_query for word in blocked_words):
            return {"error": "Unsafe SQL detected.", "sql": sql_query}

        result = duck_conn.execute(sql_query).fetchdf()

        if len(result) > 50:
            result = result.head(50)

        return {
            "sql": sql_query,
            "rows": result.to_dict(orient="records"),
            "note": "Use source_row_id or aliased row IDs as citations.",
        }

    except Exception as e:
        return {
            "error": str(e),
            "sql": sql_query,
            "hint": "Check table and column names from schema.",
        }


@tool
def resolve_business_entity(term: str) -> dict:
    """
    Resolves terms like Mumbai, Pune, Diwali, premium electronics,
    category names, store names, SKU names, etc.
    """
    try:
        matches = {}

        for table in get_table_names():
            schema_df = duck_conn.execute(f"DESCRIBE {table}").fetchdf()
            columns = schema_df["column_name"].tolist()

            for col in columns:
                try:
                    query = f"""
                    SELECT
                        source_row_id,
                        '{table}' AS table_name,
                        '{col}' AS column_name,
                        CAST({col} AS VARCHAR) AS matched_value
                    FROM {table}
                    WHERE LOWER(CAST({col} AS VARCHAR)) LIKE LOWER('%{term}%')
                    LIMIT 10
                    """

                    df = duck_conn.execute(query).fetchdf()

                    if len(df) > 0:
                        matches[f"{table}.{col}"] = df.to_dict(orient="records")

                except Exception:
                    pass

        return {
            "term": term,
            "matches": matches,
            "note": "Use this before joining when user uses business terms.",
        }

    except Exception as e:
        return {"error": str(e)}


@tool
def get_qoq_trend(
    table_name: str,
    date_column: str,
    revenue_column: str,
    group_column: str,
) -> dict:
    """
    Calculates quarter-over-quarter trend.
    Use for questions like revenue drop, QoQ growth, last quarter performance.
    """
    try:
        table_name = safe_table_name(table_name)

        query = f"""
        WITH quarterly AS (
            SELECT
                {group_column},
                DATE_TRUNC('quarter', CAST({date_column} AS DATE)) AS quarter,
                SUM({revenue_column}) AS revenue,
                MIN(source_row_id) AS first_source_row_id,
                MAX(source_row_id) AS last_source_row_id
            FROM {table_name}
            GROUP BY {group_column}, quarter
        ),
        trend AS (
            SELECT
                {group_column},
                quarter,
                revenue,
                LAG(revenue) OVER (
                    PARTITION BY {group_column}
                    ORDER BY quarter
                ) AS previous_revenue,
                ROUND(
                    ((revenue - LAG(revenue) OVER (
                        PARTITION BY {group_column}
                        ORDER BY quarter
                    )) / NULLIF(LAG(revenue) OVER (
                        PARTITION BY {group_column}
                        ORDER BY quarter
                    ), 0)) * 100,
                    2
                ) AS qoq_growth_pct,
                first_source_row_id,
                last_source_row_id
            FROM quarterly
        )
        SELECT *
        FROM trend
        ORDER BY ABS(qoq_growth_pct) DESC NULLS LAST
        LIMIT 30
        """

        df = duck_conn.execute(query).fetchdf()

        return {
            "sql": query,
            "rows": df.to_dict(orient="records"),
            "note": "Cite first_source_row_id and last_source_row_id.",
        }

    except Exception as e:
        return {"error": str(e)}


@tool
def get_store_performance(
    table_name: str,
    store_column: str,
    revenue_column: str,
) -> dict:
    """
    Ranks stores by revenue.
    Use for top stores, worst stores, store comparison.
    """
    try:
        table_name = safe_table_name(table_name)

        query = f"""
        SELECT
            {store_column},
            SUM({revenue_column}) AS total_revenue,
            COUNT(*) AS record_count,
            MIN(source_row_id) AS first_source_row_id,
            MAX(source_row_id) AS last_source_row_id
        FROM {table_name}
        GROUP BY {store_column}
        ORDER BY total_revenue DESC
        LIMIT 20
        """

        df = duck_conn.execute(query).fetchdf()

        return {
            "sql": query,
            "rows": df.to_dict(orient="records"),
            "note": "Cite source row ranges.",
        }

    except Exception as e:
        return {"error": str(e)}


@tool
def find_store_events(
    table_name: str,
    keyword: str,
) -> dict:
    """
    Finds events/promotions using keyword search.
    Use for Diwali, discount, promo, event, campaign questions.
    """
    try:
        table_name = safe_table_name(table_name)
        schema_df = duck_conn.execute(f"DESCRIBE {table_name}").fetchdf()
        columns = schema_df["column_name"].tolist()

        conditions = []
        for col in columns:
            conditions.append(
                f"LOWER(CAST({col} AS VARCHAR)) LIKE LOWER('%{keyword}%')"
            )

        where_clause = " OR ".join(conditions)

        query = f"""
        SELECT *
        FROM {table_name}
        WHERE {where_clause}
        LIMIT 30
        """

        df = duck_conn.execute(query).fetchdf()

        return {
            "sql": query,
            "rows": df.to_dict(orient="records"),
            "note": "Use source_row_id as citation.",
        }

    except Exception as e:
        return {"error": str(e)}


@tool
def get_inventory_health(
    table_name: str,
    store_column: str,
    sku_column: str,
    stock_column: str,
) -> dict:
    """
    Finds stockout or low-stock SKUs.
    Use for inventory risk and stockout questions.
    """
    try:
        table_name = safe_table_name(table_name)

        query = f"""
        SELECT
            source_row_id,
            {store_column},
            {sku_column},
            {stock_column}
        FROM {table_name}
        WHERE {stock_column} <= 0
        ORDER BY {stock_column} ASC
        LIMIT 30
        """

        df = duck_conn.execute(query).fetchdf()

        return {
            "sql": query,
            "rows": df.to_dict(orient="records"),
            "note": "Use source_row_id as citation.",
        }

    except Exception as e:
        return {"error": str(e)}


@tool
def detect_retail_anomalies(
    table_name: str,
    metric_column: str,
    group_column: str,
) -> dict:
    """
    Detects unusual spikes/drops using z-score.
    Use for anomaly investigation.
    """
    try:
        table_name = safe_table_name(table_name)

        query = f"""
        SELECT
            source_row_id,
            *,
            AVG({metric_column}) OVER(PARTITION BY {group_column}) AS avg_value,
            STDDEV({metric_column}) OVER(PARTITION BY {group_column}) AS std_value,
            ({metric_column} - AVG({metric_column}) OVER(PARTITION BY {group_column}))
            / NULLIF(STDDEV({metric_column}) OVER(PARTITION BY {group_column}), 0) AS z_score
        FROM {table_name}
        QUALIFY ABS(z_score) > 2
        ORDER BY ABS(z_score) DESC
        LIMIT 20
        """

        df = duck_conn.execute(query).fetchdf()

        return {
            "sql": query,
            "anomalies": df.to_dict(orient="records"),
            "note": "Explain anomalies and cite source_row_id.",
        }

    except Exception as e:
        return {"error": str(e)}


@tool
def forecast_next_quarter(
    table_name: str,
    date_column: str,
    metric_column: str,
    group_column: str,
) -> dict:
    """
    Simple deterministic forecast using last 4 quarter average.
    Use for next-quarter risk/performance questions.
    """
    try:
        table_name = safe_table_name(table_name)

        query = f"""
        WITH quarterly AS (
            SELECT
                {group_column},
                DATE_TRUNC('quarter', CAST({date_column} AS DATE)) AS quarter,
                SUM({metric_column}) AS metric_value,
                MIN(source_row_id) AS first_source_row_id,
                MAX(source_row_id) AS last_source_row_id
            FROM {table_name}
            GROUP BY {group_column}, quarter
        ),
        ranked AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY {group_column}
                    ORDER BY quarter DESC
                ) AS rn
            FROM quarterly
        )
        SELECT
            {group_column},
            AVG(metric_value) AS forecast_next_quarter,
            MIN(first_source_row_id) AS first_source_row_id,
            MAX(last_source_row_id) AS last_source_row_id
        FROM ranked
        WHERE rn <= 4
        GROUP BY {group_column}
        ORDER BY forecast_next_quarter DESC
        LIMIT 20
        """

        df = duck_conn.execute(query).fetchdf()

        return {
            "sql": query,
            "rows": df.to_dict(orient="records"),
            "note": "This is a simple baseline forecast using last 4 quarters.",
        }

    except Exception as e:
        return {"error": str(e)}


@tool
def run_anomaly_investigation(
    table_name: str,
    metric_column: str,
    group_column: str,
) -> dict:
    """
    Autonomous anomaly investigator:
    1. Finds anomalies
    2. Gives possible causes to inspect
    3. Stops after first deterministic anomaly scan
    """
    try:
        table_name = safe_table_name(table_name)

        query = f"""
        SELECT
            source_row_id,
            *,
            AVG({metric_column}) OVER(PARTITION BY {group_column}) AS avg_value,
            STDDEV({metric_column}) OVER(PARTITION BY {group_column}) AS std_value,
            ({metric_column} - AVG({metric_column}) OVER(PARTITION BY {group_column}))
            / NULLIF(STDDEV({metric_column}) OVER(PARTITION BY {group_column}), 0) AS z_score
        FROM {table_name}
        QUALIFY ABS(z_score) > 2
        ORDER BY ABS(z_score) DESC
        LIMIT 10
        """

        df = duck_conn.execute(query).fetchdf()

        return {
            "investigation_plan": [
                "Check metric anomaly by group.",
                "Check related event/promotion table if available.",
                "Check inventory or stockout table if available.",
                "Check returns/cancellations table if available.",
                "Stop if z_score evidence is strong or no related table exists.",
            ],
            "sql": query,
            "findings": df.to_dict(orient="records"),
            "stopping_criterion": "Stopped after deterministic anomaly scan. Continue only if related event/inventory/return tables exist.",
            "note": "Write one-page summary with cause, evidence, next action, confidence.",
        }

    except Exception as e:
        return {"error": str(e)}


@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Basic calculator.
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation {operation}"}

        return {
            "first_num": first_num,
            "second_num": second_num,
            "operation": operation,
            "result": result,
        }

    except Exception as e:
        return {"error": str(e)}


tools = [
    list_available_tables,
    query_retail_data,
    resolve_business_entity,
    get_qoq_trend,
    get_store_performance,
    find_store_events,
    get_inventory_health,
    detect_retail_anomalies,
    forecast_next_quarter,
    run_anomaly_investigation,
    calculator,
]

llm_with_tools = llm.bind_tools(tools)


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState, config=None):
    schema = get_table_schema()

    system_message = SystemMessage(
        content=(
            "You are an AI-powered Retail Intelligence Copilot for non-technical business users.\n\n"
            "You answer questions using DuckDB tools over multiple CSV tables.\n"
            "Never invent numbers. Always use tool results.\n\n"
            "Tool rules:\n"
            "- Use list_available_tables if schema/table names are unclear.\n"
            "- Use resolve_business_entity for business terms like Mumbai, Pune, Diwali, premium electronics.\n"
            "- Use query_retail_data for joins, filters, aggregations, and detailed answers.\n"
            "- Use get_qoq_trend for quarter-over-quarter trend/growth/drop questions.\n"
            "- Use get_store_performance for top/worst store questions.\n"
            "- Use find_store_events for promotions, events, campaigns, Diwali questions.\n"
            "- Use get_inventory_health for stockout/inventory risk questions.\n"
            "- Use forecast_next_quarter for next-quarter risk/forecast questions.\n"
            "- Use run_anomaly_investigation for autonomous investigation.\n\n"
            "SQL rules:\n"
            "- Only SELECT queries are allowed.\n"
            "- Use table names and columns exactly from schema.\n"
            "- Join tables using common keys like store_id, sku_id, product_id, customer_id, order_id, region_id, date.\n"
            "- Include source_row_id from every table used with alias.\n"
            "  Example: sales.source_row_id AS sales_row_id, stores.source_row_id AS stores_row_id.\n"
            "- If required keys/columns are missing, ask a clarification question.\n\n"
            "Business term rules:\n"
            "- Resolve vague entities before answering.\n"
            "- For 'last quarter', infer from MAX(date) in the relevant table.\n"
            "- For 'premium electronics', first check category/product columns.\n"
            "- For city names, check store/location/region columns.\n\n"
            "Answer rules:\n"
            "- Give simple business explanation.\n"
            "- Cite rows like: sales_row_id=10, stores_row_id=3.\n"
            "- For aggregated answers, cite source row ranges or sample source rows returned by tools.\n"
            "- If question is ambiguous, ask one clear follow-up question.\n"
            "- If question is out of scope or asks for private/PII data, refuse safely.\n\n"
            "Cost and latency rules:\n"
            "- Maximum 3 tool calls per normal user question.\n"
            "- Maximum 5 tool calls for anomaly investigation.\n"
            "- Prefer deterministic tools over re-deriving logic inside LLM.\n\n"
            "Loaded schemas:\n"
            f"{schema}"
        )
    )

    messages = [system_message, *state["messages"]]
    response = llm_with_tools.invoke(messages, config=config)
    return {"messages": [response]}


tool_node = ToolNode(tools)

conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer=checkpointer)


def retrieve_all_threads():
    all_threads = set()

    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])

    return list(all_threads)


def dataset_loaded() -> bool:
    try:
        tables = duck_conn.execute("SHOW TABLES").fetchall()
        return len(tables) > 0
    except Exception:
        return False


def retail_schema() -> str:
    return get_table_schema()