"""
TeacherHub Database Configuration
SQLAlchemy Engine 및 Session 설정
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Database Connection Settings
DB_USER = os.getenv("DB_USER", "teacherhub")
DB_PASS = os.environ.get("DB_PASSWORD") or os.environ.get("DB_PASS")
if not DB_PASS:
    raise RuntimeError("DB_PASSWORD 환경변수가 설정되지 않았습니다.")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "teacherhub")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engine & Session (커넥션 풀 설정)
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionLocal)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Create and return a new database session"""
    return SessionLocal()


def init_db():
    """Initialize database tables (create if not exists)"""
    from . import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
