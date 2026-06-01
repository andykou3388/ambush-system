"""
資料庫連線管理
使用 SQLAlchemy ORM 管理 PostgreSQL 連線
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# 從環境變數讀取資料庫連線資訊
# 優先使用完整的 DATABASE_URL，否則從個別變數拼湊
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER", "ambush")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "ambush_dev")
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "ambush_dev")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依賴注入：獲取資料庫連線"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化資料庫表格（開發環境使用）"""
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """檢查資料庫連線是否正常"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False