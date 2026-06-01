"""
StockFundamental ORM Model - 基本面與籌碼表
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Date, DateTime, UniqueConstraint, Index
from app.models.base import Base


class StockFundamental(Base):
    __tablename__ = "stock_fundamental"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    market = Column(String(4), nullable=False, default="TW")
    report_date = Column(Date, nullable=False)
    pe_ttm = Column(Numeric(10, 4))
    eps_ttm = Column(Numeric(10, 4))
    float_shares = Column(BigInteger)
    debt_ratio = Column(Numeric(6, 4))
    insider_net_buy_3m = Column(BigInteger)
    updated_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("code", "report_date", name="uq_code_report"),
        Index("idx_fund_market", "market"),
    )

    def __repr__(self):
        return f"<StockFundamental(code={self.code}, pe={self.pe_ttm})>"