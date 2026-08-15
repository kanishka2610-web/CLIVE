from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class PreferenceOut(BaseModel):
    id: Optional[int] = None
    topic: str
    weight: float
    positive_count: Optional[int] = 0
    negative_count: Optional[int] = 0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Alias for backward compatibility
TopicWeightOut = PreferenceOut

class UserSettingOut(BaseModel):
    user_id: str
    gemini_model: str
    has_custom_api_key: bool
    min_importance_threshold: float
    auto_scan_enabled: bool

class UserSettingUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    min_importance_threshold: Optional[float] = None
    auto_scan_enabled: Optional[bool] = None

class TopicWeightUpdate(BaseModel):
    topic: str
    weight: float
