import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables early from local and parent .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv()
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))

DB_FILE_PATH = os.path.join(BASE_DIR, "chatbot.db")
raw_db_url = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILE_PATH.replace(os.sep, '/')}")

import urllib.parse

# Automatically handle special characters (e.g. unencoded '@') in database passwords
if "://" in raw_db_url and raw_db_url.count("@") > 1:
    scheme, rest = raw_db_url.split("://", 1)
    last_at_idx = rest.rfind("@")
    auth_part = rest[:last_at_idx]
    host_part = rest[last_at_idx + 1:]
    if ":" in auth_part:
        user_part, pass_part = auth_part.split(":", 1)
        encoded_pass = urllib.parse.quote(pass_part, safe="")
        raw_db_url = f"{scheme}://{user_part}:{encoded_pass}@{host_part}"

# Normalize PostgreSQL URL for SQLAlchemy + psycopg2 compatibility
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_db_url.startswith("postgresql://") and not raw_db_url.startswith("postgresql+"):
    DATABASE_URL = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    DATABASE_URL = raw_db_url

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # Supabase PostgreSQL configuration with connection pooling & pinging
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides a transactional database session.
    Automatically closes the session when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
