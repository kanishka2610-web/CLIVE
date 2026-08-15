import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.seeds.sources import seed_database_if_empty

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database_if_empty(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

# 1. GET /api/health
def test_contract_get_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

# 2. GET /api/stories
def test_contract_get_stories(client):
    res = client.get("/api/stories?limit=5")
    assert res.status_code == 200
    assert "stories" in res.json()
    assert len(res.json()["stories"]) > 0

# 3. GET /api/stories/{id}
def test_contract_get_story_by_id(client):
    feed = client.get("/api/stories?limit=1").json()
    story_id = feed["stories"][0]["id"]
    res = client.get(f"/api/stories/{story_id}")
    assert res.status_code == 200
    assert res.json()["id"] == story_id

# 4. GET /api/feed
def test_contract_get_feed(client):
    res = client.get("/api/feed?limit=5")
    assert res.status_code == 200
    assert "stories" in res.json()
    assert res.json()["stories"][0]["rank_score"] is not None

# 5. GET /api/feed/trending
def test_contract_get_feed_trending(client):
    res = client.get("/api/feed/trending?limit=5")
    assert res.status_code == 200
    assert "stories" in res.json()

# 6. GET /api/feed/saved
def test_contract_get_feed_saved(client):
    res = client.get("/api/feed/saved")
    assert res.status_code == 200
    assert "stories" in res.json()

# 7. POST /api/stories/{id}/like
def test_contract_post_story_like(client):
    feed = client.get("/api/stories?limit=1").json()
    story_id = feed["stories"][0]["id"]
    res = client.post(f"/api/stories/{story_id}/like")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["interaction_type"] == "like"

# 8. POST /api/stories/{id}/dislike
def test_contract_post_story_dislike(client):
    feed = client.get("/api/stories?limit=1").json()
    story_id = feed["stories"][0]["id"]
    res = client.post(f"/api/stories/{story_id}/dislike")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["interaction_type"] == "dislike"

# 9. POST /api/stories/{id}/save
def test_contract_post_story_save(client):
    feed = client.get("/api/stories?limit=1").json()
    story_id = feed["stories"][0]["id"]
    res = client.post(f"/api/stories/{story_id}/save")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["interaction_type"] in ["save", "unsave"]

# 10. POST /api/stories/{id}/source-open
def test_contract_post_story_source_open(client):
    feed = client.get("/api/stories?limit=1").json()
    story_id = feed["stories"][0]["id"]
    res = client.post(f"/api/stories/{story_id}/source-open")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["interaction_type"] == "source-open"

# 11. GET /api/sources
def test_contract_get_sources(client):
    res = client.get("/api/sources")
    assert res.status_code == 200
    assert len(res.json()) >= 9

# 12. POST /api/sources
def test_contract_post_sources(client):
    payload = {
        "name": "Test Source Lab",
        "url": "https://example.com/test-ai-feed.xml",
        "feed_type": "rss",
        "category": "Lab",
        "is_active": True
    }
    res = client.post("/api/sources", json=payload)
    assert res.status_code == 200
    assert res.json()["name"] == "Test Source Lab"

# 13. PATCH /api/sources/{id}
def test_contract_patch_source(client):
    sources = client.get("/api/sources").json()
    target_id = sources[0]["id"]
    res = client.patch(f"/api/sources/{target_id}", json={"name": "Updated Lab Name"})
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Lab Name"

# 14. DELETE /api/sources/{id}
def test_contract_delete_source(client):
    payload = {
        "name": "To Delete Lab",
        "url": "https://example.com/to-delete.xml",
        "feed_type": "rss",
        "category": "Lab"
    }
    create_res = client.post("/api/sources", json=payload).json()
    delete_res = client.delete(f"/api/sources/{create_res['id']}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

# 15. GET /api/preferences
def test_contract_get_preferences(client):
    res = client.get("/api/preferences?user_id=default_user")
    assert res.status_code == 200
    assert len(res.json()) > 0

# 16. GET /api/status
def test_contract_get_status(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    assert "total_stories" in res.json()
    assert "is_scanning" in res.json()

# 17. POST /api/admin/scan
def test_contract_post_admin_scan(client):
    with patch("backend.app.api.routes_stats._run_admin_scan"):
        res = client.post("/api/admin/scan")
        assert res.status_code == 200
        assert "status" in res.json()
        assert "is_scanning" in res.json()

# 18. GET /api/radar/overnight
def test_get_overnight_dispatch(client):
    res = client.get("/api/radar/overnight?hours=48")
    assert res.status_code == 200
    data = res.json()
    assert "executive_summary" in data
    assert "key_developments" in data
    assert len(data["stories"]) > 0

# 19. POST /api/radar/ask
def test_post_ask_radar_rag(client):
    res = client.post("/api/radar/ask", json={"query": "reasoning models", "limit": 3})
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "key_takeaways" in data
    assert len(data["cited_stories"]) > 0
