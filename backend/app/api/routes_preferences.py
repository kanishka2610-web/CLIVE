from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models.preference import TopicWeight, UserSetting
from backend.app.schemas.preference import TopicWeightOut, UserSettingOut, UserSettingUpdate, TopicWeightUpdate
from backend.app.services.personalization import PersonalizationService
from backend.app.config import settings

router = APIRouter(prefix="/api/preferences", tags=["Preferences"])

@router.get("", response_model=List[TopicWeightOut])
def get_topic_preferences(
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """List all personalized topic weights for the user."""
    weights = db.query(TopicWeight).filter(
        TopicWeight.user_id == user_id
    ).order_by(desc(TopicWeight.weight)).all()
    return weights

@router.put("/topic", response_model=TopicWeightOut)
def update_single_topic_weight(
    payload: TopicWeightUpdate,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Manually fine-tune weight for a specific topic."""
    record = db.query(TopicWeight).filter(
        TopicWeight.user_id == user_id,
        TopicWeight.topic == payload.topic
    ).first()
    
    if not record:
        record = TopicWeight(
            user_id=user_id,
            topic=payload.topic,
            weight=max(0.1, min(4.0, payload.weight))
        )
        db.add(record)
    else:
        record.weight = max(0.1, min(4.0, payload.weight))
        
    db.commit()
    db.refresh(record)
    return record

@router.post("/reset")
def reset_user_preferences(
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Reset all learned topic weights to initial baseline."""
    personalizer = PersonalizationService(db)
    personalizer.reset_preferences(user_id)
    
    # Re-seed defaults
    from backend.app.seeds.sources import seed_database_if_empty
    seed_database_if_empty(db)
    
    return {"success": True, "message": "Personalization preferences reset to defaults."}

@router.get("/settings", response_model=UserSettingOut)
def get_user_settings(
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Get user AI and runtime settings."""
    user_setting = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    
    return UserSettingOut(
        user_id=user_id,
        gemini_model=user_setting.gemini_model if user_setting else settings.GEMINI_MODEL,
        has_custom_api_key=bool(user_setting and user_setting.gemini_api_key) or bool(settings.GEMINI_API_KEY),
        min_importance_threshold=user_setting.min_importance_threshold if user_setting else 40.0,
        auto_scan_enabled=bool(user_setting.auto_scan_enabled) if user_setting else True
    )

@router.put("/settings", response_model=UserSettingOut)
def update_user_settings(
    payload: UserSettingUpdate,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Update user API key, model ID, or threshold settings."""
    user_setting = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    if not user_setting:
        user_setting = UserSetting(user_id=user_id)
        db.add(user_setting)
        
    if payload.gemini_api_key is not None:
        user_setting.gemini_api_key = payload.gemini_api_key.strip()
    if payload.gemini_model is not None:
        user_setting.gemini_model = payload.gemini_model.strip()
    if payload.min_importance_threshold is not None:
        user_setting.min_importance_threshold = payload.min_importance_threshold
    if payload.auto_scan_enabled is not None:
        user_setting.auto_scan_enabled = 1 if payload.auto_scan_enabled else 0
        
    db.commit()
    db.refresh(user_setting)
    
    return UserSettingOut(
        user_id=user_id,
        gemini_model=user_setting.gemini_model or settings.GEMINI_MODEL,
        has_custom_api_key=bool(user_setting.gemini_api_key) or bool(settings.GEMINI_API_KEY),
        min_importance_threshold=user_setting.min_importance_threshold or 40.0,
        auto_scan_enabled=bool(user_setting.auto_scan_enabled)
    )
