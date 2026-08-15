from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class InteractionCreate(BaseModel):
    story_id: int
    interaction_type: Optional[str] = None  # LIKE, DISLIKE, SAVE, OPEN, SOURCE_OPEN, SHARE
    action: Optional[str] = None
    session_id: Optional[str] = "default_user"

class InteractionOut(BaseModel):
    id: int
    story_id: int
    action: Optional[str] = None
    interaction_type: Optional[str] = None
    session_id: Optional[str] = "default_user"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RadarInteractResponse(BaseModel):
    success: bool
    interaction_type: str
    story_id: int
    topics_updated: List[str] = []
    message: str
