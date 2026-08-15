from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class CategoryCount(BaseModel):
    category: str
    count: int

    model_config = ConfigDict(from_attributes=True)

class RadarStatsOut(BaseModel):
    total_sources: int
    active_sources: int
    total_stories: int
    breaking_stories_count: int
    saved_stories_count: int
    total_interactions: int
    last_scan_time: Optional[datetime] = None
    is_scanning: bool = False
    
    # Detailed Telemetry
    sources_scanned: int = 0
    sources_failed: int = 0
    items_discovered: int = 0
    items_duplicates: int = 0
    items_rejected_non_ai: int = 0
    items_stored: int = 0
    important_stories_count: int = 0
    last_scan_duration_sec: float = 0.0
    
    category_distribution: List[CategoryCount] = []
    top_topics: List[str] = []

    model_config = ConfigDict(from_attributes=True)
