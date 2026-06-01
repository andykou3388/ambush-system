"""
StockBar ORM Model - 週線行情與技術指標表
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Date, DateTime, UniqueConstraint, Index
from app.models.base import Base


class StockBar(Base):
    __tablename__ = "stock_bar"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(100))
    market = Column(String(4), nullable=False, default="TW")
    trade_date = Column(Date, nullable=False)
    freq = Column(String(2), nullable=False, default="W")
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    change_pct = Column(Numeric(6, 2))
    ma10_w = Column(Numeric(12, 4))
    ma30_w = Column(Numeric(12, 4))
    volume_ma5_w = Column(Numeric(12, 4))
    created_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("code", "trade_date", name="uq_bar_code_date"),
        Index("idx_bar_code_date", "code", "trade_date"),
    )

    def __repr__(self):
        return f"<StockBar(code={self.code}, date={self.trade_date}, close={self.close})>"