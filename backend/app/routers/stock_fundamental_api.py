"""
股票基本面數據 API 路由
提供手動觸發獲取股票基本面數據的端點
"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
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
