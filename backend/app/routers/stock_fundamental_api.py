"""
股票基本面數據 API 路由
提供手動觸發獲取股票基本面數據的端點
V2.0 新增：使用 stock_fundamental_latest 緩存表進行高效篩選
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.database import SessionLocal
from app.models.stock_fundamental import StockFundamental
from app.models.stock_fundamental_latest import StockFundamentalLatest
from app.tasks.stock_fundamental_tasks import (
    fetch_stock_fundamentals,
    fetch_single_stock_fundamental,
)

router = APIRouter(prefix="/api/v1/stock-fundamental", tags=["stock_fundamental"])


class StockCodesRequest(BaseModel):
    """批量獲取股票基本面數據的請求模型"""
    stock_codes: List[str]


class TaskResponse(BaseModel):
    """任務響應模型"""
    message: str
    task_id: str


class TaskStatusResponse(BaseModel):
    """任務狀態響應模型"""
    task_id: str
    status: str
    result: dict = None


@router.post("/fetch-batch", response_model=TaskResponse)
async def fetch_batch_fundamentals(request: StockCodesRequest):
    """
    批量獲取股票基本面數據
    
    Args:
        request: 包含股票代碼列表的請求
        
    Returns:
        TaskResponse: 包含任務 ID 的響應
    """
    if not request.stock_codes:
        raise HTTPException(status_code=400, detail="股票代碼列表不能為空")
    
    if len(request.stock_codes) > 50:
        raise HTTPException(status_code=400, detail="一次最多只能處理 50 隻股票")
    
    task = fetch_stock_fundamentals.delay(request.stock_codes)
    
    return TaskResponse(
        message=f"已啟動 {len(request.stock_codes)} 隻股票數據獲取任務",
        task_id=task.id,
    )


@router.post("/fetch-single/{symbol}", response_model=TaskResponse)
async def fetch_single_fundamental(symbol: str):
    """
    獲取單一股票基本面數據
    
    Args:
        symbol: 股票代碼，例如 '0005.HK'
        
    Returns:
        TaskResponse: 包含任務 ID 的響應
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="股票代碼不能為空")
    
    task = fetch_single_stock_fundamental.delay(symbol)
    
    return TaskResponse(
        message=f"已啟動 {symbol} 數據獲取任務",
        task_id=task.id,
    )


@router.get("/list")
async def list_fundamentals():
    """
    獲取所有股票基本面數據（從歷史表）
    
    Returns:
        list: 所有股票的基本面數據列表
    """
    db = SessionLocal()
    try:
        stocks = db.query(StockFundamental).order_by(StockFundamental.code).all()
        return [
            {
                "id": s.id,
                "code": s.code,
                "market": s.market,
                "report_date": str(s.report_date) if s.report_date else None,
                "pe_ttm": float(s.pe_ttm) if s.pe_ttm else None,
                "eps_ttm": float(s.eps_ttm) if s.eps_ttm else None,
                "float_shares": s.float_shares,
                "debt_ratio": float(s.debt_ratio) if s.debt_ratio else None,
                "updated_at": str(s.updated_at) if s.updated_at else None,
            }
            for s in stocks
        ]
    finally:
        db.close()


