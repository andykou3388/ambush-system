from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class ZoneType(str, Enum):
    BUY = "buy"       # 買入區
    HOLD = "hold"     # 持有區
    SELL = "sell"     # 賣出區

class ScreenerRequest(BaseModel):
    """篩選請求參數"""
    zone: Optional[ZoneType] = None     # 區域過濾
    min_price: Optional[float] = None   # 最低價格
    max_price: Optional[float] = None   # 最高價格
    min_volume: Optional[float] = None  # 最低成交量
    page: int = 1                       # 頁碼
    page_size: int = 20                 # 每頁筆數
    sort_by: str = "score"              # 排序欄位
    sort_order: str = "desc"            # 排序方向

class StockItem(BaseModel):
    """股票項目"""
    symbol: str
    name: str
    price: float
    change_pct: float
    zone: ZoneType
    score: float
    ma10: float
    ma30: float

class ScreenerResponse(BaseModel):
    """篩選響應"""
    total: int
    page: int
    page_size: int
    items: List[StockItem]