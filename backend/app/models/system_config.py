"""
SystemConfig ORM Model - 系統配置表
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_key = Column(String(64), nullable=False, unique=True)
    config_value = Column(JSONB, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<SystemConfig(key={self.config_key})>"