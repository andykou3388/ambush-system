"""
MediaHeat ORM Model - 媒體熱度表
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Integer, Date, DateTime, UniqueConstraint, Index
from app.models.base import Base


class MediaHeat(Base):
    __tablename__ = "media_heat"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    record_date = Column(Date, nullable=False)
    heat_score = Column(Numeric(5, 2), default=0)
    news_count = Column(Integer, default=0)
    forum_mention_count = Column(Integer, default=0)
    social_media_mentions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("code", "record_date", name="uq_code_heat_date"),
        Index("idx_heat_code_date", "code", "record_date"),
    )

    def __repr__(self):
        return f"<MediaHeat(code={self.code}, score={self.heat_score})>"