"""
SQLAlchemy Base 宣告
使用 declarative_base() 以相容 SQLAlchemy 1.4.x（Python 3.9）
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()