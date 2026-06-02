from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import health
from app.routers.screener import router as screener_router
from app.routers.stock_detail import router as stock_detail_router
from app.routers.stock_fundamental_api import router as stock_fundamental_router
from app.database import check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時檢查資料庫連線
    if check_db_connection():
        print("✅ 資料庫連線正常")
    else:
        print("⚠️ 資料庫連線失敗，請確認容器已啟動")
    yield
    # 關閉時清理（如有需要）


app = FastAPI(
    title="Ambush System API",
    description="伏擊系統後端 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vue3 開發服務器和前端容器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(health.router)
app.include_router(screener_router)
app.include_router(stock_detail_router)
app.include_router(stock_fundamental_router)
