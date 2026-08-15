import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.database import Base
from backend.app.models.source import Source
from backend.app.models.story import Story
from backend.app.services.normalizer import canonicalize_url, normalize_title, generate_content_hash
from backend.app.services.deduplicator import Deduplicator, is_primary_source

@pytest.fixture
def test_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    
    src = Source(name="OpenAI News", url="https://openai.com/news/rss.xml", feed_type="rss", category="Lab")
    db.add(src)
    db.commit()
    db.refresh(src)
    
    yield db
    db.close()

def test_is_primary_source():
    assert is_primary_source("https://openai.com/index/deep-research") is True
    assert is_primary_source("https://deepmind.google/discover/blog") is True
    assert is_primary_source("https://random-tech-aggregator.xyz/ai-news") is False

def test_deduplicator_exact_url(test_db):
    src = test_db.query(Source).first()
    canonical = "https://openai.com/index/deep-research"
    norm_title = "Introducing Deep Research"
    hash_sig = generate_content_hash(canonical, norm_title, "content")
    
    story = Story(
        source_id=src.id,
        canonical_url=canonical,
        original_url="https://openai.com/index/deep-research?utm_source=x",
        title="Introducing Deep Research",
        normalized_title=norm_title,
        hash_signature=hash_sig,
        published_at=datetime.now(timezone.utc),
        is_ai_related=True
    )
    test_db.add(story)
    test_db.commit()

    dedup = Deduplicator(test_db)
    is_dup, existing, reason = dedup.check_duplicate(
        raw_url="https://openai.com/index/deep-research",
        title="Introducing Deep Research",
        content="content"
    )
    assert is_dup is True
    assert reason == "exact_url_match"

def test_deduplicator_tracking_urls(test_db):
    src = test_db.query(Source).first()
    canonical = "https://openai.com/index/deep-research"
    norm_title = "Introducing Deep Research"
    hash_sig = generate_content_hash(canonical, norm_title, "content")
    
    story = Story(
        source_id=src.id,
        canonical_url=canonical,
        original_url=canonical,
        title="Introducing Deep Research",
        normalized_title=norm_title,
        hash_signature=hash_sig,
        published_at=datetime.now(timezone.utc),
        is_ai_related=True
    )
    test_db.add(story)
    test_db.commit()

    dedup = Deduplicator(test_db)
    # Incoming URL with varied tracking params
    is_dup, existing, reason = dedup.check_duplicate(
        raw_url="https://openai.com/index/deep-research?utm_source=newsletter&utm_medium=email&ref=hacker_news&fbclid=abc1234",
        title="Introducing Deep Research",
        content="content"
    )
    assert is_dup is True
    assert reason == "exact_url_match"

def test_deduplicator_fuzzy_title_with_context(test_db):
    src = test_db.query(Source).first()
    canonical = "https://openai.com/index/deep-research"
    norm_title = "OpenAI Releases Autonomous Deep Research Synthesis Agent"
    hash_sig = generate_content_hash(canonical, norm_title, "content")
    pub_time = datetime.now(timezone.utc)
    
    story = Story(
        source_id=src.id,
        canonical_url=canonical,
        original_url=canonical,
        title=norm_title,
        normalized_title=norm_title,
        hash_signature=hash_sig,
        published_at=pub_time,
        companies=["OpenAI"],
        topics=["Autonomous Agents"],
        is_ai_related=True
    )
    test_db.add(story)
    test_db.commit()

    dedup = Deduplicator(test_db)
    # Similar title reposted by aggregator within time window
    is_dup, existing, reason = dedup.check_duplicate(
        raw_url="https://tech-blog.com/openai-autonomous-deep-research-agent",
        title="OpenAI Releases Autonomous Deep Research Agent",
        companies=["OpenAI"],
        topics=["Autonomous Agents"],
        published_at=pub_time + timedelta(hours=2),
        source_category="Industry"
    )
    assert is_dup is True
    assert "fuzzy" in reason

def test_deduplicator_prevents_false_positive(test_db):
    src = test_db.query(Source).first()
    canonical = "https://openai.com/index/gpt-4-release"
    norm_title = "Announcing GPT-4 Frontier Foundation Model"
    hash_sig = generate_content_hash(canonical, norm_title, "content")
    pub_time = datetime(2023, 3, 14, 12, 0, 0, tzinfo=timezone.utc)
    
    story = Story(
        source_id=src.id,
        canonical_url=canonical,
        original_url=canonical,
        title=norm_title,
        normalized_title=norm_title,
        hash_signature=hash_sig,
        published_at=pub_time,
        companies=["OpenAI"],
        topics=["LLMs"],
        is_ai_related=True
    )
    test_db.add(story)
    test_db.commit()

    dedup = Deduplicator(test_db)
    
    # Story 2: Similar title phrase ("Announcing GPT-4.5 Frontier Foundation Model") but different company/timeframe
    is_dup, existing, reason = dedup.check_duplicate(
        raw_url="https://openai.com/index/gpt-4-5-release",
        title="Announcing GPT-4.5 Frontier Foundation Model",
        companies=["OpenAI"],
        topics=["LLMs"],
        published_at=datetime(2025, 2, 20, 12, 0, 0, tzinfo=timezone.utc),
        source_category="Lab"
    )
    # Outside time window and distinct version -> must NOT be marked as duplicate
    assert is_dup is False
    assert reason == "unique"

def test_deduplicator_prevents_false_positive_different_companies(test_db):
    src = test_db.query(Source).first()
    canonical = "https://anthropic.com/news/claude-reasoning"
    norm_title = "New Frontier Reasoning Capabilities Released"
    hash_sig = generate_content_hash(canonical, norm_title, "anthropic content")
    pub_time = datetime.now(timezone.utc)
    
    story = Story(
        source_id=src.id,
        canonical_url=canonical,
        original_url=canonical,
        title=norm_title,
        normalized_title=norm_title,
        hash_signature=hash_sig,
        published_at=pub_time,
        companies=["Anthropic"],
        topics=["Reasoning"],
        is_ai_related=True
    )
    test_db.add(story)
    test_db.commit()

    dedup = Deduplicator(test_db)
    
    # Different company publishes a story with similar generic phrasing
    is_dup, existing, reason = dedup.check_duplicate(
        raw_url="https://deepseek.com/r1-reasoning",
        title="New Open Reasoning Model Released",
        companies=["DeepSeek"],
        topics=["Open Weights"],
        published_at=pub_time,
        source_category="Lab"
    )
    assert is_dup is False
    assert reason == "unique"
