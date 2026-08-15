from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from datetime import datetime, timezone
from backend.app.database import Base

class Preference(Base):
    __tablename__ = "preferences"

    # Core Columns specified for v1
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(100), nullable=False, index=True)
    weight = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Backward-compatible metadata
    user_id = Column(String(100), default="default_user", index=True)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_preference_user_topic", "user_id", "topic", unique=True),
    )

    def __repr__(self):
        return f"<Preference topic='{self.topic}' weight={self.weight}>"

# Alias for backward compatibility
TopicWeight = Preference

class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), default="default_user", unique=True, index=True)
    gemini_api_key = Column(String(255), nullable=True)
    gemini_model = Column(String(100), default="gemini-3.5-flash-lite")
    min_importance_threshold = Column(Float, default=40.0)
    auto_scan_enabled = Column(Integer, default=1)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
