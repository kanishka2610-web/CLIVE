from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship, synonym
from datetime import datetime, timezone
from backend.app.database import Base

class Source(Base):
    __tablename__ = "sources"

    # Core columns specified for v1
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    website_url = Column(String(500), nullable=True)
    feed_url = Column(String(500), nullable=False, unique=True)
    source_type = Column(String(20), default="rss")  # rss, atom, html
    category = Column(String(50), default="Industry")
    enabled = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=1)
    last_checked_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Backward-compatible columns & aliases
    icon_url = Column(String(500), nullable=True)
    last_error = Column(Text, nullable=True)

    url = synonym("feed_url")
    feed_type = synonym("source_type")
    is_active = synonym("enabled")
    last_scanned_at = synonym("last_checked_at")

    stories = relationship("Story", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Source id={self.id} name='{self.name}'>"
