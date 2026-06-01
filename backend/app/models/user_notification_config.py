"""
UserNotificationConfig ORM Model - 用戶通知偏好配置
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import ARRAY
from app.models.base import Base


class UserNotificationConfig(Base):
    __tablename__ = "user_notification_config"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False)
    channel = Column(String(10), nullable=False)
    zone_filter = Column(ARRAY(String(12)), default=["UPTREND", "DOWNTREND"])
    min_confidence = Column(Numeric(3, 2), default=0.5)
    quiet_hours_start = Column(String(5), default="22:00")
    quiet_hours_end = Column(String(5), default="08:00")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("user_id", "channel", name="uq_user_channel"),
        Index("idx_notif_user", "user_id"),
    )

    def __repr__(self):
        return f"<UserNotificationConfig(user={self.user_id}, channel={self.channel})>"