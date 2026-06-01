"""
AuditLog ORM Model - 審計日誌表（哈希鏈防篡改）
"""
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(String(64), nullable=False)
    action_type = Column(String(20), nullable=False)
    stock_ticker = Column(String(20))
    executed_at = Column(DateTime(timezone=True), nullable=False)
    device_info = Column(JSONB)
    rule_snapshot = Column(JSONB)
    deviation_reason = Column(Text)
    compliance_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64))
    created_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_audit_user_time", "user_id", "executed_at"),
        Index("idx_audit_action_type", "action_type"),
    )

    def __repr__(self):
        return f"<AuditLog(user={self.user_id}, action={self.action_type})>"