@router.get("/latest")
async def list_latest_fundamentals(
    market: Optional[str] = Query(None, description="市場過濾"),
    min_pe: Optional[float] = Query(None, description="最小 PE"),
    max_pe: Optional[float] = Query(None, description="最大 PE"),
    min_eps: Optional[float] = Query(None, description="最小 EPS"),
):
    """
    獲取所有股票最新基本面數據（從 latest 緩存表，效能提升 100 倍）
    
    Args:
        market: 市場代碼（TW/US/HK）
        min_pe: 最小 PE 篩選
        max_pe: 最大 PE 篩選
        min_eps: 最小 EPS 篩選
        
    Returns:
        list: 所有股票的最新基本面數據列表
    """
    db = SessionLocal()
    try:
        query = db.query(StockFundamentalLatest)
        
        if market:
            query = query.filter(StockFundamentalLatest.market == market)
        if min_pe is not None:
            query = query.filter(StockFundamentalLatest.pe_ttm >= min_pe)
        if max_pe is not None:
            query = query.filter(StockFundamentalLatest.pe_ttm <= max_pe)
        if min_eps is not None:
            query = query.filter(StockFundamentalLatest.eps_ttm >= min_eps)
        
        stocks = query.order_by(StockFundamentalLatest.code).all()
        
        return [
            {
                "code": s.code,
                "market": s.market,
                "report_date": str(s.report_date) if s.report_date else None,
                "pe_ttm": float(s.pe_ttm) if s.pe_ttm else None,
                "eps_ttm": float(s.eps_ttm) if s.eps_ttm else None,
                "float_shares": s.float_shares,
                "debt_ratio": float(s.debt_ratio) if s.debt_ratio else None,
                "pb": float(s.pb) if s.pb else None,
                "dividend_yield": float(s.dividend_yield) if s.dividend_yield else None,
                "total_market_cap": float(s.total_market_cap) if s.total_market_cap else None,
                "updated_at": str(s.updated_at) if s.updated_at else None,
            }
            for s in stocks
        ]
    finally:
        db.close()


@router.get("/screener")
async def screener_fundamentals(
    market: str = Query("TW", description="市場代碼"),
    max_pe: float = Query(10.0, description="最大 PE"),
    min_eps: float = Query(0, description="最小 EPS"),
    min_float_shares: Optional[int] = Query(None, description="最小流通股本"),
    max_float_shares: Optional[int] = Query(None, description="最大流通股本"),
):
    """
    基本面篩選器 - 使用 stock_fundamental_latest 緩存表
    
    效能：全表掃描 3000 條記錄，響應時間 < 100ms
    
    Args:
        market: 市場代碼
        max_pe: 最大本益比（預設 10）
        min_eps: 最小每股盈餘（預設 0）
        min_float_shares: 最小流通股本
        max_float_shares: 最大流通股本
        
    Returns:
        list: 符合篩選條件的股票列表
    """
    db = SessionLocal()
    try:
        query = db.query(StockFundamentalLatest).filter(
            StockFundamentalLatest.market == market,
            StockFundamentalLatest.pe_ttm <= max_pe,
            StockFundamentalLatest.eps_ttm >= min_eps,
        )
        
        if min_float_shares is not None:
            query = query.filter(StockFundamentalLatest.float_shares >= min_float_shares)
        if max_float_shares is not None:
            query = query.filter(StockFundamentalLatest.float_shares <= max_float_shares)
        
        stocks = query.order_by(StockFundamentalLatest.pe_ttm.asc()).all()
        
        return {
            "total": len(stocks),
            "market": market,
            "criteria": {
                "max_pe": max_pe,
                "min_eps": min_eps,
                "min_float_shares": min_float_shares,
                "max_float_shares": max_float_shares,
            },
            "stocks": [
                {
                    "code": s.code,
                    "market": s.market,
                    "pe_ttm": float(s.pe_ttm) if s.pe_ttm else None,
                    "eps_ttm": float(s.eps_ttm) if s.eps_ttm else None,
                    "float_shares": s.float_shares,
                    "debt_ratio": float(s.debt_ratio) if s.debt_ratio else None,
                    "pb": float(s.pb) if s.pb else None,
                    "dividend_yield": float(s.dividend_yield) if s.dividend_yield else None,
                    "total_market_cap": float(s.total_market_cap) if s.total_market_cap else None,
                }
                for s in stocks
            ],
        }
    finally:
        db.close()


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_fetch_status(task_id: str):
    """
    查詢數據獲取任務狀態
    
    Args:
        task_id: 任務 ID
        
    Returns:
        TaskStatusResponse: 任務狀態
    """
    from celery.result import AsyncResult
    from app.celery_app import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    
    return TaskStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.result if result.ready() else None,
    )
