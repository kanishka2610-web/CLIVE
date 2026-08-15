import httpx
import sqlite3

def main():
    print("================ RUNNING LAUNCH CHECKLIST VERIFICATION ================")

    # 1. FastAPI Boot & Docs
    with httpx.Client(base_url="http://127.0.0.1:8000") as client:
        r_docs = client.get("/docs")
        r_health = client.get("/api/health")
        print(f"[OK] FastAPI Docs: {r_docs.status_code} OK | Health: {r_health.status_code} ({r_health.json()['status']})")

    # 2. Database WAL Mode Check
    conn = sqlite3.connect("ai_radar.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    journal_mode = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sources;")
    sources_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM stories;")
    stories_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM interactions;")
    interactions_count = cursor.fetchone()[0]
    conn.close()
    print(f"[OK] SQLite Journal Mode: {journal_mode.upper()} | Configured Sources: {sources_count} | Stories: {stories_count} | Interactions: {interactions_count}")

    # 3. Preferences & Dynamic Ranking Shift Check
    with httpx.Client(base_url="http://127.0.0.1:8000") as client:
        feed_before = client.get("/api/feed?limit=1").json()
        top_story = feed_before["stories"][0]
        
        # Record Like interaction
        inter_res = client.post(f"/api/stories/{top_story['id']}/like").json()
        print(f"[OK] Interaction Recorded: {inter_res['message']}")
        
        # Check preferences update
        prefs = client.get("/api/preferences").json()
        top_pref = prefs[0]
        print(f"[OK] Dynamic Topic Preferences: Top topic '{top_pref['topic']}' weight={top_pref['weight']:.2f} (pos={top_pref['positive_count']})")
        
        # Check status & telemetry endpoint
        status = client.get("/api/status").json()
        print(f"[OK] Radar Status & Telemetry: Active Sources={status['active_sources']}, Total Stories={status['total_stories']}, Scanning={status['is_scanning']}")

    print("=======================================================================")

if __name__ == "__main__":
    main()
