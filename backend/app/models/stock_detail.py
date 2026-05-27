from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class RuleResult(BaseModel):
    """規則檢核結果"""
    layer: int
    rule_name: str
    passed: bool
    description: str
    details: Optional[str] = None

class TechnicalIndicators(BaseModel):
    """技術指標"""
    ma10: Optional[float] = None
    ma30: Optional[float] = None
    ma10_ma30_ratio: Optional[float] = None

class ZoneInfo(BaseModel):
    """三區分類資訊"""
    zone: str
    confidence: float
    explanation: str

class StockDetailResponse(BaseModel):
    """個股詳情響應"""
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: int
    market_cap: float
    pe_ratio: Optional[float] = None
    technical_indicators: TechnicalIndicators
    zone_info: ZoneInfo
    rules: List[RuleResult]
    updated_at: str