from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class StoryBase(BaseModel):
    title: str
    original_title: Optional[str] = None
    url: Optional[str] = None
    original_url: Optional[str] = None
    canonical_url: str
    author: Optional[str] = None
    published_at: datetime
    discovered_at: Optional[datetime] = None
    
    is_ai_related: bool = True
    category: str = "General AI"
    sub_category: Optional[str] = None
    companies: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    
    importance_score: float = 50.0
    novelty_score: float = 50.0
    technical_score: float = 50.0
    is_breaking: bool = False
    is_duplicate: bool = False
    duplicate_of: Optional[int] = None
    image_url: Optional[str] = None
    
    headline: Optional[str] = None
    summary: Optional[str] = None
    why_it_matters: List[str] = Field(default_factory=list)
    clean_content: Optional[str] = None
    raw_content: Optional[str] = None

class StoryOut(StoryBase):
    id: int
    source_id: int
    source_name: Optional[str] = None
    source_icon: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_saved: bool = False
    interaction_state: Optional[str] = None
    rank_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class StoryFeedResponse(BaseModel):
    stories: List[StoryOut]
    total: int
    page: int
    has_more: bool
