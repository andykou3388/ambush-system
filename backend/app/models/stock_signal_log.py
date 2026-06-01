"""
StockSignalLog ORM Model - 信號狀態機與規則快照表
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Date, DateTime, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base


class StockSignalLog(Base):
    __tablename__ = "stock_signal_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    market = Column(String(4), nullable=False, default="TW")
    trade_date = Column(Date, nullable=False)
    zone = Column(String(12), nullable=False)
    confidence = Column(Numeric(3, 2))
    trigger_rules = Column(JSONB, default={})
    reason = Column(Text)
    engine_version = Column(String(10), default="V2.2")
    created_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("code", "trade_date", name="uq_sig_code_date"),
        Index("idx_sig_zone_conf", "zone", "confidence"),
    )

    def __repr__(self):
        return f"<StockSignalLog(code={self.code}, zone={self.zone}, conf={self.confidence})>"