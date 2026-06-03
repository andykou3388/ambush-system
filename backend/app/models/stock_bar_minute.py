"""
StockBarMinute ORM Model - 分鐘線行情表（拉姆止損專用）
"""
from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, Boolean, UniqueConstraint, Index
from app.models.base import Base


class StockBarMinute(Base):
    __tablename__ = "stock_bar_minute"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    trade_time = Column(DateTime(timezone=True), nullable=False)
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    is_valid = Column(Boolean, default=True)
    corrected_open = Column(Numeric(12, 4))
    corrected_close = Column(Numeric(12, 4))
    created_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("code", "trade_time", name="uq_code_minute"),
        Index("idx_minute_code_time", "code", "trade_time"),
    )

    def __repr__(self):
        return f"<StockBarMinute(code={self.code}, time={self.trade_time}, close={self.close})>"
