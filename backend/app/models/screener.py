from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class ZoneType(str, Enum):
    UPTREND = "UPTREND"       # 上升交易區
    POTENTIAL = "POTENTIAL"   # 潛力驗證區
    DOWNTREND = "DOWNTREND"   # 下跌避雷區


class ScreenerRequest(BaseModel):
    """篩選請求參數"""
    zone: Optional[ZoneType] = None     # 區域過濾
    min_price: Optional[float] = None   # 最低價格
    max_price: Optional[float] = None   # 最高價格
    market: Optional[str] = None        # 市場 (TW/US)
    days: int = 14                      # 查詢最近 N 天的資料
    page: int = 1                       # 頁碼
    page_size: int = 20                 # 每頁筆數


class StockItem(BaseModel):
    """股票項目"""
    symbol: str
    name: str
    market: str
    price: float
    changePct: float
    zone: str
    score: float
    ma10: float
    ma30: float
    tradeDate: str = ""


class ScreenerResponse(BaseModel):
    """篩選響應"""
    total: int
    page: int
    page_size: int
    days: int = 14
    items: List[StockItem]
