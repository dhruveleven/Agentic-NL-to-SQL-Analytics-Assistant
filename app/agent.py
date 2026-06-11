import json
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from sqlalchemy import create_engine, text, inspect
from app.config import OPENROUTER_API_KEY, DATABASE_URL

engine = create_engine(DATABASE_URL)

llm = ChatOpenAI(
    model="openai/gpt-oss-120b:free",
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "NL-SQL Assistant"
    }
)

# ── MCP-style Tool 1: Schema Discovery ──────────────────────────────────────
@tool
def discover_schema(table_name: str = "") -> str:
    """
    Discovers the database schema.
    If table_name is empty, returns all table names.
    If table_name is provided, returns column names and types for that table.
    """
    inspector = inspect(engine)
    if not table_name:
        tables = inspector.get_table_names()
        return json.dumps({"tables": tables})
    cols = inspector.get_columns(table_name)
    schema = [{"name": c["name"], "type": str(c["type"])} for c in cols]
    return json.dumps({"table": table_name, "columns": schema})


# ── MCP-style Tool 2: SQL Validation ────────────────────────────────────────
@tool
def validate_sql(query: str) -> str:
    """
    Validates a SQL query using EXPLAIN. Returns 'valid' or an error message.
    Only SELECT queries are allowed.
    """
    q = query.strip().upper()
    if not q.startswith("SELECT"):
        return "invalid: only SELECT queries are allowed"
    try:
        with engine.connect() as conn:
            conn.execute(text(f"EXPLAIN {query}"))
        return "valid"
    except Exception as e:
        return f"invalid: {str(e)}"


# ── MCP-style Tool 3: SQL Execution ─────────────────────────────────────────
@tool
def execute_sql(query: str) -> str:
    """
    Executes a validated SELECT SQL query and returns results as JSON.
    Limit output to 100 rows for safety.
    """
    if not query.strip().upper().startswith("SELECT"):
        return json.dumps({"error": "only SELECT queries are permitted"})
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result.fetchmany(100)]
            return json.dumps({"rows": rows, "count": len(rows)})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── MCP-style Tool 4: Result Interpretation ──────────────────────────────────
@tool
def interpret_results(results_json: str, original_question: str) -> str:
    """
    Takes raw SQL results (JSON string) and the original user question,
    then produces a plain-English analytical summary.
    """
    try:
        data = json.loads(results_json)
    except Exception:
        return "Could not parse results for interpretation."

    rows = data.get("rows", [])
    if not rows:
        return "The query returned no results."

    summary_prompt = (
        f"The user asked: '{original_question}'\n"
        f"The database returned {len(rows)} rows. Here is a sample (up to 5):\n"
        f"{json.dumps(rows[:5], indent=2)}\n\n"
        "Provide a concise analytical summary answering the user's question. "
        "Highlight key numbers, trends, or insights. Be direct."
    )
    response = llm.invoke(summary_prompt)
    return response.content


# ── Agent Assembly ───────────────────────────────────────────────────────────
tools = [discover_schema, validate_sql, execute_sql, interpret_results]

system_prompt = """You are an expert SQL analytics assistant. 
When a user asks a business question, follow this workflow:
1. Call discover_schema with no arguments to list all tables.
2. Call discover_schema with a specific table_name to understand its columns.
3. Generate the correct SQL SELECT query based on the schema.
4. Call validate_sql to check the query before running it.
5. If valid, call execute_sql to get the data.
6. Call interpret_results with the raw JSON results and the original question.
7. Return the interpretation as your final answer.

Never mutate data. Only SELECT queries."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)


async def run_agent(question: str) -> dict:
    try:
        result = await agent_executor.ainvoke({"input": question})
        return {
            "question": question,
            "answer": result.get("output", "No answer generated."),
            "status": "success"
        }
    except Exception as e:
        return {
            "question": question,
            "answer": str(e),
            "status": "error"
        }