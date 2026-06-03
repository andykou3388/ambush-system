"""
StockFundamentalLatest ORM Model - 最新基本面緩存表
用於優化批量篩選性能，永遠只有每隻股票的最新一筆記錄
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Date, DateTime
from app.models.base import Base


class StockFundamentalLatest(Base):
    __tablename__ = "stock_fundamental_latest"

    code = Column(String(20), primary_key=True)
    market = Column(String(4), nullable=False, default="TW")
    report_date = Column(Date, nullable=False)
    pe_ttm = Column(Numeric(10, 4))
    eps_ttm = Column(Numeric(10, 4))
    float_shares = Column(BigInteger)
    debt_ratio = Column(Numeric(6, 4))
    insider_net_buy_3m = Column(BigInteger)
    pb = Column(Numeric(10, 4))
    dividend_yield = Column(Numeric(8, 4))
    total_market_cap = Column(Numeric(18, 2))
    net_profit_ttm = Column(Numeric(18, 2))
    updated_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<StockFundamentalLatest(code={self.code}, pe={self.pe_ttm})>"
