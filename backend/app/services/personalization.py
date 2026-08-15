import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.story import Story
from backend.app.models.interaction import Interaction
from backend.app.models.preference import Preference
from backend.app.config import settings

logger = logging.getLogger(__name__)

def get_weight_deltas() -> Dict[str, float]:
    """Returns dynamic weight adjustment deltas from settings."""
    return {
        # Core v1 Actions from configuration
        "like": settings.WEIGHT_DELTA_LIKE,
        "dislike": settings.WEIGHT_DELTA_DISLIKE,
        "save": settings.WEIGHT_DELTA_SAVE,
        "unsave": -settings.WEIGHT_DELTA_SAVE,
        "open": settings.WEIGHT_DELTA_OPEN,
        "source_open": settings.WEIGHT_DELTA_SOURCE_OPEN,
        "source-open": settings.WEIGHT_DELTA_SOURCE_OPEN,
        "share": settings.WEIGHT_DELTA_SHARE,
        
        # Aliases
        "swipe_right": settings.WEIGHT_DELTA_LIKE,
        "interested": settings.WEIGHT_DELTA_LIKE,
        "swipe_left": settings.WEIGHT_DELTA_DISLIKE,
        "skip": settings.WEIGHT_DELTA_DISLIKE,
        "click": settings.WEIGHT_DELTA_OPEN,
        "open_source": settings.WEIGHT_DELTA_SOURCE_OPEN,
    }

class PersonalizationService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_topic_weights(self, user_id: str = "default_user") -> Dict[str, float]:
        """Returns dictionary of {topic: weight} for a given user."""
        weights = self.db.query(Preference).filter(Preference.user_id == user_id).all()
        return {w.topic: w.weight for w in weights}

    def record_interaction(
        self,
        story_id: int,
        interaction_type: str,
        user_id: str = "default_user"
    ) -> List[str]:
        """
        Persists user interaction and updates relevant topic weights.
        Actions supported: LIKE (+0.25), DISLIKE (-0.12), SAVE (+0.40), SOURCE_OPEN (+0.15), OPEN (+0.10), SHARE (+0.30)
        Returns list of updated topic names.
        """
        action_clean = interaction_type.strip().lower()
        
        # 1. Persist interaction event
        interaction = Interaction(
            story_id=story_id,
            action=action_clean.upper(),
            session_id=user_id,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(interaction)
        
        # 2. Find story to extract associated tags
        story = self.db.query(Story).filter(Story.id == story_id).first()
        if not story:
            self.db.commit()
            return []

        deltas = get_weight_deltas()
        delta = deltas.get(action_clean, 0.0)
        is_positive = delta > 0
        is_negative = delta < 0

        # Collect all related tags (category, sub_category, topics, companies, technologies)
        tags_to_update = set()
        if story.category:
            tags_to_update.add(story.category)
        if story.sub_category:
            tags_to_update.add(story.sub_category)
        for t in (story.topics or []):
            tags_to_update.add(t)
        for c in (story.companies or []):
            tags_to_update.add(c)
        for tech in (story.technologies or []):
            tags_to_update.add(tech)

        updated_topics = []
        for tag in tags_to_update:
            if not tag or len(tag.strip()) < 2:
                continue
                
            tag_clean = tag.strip()
            topic_record = self.db.query(Preference).filter(
                Preference.user_id == user_id,
                Preference.topic == tag_clean
            ).first()

            if not topic_record:
                # Start at baseline 1.0 + delta
                initial_weight = max(0.2, min(3.5, 1.0 + delta))
                topic_record = Preference(
                    user_id=user_id,
                    topic=tag_clean,
                    weight=initial_weight,
                    positive_count=1 if is_positive else 0,
                    negative_count=1 if is_negative else 0
                )
                self.db.add(topic_record)
            else:
                # Apply delta and clamp between 0.15 and 3.5
                new_weight = max(0.15, min(3.5, topic_record.weight + delta))
                topic_record.weight = round(new_weight, 3)
                if is_positive:
                    topic_record.positive_count = (topic_record.positive_count or 0) + 1
                elif is_negative:
                    topic_record.negative_count = (topic_record.negative_count or 0) + 1
                topic_record.updated_at = datetime.now(timezone.utc)

            updated_topics.append(tag_clean)

        self.db.commit()
        return updated_topics

    def reset_preferences(self, user_id: str = "default_user") -> None:
        """Resets all learned topic weights to default baseline."""
        self.db.query(Preference).filter(Preference.user_id == user_id).delete()
        self.db.commit()
