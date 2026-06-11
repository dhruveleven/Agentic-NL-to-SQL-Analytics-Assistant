import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/analytics")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set in environment")