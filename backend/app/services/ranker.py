import math
from typing import Dict, List, Optional
from datetime import datetime, timezone
from backend.app.config import settings

def calculate_recency_score(published_at: datetime, reference_time: Optional[datetime] = None) -> float:
    """
    Computes a recency score based on discrete step decay:
    < 3 hours  -> 1.00 (100.0)
    < 12 hours -> 0.90 (90.0)
    < 24 hours -> 0.75 (75.0)
    < 48 hours -> 0.55 (55.0)
    < 7 days   -> 0.30 (30.0)
    >= 7 days  -> 0.10 (10.0)
    """
    if not reference_time:
        reference_time = datetime.now(timezone.utc)
        
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
        
    age_hours = max(0.0, (reference_time - published_at).total_seconds() / 3600.0)
    
    if age_hours < 3.0:
        multiplier = 1.00
    elif age_hours < 12.0:
        multiplier = 0.90
    elif age_hours < 24.0:
        multiplier = 0.75
    elif age_hours < 48.0:
        multiplier = 0.55
    elif age_hours < 168.0:  # 7 days
        multiplier = 0.30
    else:
        multiplier = 0.10
        
    return round(multiplier * 100.0, 2)

def calculate_personal_interest_score(
    story_category: str,
    story_topics: List[str],
    story_companies: List[str],
    story_technologies: List[str],
    user_topic_weights: Dict[str, float]
) -> float:
    """
    Calculates personal interest score from 0 to 100 based on matched topic weights.
    Base weight is 1.0 (maps to 50.0 score). Higher weights increase the score up to 100.
    """
    if not user_topic_weights:
        return 50.0
        
    matched_weights = []
    
    # Category match
    if story_category in user_topic_weights:
        matched_weights.append(user_topic_weights[story_category])
        
    # Topics match
    for topic in (story_topics or []):
        if topic in user_topic_weights:
            matched_weights.append(user_topic_weights[topic])
            
    # Companies match
    for company in (story_companies or []):
        if company in user_topic_weights:
            matched_weights.append(user_topic_weights[company])
            
    # Technologies match
    for tech in (story_technologies or []):
        if tech in user_topic_weights:
            matched_weights.append(user_topic_weights[tech])
            
    if not matched_weights:
        return 50.0
        
    avg_weight = sum(matched_weights) / len(matched_weights)
    
    # Map weight (typically 0.1 to 3.0+) to 0-100 scale: weight of 1.0 -> 50.0, weight of 2.0 -> 80.0
    score = 50.0 * (avg_weight ** 0.7)
    return round(max(5.0, min(100.0, score)), 2)

# Alias for backward compatibility
calculate_personal_relevance_score = calculate_personal_interest_score

def calculate_story_rank(
    importance_score: float,
    novelty_score: float,
    published_at: datetime,
    story_category: str,
    story_topics: List[str],
    story_companies: List[str],
    story_technologies: List[str],
    user_topic_weights: Optional[Dict[str, float]] = None,
    is_breaking: bool = False,
    reference_time: Optional[datetime] = None
) -> float:
    """
    Ranking formula for v1:
    ranking_score =
      importance * 0.40
    + personal_interest * 0.30
    + recency * 0.20
    + novelty * 0.10
    """
    w_imp = settings.WEIGHT_IMPORTANCE
    w_interest = settings.WEIGHT_RELEVANCE
    w_rec = settings.WEIGHT_RECENCY
    w_nov = settings.WEIGHT_NOVELTY
    
    recency_score = calculate_recency_score(published_at, reference_time)
    personal_interest = calculate_personal_interest_score(
        story_category,
        story_topics or [],
        story_companies or [],
        story_technologies or [],
        user_topic_weights or {}
    )
    
    ranking_score = (
        (importance_score * w_imp) +
        (personal_interest * w_interest) +
        (recency_score * w_rec) +
        (novelty_score * w_nov)
    )
    
    if is_breaking:
        breaking_bonus = settings.BREAKING_BOOST * (recency_score / 100.0)
        ranking_score += breaking_bonus
        
    return round(ranking_score, 2)
