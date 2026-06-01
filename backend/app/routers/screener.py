"""
篩選器 API Router
提供股票篩選和批量查詢功能
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.stock_bar import StockBar
from app.models.stock_signal_log import StockSignalLog

router = APIRouter(prefix="/api/v1/screener", tags=["screener"])


@router.get("/stocks")
async def screen_stocks(
    zone: Optional[str] = Query(None, description="區域過濾 (UPTREND/POTENTIAL/DOWNTREND)"),
    min_price: Optional[float] = Query(None, description="最低價格"),
    max_price: Optional[float] = Query(None, description="最高價格"),
    market: Optional[str] = Query(None, description="市場 (TW/US)"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    db: Session = Depends(get_db),
):
    """
    篩選股票

    根據指定的過濾條件篩選股票，支援分頁查詢。
    資料來源：stock_bar + stock_signal_log JOIN
    """
    # 獲取最新交易日
    latest_date = db.query(func.max(StockSignalLog.trade_date)).scalar()
    if not latest_date:
        return {"total": 0, "page": page, "page_size": page_size, "items": []}

    # 建立查詢
    query = (
        db.query(
            StockBar.code,
            StockBar.name,
            StockBar.market,
            StockBar.close,
            StockBar.change_pct,
            StockBar.ma10_w,
            StockBar.ma30_w,
            StockBar.volume_ma5_w,
            StockSignalLog.zone,
            StockSignalLog.confidence,
            StockSignalLog.trigger_rules,
        )
        .join(
            StockSignalLog,
            (StockBar.code == StockSignalLog.code)
            & (StockBar.trade_date == StockSignalLog.trade_date),
        )
        .filter(StockSignalLog.trade_date == latest_date)
    )

    # 過濾條件
    if zone:
        query = query.filter(StockSignalLog.zone == zone.upper())
    if min_price is not None:
        query = query.filter(StockBar.close >= min_price)
    if max_price is not None:
        query = query.filter(StockBar.close <= max_price)
    if market:
        query = query.filter(StockBar.market == market.upper())

    # 排序（按信心度降序）
    query = query.order_by(StockSignalLog.confidence.desc())

    # 計算總數
    total = query.count()

    # 分頁
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "symbol": r.code,
                "name": r.name or "",
                "market": r.market,
                "price": float(r.close) if r.close else 0,
                "changePct": float(r.change_pct) if r.change_pct else 0,
                "zone": r.zone,
                "ma10": float(r.ma10_w) if r.ma10_w else 0,
                "ma30": float(r.ma30_w) if r.ma30_w else 0,
                "score": float(r.confidence) if r.confidence else 0,
            }
            for r in items
        ],
    }


@router.get("/stocks/batch")
async def batch_get_stocks(
    symbols: Optional[str] = Query(None, description="股票代碼列表，逗號分隔"),
    zone: Optional[str] = Query(None, description="區域過濾"),
    market: Optional[str] = Query(None, description="市場 (TW/US)"),
    db: Session = Depends(get_db),
):
    """
    批量獲取股票數據

    支援根據股票代碼列表或區域過濾條件獲取多個股票數據。
    """
    # 獲取最新交易日
    latest_date = db.query(func.max(StockSignalLog.trade_date)).scalar()
    if not latest_date:
        return []

    # 建立查詢
    query = (
        db.query(
            StockBar.code,
            StockBar.name,
            StockBar.market,
            StockBar.close,
            StockBar.change_pct,
            StockBar.ma10_w,
            StockBar.ma30_w,
            StockBar.volume_ma5_w,
            StockSignalLog.zone,
            StockSignalLog.confidence,
            StockSignalLog.trigger_rules,
        )
        .join(
            StockSignalLog,
            (StockBar.code == StockSignalLog.code)
            & (StockBar.trade_date == StockSignalLog.trade_date),
        )
        .filter(StockSignalLog.trade_date == latest_date)
    )

    # 過濾條件
    if symbols:
        symbol_list = symbols.split(",")
        query = query.filter(StockBar.code.in_(symbol_list))
    if zone:
        query = query.filter(StockSignalLog.zone == zone.upper())
    if market:
        query = query.filter(StockBar.market == market.upper())

    # 排序
    query = query.order_by(StockSignalLog.confidence.desc())

    items = query.all()

    return [
        {
            "symbol": r.code,
            "name": r.name or "",
            "market": r.market,
            "price": float(r.close) if r.close else 0,
            "changePct": float(r.change_pct) if r.change_pct else 0,
            "zone": r.zone,
            "ma10": float(r.ma10_w) if r.ma10_w else 0,
            "ma30": float(r.ma30_w) if r.ma30_w else 0,
            "score": float(r.confidence) if r.confidence else 0,
        }
        for r in items
    ]