from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SourceBase(BaseModel):
    name: str
    url: str
    feed_type: str = "rss"  # rss, atom, html
    category: str = "Industry"
    is_active: bool = True
    icon_url: Optional[str] = None
    website_url: Optional[str] = None
    priority: int = 1

class SourceCreate(SourceBase):
    pass

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    feed_type: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    icon_url: Optional[str] = None
    website_url: Optional[str] = None
    priority: Optional[int] = None

class SourceOut(SourceBase):
    id: int
    feed_url: Optional[str] = None
    source_type: Optional[str] = None
    enabled: Optional[bool] = True
    last_checked_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    failure_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime
    story_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
