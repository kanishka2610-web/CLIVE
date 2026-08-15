import pytest
from datetime import datetime, timezone, timedelta
from backend.app.services.ranker import calculate_recency_score, calculate_personal_relevance_score, calculate_story_rank

def test_recency_score_decay():
    now = datetime.now(timezone.utc)
    
    score_2h = calculate_recency_score(now - timedelta(hours=2), now)
    score_6h = calculate_recency_score(now - timedelta(hours=6), now)
    score_18h = calculate_recency_score(now - timedelta(hours=18), now)
    score_36h = calculate_recency_score(now - timedelta(hours=36), now)
    score_4days = calculate_recency_score(now - timedelta(days=4), now)
    score_8days = calculate_recency_score(now - timedelta(days=8), now)

    assert score_2h == 100.0    # < 3 hours -> 1.00
    assert score_6h == 90.0     # < 12 hours -> 0.90
    assert score_18h == 75.0    # < 24 hours -> 0.75
    assert score_36h == 55.0    # < 48 hours -> 0.55
    assert score_4days == 30.0  # < 7 days -> 0.30
    assert score_8days == 10.0  # >= 7 days -> 0.10

    assert score_2h > score_6h > score_18h > score_36h > score_4days > score_8days

def test_personal_relevance_score_scaling():
    user_weights = {
        "LLMs": 1.5,
        "Anthropic": 2.0,
        "Agents": 0.5
    }
    
    # Story about Anthropic & LLMs
    score_fav = calculate_personal_relevance_score(
        story_category="LLMs",
        story_topics=["Reasoning"],
        story_companies=["Anthropic"],
        story_technologies=["Claude 3.7"],
        user_topic_weights=user_weights
    )
    
    # Neutral story
    score_neutral = calculate_personal_relevance_score(
        story_category="Robotics",
        story_topics=["Actuators"],
        story_companies=["Figure"],
        story_technologies=["Actuator V2"],
        user_topic_weights=user_weights
    )
    
    assert score_fav > 65.0
    assert score_neutral == 50.0

def test_calculate_story_rank_combines_factors():
    now = datetime.now(timezone.utc)
    user_weights = {"LLMs": 1.8}
    
    rank_breaking = calculate_story_rank(
        importance_score=90.0,
        novelty_score=85.0,
        published_at=now,
        story_category="LLMs",
        story_topics=["Reasoning"],
        story_companies=["OpenAI"],
        story_technologies=["o3"],
        user_topic_weights=user_weights,
        is_breaking=True,
        reference_time=now
    )
    
    rank_old = calculate_story_rank(
        importance_score=90.0,
        novelty_score=85.0,
        published_at=now - timedelta(days=6),
        story_category="LLMs",
        story_topics=["Reasoning"],
        story_companies=["OpenAI"],
        story_technologies=["o3"],
        user_topic_weights=user_weights,
        is_breaking=False,
        reference_time=now
    )
    
    assert rank_breaking > rank_old
    assert rank_breaking > 85.0
