# 配置文件
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API 配置
    api_title: str = "Ambush System API"
    api_description: str = "伏擊系統後端 API"
    api_version: str = "1.0.0"
    
    # CORS 配置
    cors_origins: list = ["http://localhost:5173"]
    
    # 伺服器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"

settings = Settings()