from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from app.agent import run_agent

app = FastAPI(
    title="Agentic NL-to-SQL Analytics Assistant",
    description="Ask business questions in plain English. Get SQL-powered answers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, example="What are the top 5 customers by revenue?")


class QueryResponse(BaseModel):
    question: str
    answer: str
    status: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    """
    Main endpoint. Accepts a natural language business question
    and returns an analytical answer backed by SQL execution.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    result = await run_agent(request.question)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["answer"])
    
    return QueryResponse(**result)


@app.get("/schema")
async def get_schema():
    """
    Utility endpoint: returns the full database schema for debugging/exploration.
    """
    from sqlalchemy import inspect
    from app.agent import engine
    inspector = inspect(engine)
    schema = {}
    for table in inspector.get_table_names():
        cols = inspector.get_columns(table)
        schema[table] = [{"name": c["name"], "type": str(c["type"])} for c in cols]
    return {"schema": schema}