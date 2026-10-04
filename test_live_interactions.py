import httpx
from fastapi.testclient import TestClient
from backend.app.main import app

def get_client():
    try:
        c = httpx.Client(base_url="http://127.0.0.1:8000", timeout=2.0)
        r = c.get("/api/health")
        if r.status_code == 200 and r.json().get("status") == "healthy":
            return c
    except Exception:
        pass
    return TestClient(app)

def main():
    client = get_client()

    # 1. Fetch stories
    res = client.get("/api/stories?limit=3").json()
    stories = res.get("stories", [])
    print(f"1. Stories fetched: {len(stories)} stories available.")
    s1 = stories[0]
    title = s1["title"][:50]
    print(f"   Target Story: [{s1['id']}] {title}...")
    print(f"   Story Topics: {s1.get('topics', [])}")

    # 2. Record Swipe Right (Interested)
    r1 = client.post("/api/radar/interact", json={"story_id": s1["id"], "interaction_type": "swipe_right", "session_id": "default_user"}).json()
    print(f"2. Swipe Right Result: {r1['message']}")

    # 3. Record Save Bookmark
    r2 = client.post("/api/radar/interact", json={"story_id": s1["id"], "interaction_type": "save", "session_id": "default_user"}).json()
    print(f"3. Save Result: {r2['message']}")

    # 4. Record Read Source
    r3 = client.post("/api/interactions", json={"story_id": s1["id"], "interaction_type": "open_source", "session_id": "default_user"}).json()
    print(f"4. Open Source Result: {r3['message']}")

    # 5. Check preferences
    prefs = client.get("/api/preferences?user_id=default_user").json()
    print("\n5. Top Updated Topic Weights in Database:")
    for p in prefs[:6]:
        topic = p["topic"]
        w = p["weight"]
        pos = p["positive_count"]
        neg = p["negative_count"]
        print(f"   - {topic}: weight={w:.2f} (pos={pos}, neg={neg})")

    # 6. Verify personalized feed ranking
    feed = client.get("/api/feed?limit=3").json()
    print("\n6. Personalized Ranked Feed (40% Imp + 30% Rel + 20% Rec + 10% Nov):")
    for st in feed["stories"][:3]:
        headline = st["headline"] or st["title"]
        rank = st["rank_score"]
        cat = st["category"]
        print(f"   - Rank {rank:.1f} | [{cat}] {headline[:65]}")

if __name__ == "__main__":
    main()

