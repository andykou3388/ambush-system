"""
拉姆止損 API 路由
提供止損部位管理、狀態查詢與手動觸發功能
"""
import logging
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import SessionLocal
from app.models.ram_stop_loss import RamStopLoss
from app.engine.ram_stop_loss import RamStopLossEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ram-stop-loss", tags=["拉姆止損"])


# ==========================================
# Pydantic 模型
# ==========================================

class CreatePositionRequest(BaseModel):
    """建立止損部位請求"""
    code: str = Field(..., description="股票代碼")
    market: str = Field("TW", description="市場")
    buy_date: date = Field(..., description="買入日期")
    buy_price: float = Field(..., gt=0, description="買入價格")


class StopLossStatusResponse(BaseModel):
    """止損狀態響應"""
    code: str
    market: str
    buy_date: date
    buy_price: float
    highest_price: float
    current_price: float
    stop_loss_price: float
    drawdown_pct: float
    is_triggered: bool
    is_active: bool


# ==========================================
# API 路由
# ==========================================

@router.post("/positions", summary="建立止損部位")
async def create_position(request: CreatePositionRequest):
    """
    建立新的拉姆止損部位
    
    當買入股票時調用此 API，系統會自動計算初始止損價
    """
    engine = RamStopLossEngine()
    result = engine.create_position(
        code=request.code,
        market=request.market,
        buy_date=request.buy_date,
        buy_price=request.buy_price,
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "建立失敗"))
    
    return result


@router.get("/positions", summary="獲取所有止損部位")
async def get_all_positions(
    active_only: bool = Query(True, description="僅返回活躍部位"),
    market: Optional[str] = Query(None, description="市場過濾"),
):
    """
    獲取所有拉姆止損部位列表
    """
    db = SessionLocal()
    try:
        query = db.query(RamStopLoss)
        
        if active_only:
            query = query.filter(RamStopLoss.is_active == True)
        
        if market:
            query = query.filter(RamStopLoss.market == market)
        
        positions = query.order_by(RamStopLoss.created_at.desc()).all()
        
        return [
            StopLossStatusResponse(
                code=p.code,
                market=p.market,
                buy_date=p.buy_date,
                buy_price=float(p.buy_price),
                highest_price=float(p.highest_price),
                current_price=float(p.current_price),
                stop_loss_price=float(p.stop_loss_price),
                drawdown_pct=float(p.drawdown_pct),
                is_triggered=p.is_triggered,
                is_active=p.is_active,
            )
            for p in positions
        ]
    finally:
        db.close()


@router.get("/positions/{code}", summary="查詢單一股票止損狀態")
async def get_position_status(code: str):
    """
    查詢指定股票的拉姆止損狀態
    """
    db = SessionLocal()
    try:
        position = db.query(RamStopLoss).filter(
            RamStopLoss.code == code
        ).first()
        
        if not position:
            raise HTTPException(status_code=404, detail=f"股票 {code} 無止損記錄")
        
        return StopLossStatusResponse(
            code=position.code,
            market=position.market,
            buy_date=position.buy_date,
            buy_price=float(position.buy_price),
            highest_price=float(position.highest_price),
            current_price=float(position.current_price),
            stop_loss_price=float(position.stop_loss_price),
            drawdown_pct=float(position.drawdown_pct),
            is_triggered=position.is_triggered,
            is_active=position.is_active,
        )
    finally:
        db.close()


@router.post("/check/{code}", summary="手動檢查止損")
async def manual_check_stop_loss(code: str):
    """
    手動觸發指定股票的止損檢查
    """
    engine = RamStopLossEngine()
    result = engine.check_stop_loss(code)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "檢查失敗"))
    
    return result


@router.post("/check-all", summary="檢查所有活躍部位止損")
async def check_all_stop_loss():
    """
    手動觸發所有活躍部位的止損檢查
    """
    engine = RamStopLossEngine()
    
    db = SessionLocal()
    try:
        active_positions = db.query(RamStopLoss).filter(
            RamStopLoss.is_active == True
        ).all()
        
        results = []
        for position in active_positions:
            result = engine.check_stop_loss(position.code)
            results.append(result)
        
        return {
            "total": len(results),
            "triggered": sum(1 for r in results if r.get("status") == "triggered"),
            "results": results,
        }
    finally:
        db.close()


@router.delete("/positions/{code}", summary="關閉止損部位")
async def close_position(code: str):
    """
    手動關閉指定股票的止損部位（例如賣出股票時）
    """
    db = SessionLocal()
    try:
        position = db.query(RamStopLoss).filter(
            RamStopLoss.code == code,
            RamStopLoss.is_active == True
        ).first()
        
        if not position:
            raise HTTPException(status_code=404, detail=f"股票 {code} 無活躍止損部位")
        
        position.is_active = False
        position.updated_at = datetime.now()
        db.commit()
        
        return {
            "status": "closed",
            "code": code,
            "message": f"{code} 止損部位已關閉",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
