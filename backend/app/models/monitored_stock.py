"""
MonitoredStock ORM Model - 基本面監控股票清單
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.models.base import Base


class MonitoredStock(Base):
    __tablename__ = "monitored_stocks"

    code = Column(String(20), primary_key=True)
    market = Column(String(4), nullable=False, default="TW")
    added_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<MonitoredStock(code={self.code}, market={self.market})>"