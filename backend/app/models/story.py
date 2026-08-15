from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, synonym
from datetime import datetime, timezone
from backend.app.database import Base

class Story(Base):
    __tablename__ = "stories"

    # Core Columns specified for v1
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(500), nullable=False)
    original_title = Column(String(500), nullable=True)
    url = Column(String(1000), nullable=False)
    canonical_url = Column(String(1000), nullable=False, unique=True, index=True)
    
    author = Column(String(100), nullable=True)
    raw_content = Column(Text, nullable=True)
    clean_content = Column(Text, nullable=True)
    
    summary = Column(Text, nullable=True)
    why_it_matters = Column(JSON, default=list)
    
    published_at = Column(DateTime, nullable=False, index=True, default=lambda: datetime.now(timezone.utc))
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    is_ai_related = Column(Boolean, default=True, index=True)
    category = Column(String(50), default="General AI", index=True)
    sub_category = Column(String(100), nullable=True)
    companies = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    topics = Column(JSON, default=list)
    
    importance_score = Column(Float, default=50.0, index=True)
    novelty_score = Column(Float, default=50.0)
    technical_score = Column(Float, default=50.0)
    is_breaking = Column(Boolean, default=False, index=True)
    
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of = Column(Integer, ForeignKey("stories.id", ondelete="SET NULL"), nullable=True)
    image_url = Column(String(1000), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Backward-compatible columns & aliases
    normalized_title = Column(String(500), nullable=True, index=True)
    hash_signature = Column(String(64), nullable=True, index=True)
    headline = Column(String(255), nullable=True)
    status = Column(String(20), default="processed")

    original_url = synonym("url")
    extracted_content = synonym("clean_content")

    # Relationships
    source = relationship("Source", back_populates="stories")
    interactions = relationship("Interaction", back_populates="story", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_story_published_importance", "published_at", "importance_score"),
        Index("idx_story_category", "category"),
    )

    def __repr__(self):
        return f"<Story id={self.id} title='{self.title[:30]}...' importance={self.importance_score}>"
