# Agentic NL-to-SQL Analytics Assistant

A fully agentic analytics assistant that translates natural language business questions into SQL queries, executes them against a PostgreSQL database, and returns plain-English analytical answers — all autonomously.

Built as a hands-on learning project to work end-to-end with a modern AI engineering stack: **FastAPI · LangChain · LLM via OpenRouter · MCP · PostgreSQL · Docker**.

---

## What It Does

You ask a question in plain English:

```
"Which product category has the highest total sales?"
```

The agent does the rest:

1. Discovers the database schema autonomously
2. Generates the appropriate SQL query
3. Validates the query before running it
4. Executes it against PostgreSQL
5. Interprets the raw results into a human-readable answer

```json
{
  "question": "Which product category has the highest total sales?",
  "answer": "Electronics is the top-performing category with total sales of ₹1,28,500, driven primarily by the Laptop Pro (₹85,000) and Monitor 4K (₹32,000).",
  "status": "success"
}
```

No SQL knowledge required from the user. The agent self-corrects if a query fails — it reads the error, fixes the query, and retries.

---

## Purpose

This project was built to gain practical, end-to-end experience with a stack that represents modern AI application engineering:

| Technology | What I learned |
|---|---|
| **FastAPI** | Building REST APIs, request validation with Pydantic, async endpoints |
| **LangChain** | Agent orchestration, tool definition with `@tool`, `AgentExecutor` loop |
| **LLM (OpenRouter)** | Model-agnostic LLM integration, tool calling, prompt design |
| **MCP** | Designing structured tool interfaces following the Model Context Protocol pattern |
| **PostgreSQL** | Schema inspection with SQLAlchemy, query execution, data types |
| **Docker** | Multi-container orchestration with Compose, container networking, volumes |

The goal was not just to call an LLM API — but to build a system where an LLM autonomously orchestrates tools, recovers from failures, and produces grounded, database-backed answers.

---

## Architecture

```
User (HTTP)
    ↓
FastAPI (main.py)         — receives question, returns answer
    ↓
LangChain AgentExecutor   — runs the tool loop
    ↓
LLM via OpenRouter        — decides what to do at each step
    ↓
MCP-style Tools (agent.py)
    ├── discover_schema   — lists tables and columns
    ├── validate_sql      — checks query with EXPLAIN
    ├── execute_sql       — runs query, returns rows
    └── interpret_results — summarizes data into plain English
    ↓
PostgreSQL (Docker)       — stores and serves the data
```

All components run inside Docker containers. The app and database are networked internally — no local installations needed beyond Docker Desktop.

---

## Project Structure

```
agentic-sql-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and API routes
│   ├── agent.py         # LangChain agent, tools, and LLM setup
│   └── config.py        # Environment variable loading
├── compose.yaml         # Multi-container Docker configuration
├── Dockerfile           # FastAPI app containerization
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template (copy to .env)
└── README.md
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- An [OpenRouter](https://openrouter.ai) API key (free tier available)

That's it. No Python, no PostgreSQL installation needed locally.

---

## Setup and Running

### 1. Clone the repository

```bash
git clone https://github.com/your-username/agentic-sql-assistant.git
cd agentic-sql-assistant
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
DATABASE_URL=postgresql://postgres:postgres@db:5432/analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=analytics
```

Get a free OpenRouter API key at [https://openrouter.ai/keys](https://openrouter.ai/keys).

### 3. Start the containers

```bash
docker compose up --build
```

Wait for:
```
api-1  | INFO:     Application startup complete.
```

### 4. Seed the database

In a new terminal, connect to the database container:

```bash
docker compose exec db psql -U postgres -d analytics
```

Paste the sample data:

```sql
CREATE TABLE sales (
  id SERIAL PRIMARY KEY,
  product VARCHAR(100),
  category VARCHAR(50),
  amount NUMERIC(10,2),
  region VARCHAR(50),
  sale_date DATE
);

INSERT INTO sales (product, category, amount, region, sale_date) VALUES
('Laptop Pro', 'Electronics', 85000, 'Mumbai', '2024-01-15'),
('Wireless Mouse', 'Electronics', 1200, 'Delhi', '2024-01-18'),
('Office Chair', 'Furniture', 12000, 'Bengaluru', '2024-01-22'),
('Standing Desk', 'Furniture', 28000, 'Mumbai', '2024-02-10'),
('Mechanical Keyboard', 'Electronics', 6500, 'Pune', '2024-02-14'),
('Monitor 4K', 'Electronics', 32000, 'Bengaluru', '2024-03-01'),
('Bookshelf', 'Furniture', 4500, 'Delhi', '2024-03-12'),
('Webcam HD', 'Electronics', 3800, 'Mumbai', '2024-03-20'),
('Desk Lamp', 'Accessories', 1100, 'Pune', '2024-03-25'),
('Laptop Stand', 'Accessories', 2200, 'Delhi', '2024-04-02');

\q
```

### 5. Query the assistant

Open the interactive API docs in your browser:

```
http://localhost:8000/docs
```

Or use curl:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which category has the highest total sales?"}'
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Submit a natural language question |
| `GET` | `/schema` | View the current database schema |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive Swagger UI |

---

## Choosing a Model

The LLM is configured in `app/agent.py`. Any OpenRouter model that supports tool calling will work. Confirmed working models:

```
openai/gpt-oss-120b:free
google/gemini-2.0-flash-exp:free
meta-llama/llama-3.3-70b-instruct:free
```

To switch models, change the `model` field in `agent.py` and run `docker compose up --build`.

---

## Subsequent Runs

Once set up, starting the project again only requires:

```bash
docker compose up
```

Your database data persists in a Docker volume between restarts. Re-seeding is only needed if you run `docker compose down -v`.

To stop:

```bash
docker compose down
```

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `DATABASE_URL` | PostgreSQL connection string (use `db` as host inside Docker) |
| `POSTGRES_USER` | Database username |
| `POSTGRES_PASSWORD` | Database password |
| `POSTGRES_DB` | Database name |
