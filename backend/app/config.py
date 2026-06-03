# 配置文件
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API 配置
    api_title: str = "Ambush System API"
    api_description: str = "伏擊系統後端 API - V2.0 含拉姆止損"
    api_version: str = "2.0.0"
    
    # CORS 配置
    cors_origins: list = ["http://localhost:5173"]
    
    # 伺服器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 資料庫配置
    database_url: str = "postgresql://dev_user:dev_pass_123@db:5432/ambush_dev"
    
    # Redis/Celery 配置
    redis_url: str = "redis://redis:6379"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    
    class Config:
        env_prefix = ""
        extra = "allow"

settings = Settings()
