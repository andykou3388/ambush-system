"""
RamStopLoss ORM Model - 拉姆動態止損狀態表
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Date, DateTime, Boolean, Index
from app.models.base import Base


class RamStopLoss(Base):
    __tablename__ = "ram_stop_loss"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True)
    market = Column(String(4), nullable=False, default="TW")
    buy_date = Column(Date, nullable=False)
    buy_price = Column(Numeric(12, 4), nullable=False)
    highest_price = Column(Numeric(12, 4), nullable=False)
    current_price = Column(Numeric(12, 4), nullable=False)
    stop_loss_price = Column(Numeric(12, 4), nullable=False)
    drawdown_pct = Column(Numeric(6, 4), default=0)
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_ram_active", "is_active"),
    )

    def __repr__(self):
        return f"<RamStopLoss(code={self.code}, active={self.is_active}, drawdown={self.drawdown_pct})>"
