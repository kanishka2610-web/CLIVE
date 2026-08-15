from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, synonym
from datetime import datetime, timezone
from backend.app.database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    # Core Columns specified for v1
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)  # LIKE, DISLIKE, SAVE, OPEN, SOURCE_OPEN, SHARE
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Backward-compatible column & alias
    session_id = Column(String(100), default="default_user", index=True)

    interaction_type = synonym("action")

    story = relationship("Story", back_populates="interactions")

    __table_args__ = (
        Index("idx_interaction_action_session", "session_id", "action"),
    )

    def __repr__(self):
        return f"<Interaction id={self.id} action='{self.action}' story_id={self.story_id}>"
