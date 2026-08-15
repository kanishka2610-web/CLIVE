import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.source import Source
from backend.app.models.story import Story
from backend.app.models.preference import TopicWeight
from backend.app.services.personalization import PersonalizationService

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    
    src = Source(name="Test Lab", url="https://test.com/rss", feed_type="rss", category="Lab")
    db.add(src)
    db.commit()
    db.refresh(src)
    
    story = Story(
        source_id=src.id,
        canonical_url="https://test.com/claude-3-7",
        original_url="https://test.com/claude-3-7",
        title="Claude 3.7 Sonnet Released",
        normalized_title="Claude 3.7 Sonnet Released",
        hash_signature="abcd1234",
        category="LLMs",
        sub_category="Reasoning",
        companies=["Anthropic"],
        technologies=["Claude 3.7"],
        topics=["Reasoning", "Benchmarks"],
        published_at=datetime.now(timezone.utc),
        is_ai_related=True
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    
    yield db, story
    db.close()

def test_swipe_right_boosts_topics(test_db):
    db, story = test_db
    svc = PersonalizationService(db)
    
    updated = svc.record_interaction(story.id, "swipe_right", user_id="u1")
    assert "LLMs" in updated
    assert "Anthropic" in updated
    
    weights = svc.get_user_topic_weights("u1")
    assert weights["LLMs"] > 1.0
    assert weights["Anthropic"] > 1.0

def test_swipe_left_reduces_topics(test_db):
    db, story = test_db
    svc = PersonalizationService(db)
    
    # Set initial weight 1.0
    tw = TopicWeight(user_id="u2", topic="LLMs", weight=1.0)
    db.add(tw)
    db.commit()
    
    svc.record_interaction(story.id, "swipe_left", user_id="u2")
    weights = svc.get_user_topic_weights("u2")
    assert weights["LLMs"] < 1.0
    assert weights["LLMs"] >= 0.15

def test_save_provides_strongest_boost(test_db):
    db, story = test_db
    svc = PersonalizationService(db)
    
    svc.record_interaction(story.id, "save", user_id="u3")
    weights = svc.get_user_topic_weights("u3")
    assert weights["Anthropic"] >= 1.4
