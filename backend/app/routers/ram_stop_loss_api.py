"""
拉姆止損 API 路由
提供止損部位管理、狀態查詢與手動觸發功能
"""
import logging
import re
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import SessionLocal
from app.models.ram_stop_loss import RamStopLoss
from app.models.stock_bar import StockBar
from app.engine.ram_stop_loss import RamStopLossEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ram-stop-loss", tags=["拉姆止損"])


# ==========================================
# Pydantic 模型
# ==========================================

class CreatePositionRequest(BaseModel):
    """建立止損部位請求"""
    code: str = Field(..., description="股票代碼（含市場後綴，如 2330.TW）")
    market: str = Field("TW", description="市場")
    buy_date: date = Field(..., description="買入日期")
    buy_price: float = Field(..., gt=0, description="買入價格")


class CreateTrackingRequest(BaseModel):
    """建立追蹤記錄請求"""
    code: str = Field(..., description="股票代碼（含市場後綴，如 2330.TW）")


class ActivateStopLossRequest(BaseModel):
    """啟用止損監控請求"""
    code: str = Field(..., description="股票代碼（含市場後綴，如 2330.TW）")
    buy_price: float = Field(..., gt=0, description="買入價格")


class StopLossStatusResponse(BaseModel):
    """止損狀態響應"""
    code: str
    market: str
    buy_date: Optional[date] = None
    buy_price: Optional[float] = 0
    highest_price: float
    current_price: float
    stop_loss_price: float
    drawdown_pct: float
    is_triggered: bool
    is_active: bool


# ==========================================
# 輔助函數
# ==========================================

def extract_code_and_market(full_code: str) -> tuple:
    """從完整代碼中拆分 code 和 market，如 2330.TW -> (2330, TW)"""
    parts = full_code.split(".")
    if len(parts) == 2:
        return parts[0], parts[1]
    return full_code, "TW"


def get_stock_name_from_stock_bar(db, code: str) -> str:
    """從 stock_bar 表查詢股票名稱"""
    try:
        stock = db.query(StockBar).filter(
            StockBar.code == code
        ).order_by(StockBar.trade_date.desc()).first()
        return stock.name if stock and stock.name else ""
    except Exception:
        return ""


# ==========================================
# API 路由
# ==========================================

@router.post("/create", summary="將股票加入實時追蹤")
async def create_tracking(request: CreateTrackingRequest):
    """
    將股票加入實時追蹤
    
    Request:
        {
            "code": "2330.TW"
        }
    
    Response:
        {
            "success": true,
            "message": "已加入實時追蹤",
            "data": {
                "code": "2330.TW",
                "name": "台積電",
                "status": "tracking",
                "created_at": "2026-07-02T12:00:00Z"
            }
        }
    """
    full_code = request.code.strip().upper()
    
    # 驗證 code 格式（支援 .TW 和 .HK）
    if not re.match(r'^[A-Za-z0-9]+\.(TW|HK)$', full_code):
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "無效的股票代碼格式，需包含市場後綴（如 2330.TW）"}
        )
    
    # 拆分 code 和 market
    bare_code, market = extract_code_and_market(full_code)
    
    db = SessionLocal()
    try:
        # 檢查是否已存在
        existing = db.query(RamStopLoss).filter(
            RamStopLoss.code == full_code
        ).first()
        
        if existing:
            return {
                "success": True,
                "message": "已在追蹤列表中",
                "data": {
                    "code": existing.code,
                    "name": existing.name or "",
                    "status": existing.status,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None,
                }
            }
        
        # 從 stock_bar 表查詢股票名稱
        name = get_stock_name_from_stock_bar(db, bare_code)
        
        # 創建新的追蹤記錄
        now = datetime.now()
        new_position = RamStopLoss(
            code=full_code,
            name=name,
            market=market,
            status='tracking',
            buy_date=None,
            buy_price=None,
            highest_price=0,
            current_price=0,
            lowest_price=None,
            stop_loss_price=0,
            drawdown_pct=0,
            is_active=True,
            is_triggered=False,
            created_at=now,
            updated_at=now,
        )
        
        db.add(new_position)
        db.commit()
        
        return {
            "success": True,
            "message": "已加入實時追蹤",
            "data": {
                "code": new_position.code,
                "name": new_position.name or "",
                "status": new_position.status,
                "created_at": new_position.created_at.isoformat() if new_position.created_at else None,
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f'創建追蹤記錄失敗：{str(e)}')
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "伺服器內部錯誤"}
        )
    finally:
        db.close()


@router.post("/activate", summary="設定買入價並啟用止損監控")
async def activate_stop_loss(request: ActivateStopLossRequest):
    """
    設定買入價格後啟動止損監控計算
    
    從 tracking 狀態激活為 monitoring，自動計算初始止損價
    
    Request:
        {
            "code": "2330.TW",
            "buy_price": 580.0
        }
    
    Response:
        {
            "success": true,
            "message": "已啟用止損監控",
            "data": {
                "code": "2330.TW",
                "name": "台積電",
                "buy_price": 580.0,
                "current_price": 578.5,
                "highest_price": 580.0,
                "stop_loss_price": 533.6,
                "drawdown_pct": 0.0,
                "status": "monitoring"
            }
        }
    """
    full_code = request.code.strip().upper()
    
    # 驗證 code 格式
    if not re.match(r'^[A-Za-z0-9]+\.(TW|HK)$', full_code):
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "無效的股票代碼格式，需包含市場後綴（如 2330.TW）"}
        )
    
    engine = RamStopLossEngine()
    result = engine.activate_stop_loss(code=full_code, buy_price=request.buy_price)
    
    if result["status"] == "not_found":
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": result["message"]}
        )
    
    if result["status"] == "already_monitoring":
        raise HTTPException(
            status_code=409,
            detail={"success": False, "message": result["message"]}
        )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": result["message"]}
        )
    
    return {
        "success": True,
        "message": result["message"],
        "data": result["data"],
    }


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
                buy_price=float(p.buy_price) if p.buy_price else 0,
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
            buy_price=float(position.buy_price) if position.buy_price else 0,
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