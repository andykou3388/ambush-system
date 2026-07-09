"""
監控股票清單 API
提供新增、查詢、刪除監控股票的功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.database import SessionLocal
from app.models.monitored_stock import MonitoredStock
from app.tasks.stock_fundamental_tasks import _fetch_stock_fundamentals_impl
from sqlalchemy.dialects.postgresql import insert

router = APIRouter(prefix="/api/v1/monitored-stocks", tags=["monitored-stocks"])


class AddStockRequest(BaseModel):
    code: str
    market: str = Field(default="TW", pattern=r"^(TW|US|HK)$")
    fetch: bool = True


class RemoveStockRequest(BaseModel):
    code: str


@router.get("/")
def list_monitored_stocks():
    """列出所有監控中的股票"""
    db = SessionLocal()
    try:
        rows = db.query(MonitoredStock).filter(
            MonitoredStock.is_active == True
        ).order_by(MonitoredStock.added_at).all()
        return [
            {
                "code": r.code,
                "market": r.market,
                "added_at": r.added_at.isoformat() if r.added_at else None,
            }
            for r in rows
        ]
    finally:
        db.close()


@router.post("/")
def add_monitored_stock(req: AddStockRequest):
    """
    將股票加入監控清單。
    若 fetch=True（預設），會先從 YFinance 抓取基本面資料，成功後才寫入資料庫。
    """
    fetch_result = None
    if req.fetch:
        try:
            fetch_result = _fetch_stock_fundamentals_impl([req.code])
            if fetch_result.get("failed", 0) > 0:
                raise HTTPException(
                    status_code=422,
                    detail=f"無法從 YFinance 取得 {req.code} 的資料，請確認股票代碼是否正確"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"抓取基本面資料失敗：{str(e)}"
            )

    db = SessionLocal()
    try:
        stmt = insert(MonitoredStock).values(
            code=req.code,
            market=req.market,
        )
        stmt = stmt.on_conflict_do_nothing()
        db.execute(stmt)
        db.commit()
        return {
            "status": "ok",
            "code": req.code,
            "market": req.market,
            "fetch_result": fetch_result,
        }
    finally:
        db.close()


@router.post("/remove")
def remove_monitored_stock(req: RemoveStockRequest):
    """從監控清單移除股票（軟刪除：設為 inactive）"""
    db = SessionLocal()
    try:
        row = db.query(MonitoredStock).filter(MonitoredStock.code == req.code).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"股票 {req.code} 不在監控清單中")
        row.is_active = False
        db.commit()
        return {"status": "ok", "code": req.code, "action": "removed"}
    finally:
        db.close()