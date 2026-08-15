import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.services.collector import FeedCollectorService

logger = logging.getLogger(__name__)

# Global singleton scheduler and telemetry state
scheduler = BackgroundScheduler()
_is_initialized = False

# Live scan telemetry stats store
scan_stats: Dict[str, Any] = {
    "is_scanning": False,
    "last_scan_started_at": None,
    "last_scan_completed_at": None,
    "last_scan_duration_sec": 0.0,
    "sources_scanned": 0,
    "sources_failed": 0,
    "items_discovered": 0,
    "items_duplicates": 0,
    "items_rejected_non_ai": 0,
    "items_stored": 0,
    "important_stories_count": 0,
    "last_status": "idle"
}

def run_scheduled_intelligence_scan() -> Dict[str, Any]:
    """
    Executes the full CLIVE Intelligence Pipeline:
    collect -> normalize -> dedupe -> classify -> summarize -> persist.
    Tracks granular telemetry statistics.
    """
    global scan_stats
    if scan_stats["is_scanning"]:
        logger.warning("Scan cycle already active; skipping concurrent scheduler tick.")
        return scan_stats

    scan_stats["is_scanning"] = True
    scan_stats["last_scan_started_at"] = datetime.now(timezone.utc)
    scan_stats["last_status"] = "scanning"
    start_time = time.time()

    db = SessionLocal()
    try:
        logger.info("📡 [CLIVE RADAR] Executing scheduled multi-source intelligence ingestion...")
        collector = FeedCollectorService(db)
        summary = collector.scan_all_active_sources()
        
        # Calculate importance counts
        from backend.app.models.story import Story
        imp_count = db.query(Story).filter(Story.importance_score >= settings.IMPORTANCE_SUMMARY_THRESHOLD).count()

        # Update telemetry
        scan_stats["sources_scanned"] = summary.get("total_sources", 0)
        scan_stats["sources_failed"] = summary.get("failed_sources", 0)
        discovered = sum(d.get("items_found", 0) for d in summary.get("details", []))
        scan_stats["items_discovered"] = discovered
        scan_stats["items_duplicates"] = summary.get("total_duplicates", 0)
        scan_stats["items_stored"] = summary.get("total_items_saved", 0)
        scan_stats["items_rejected_non_ai"] = max(0, discovered - scan_stats["items_duplicates"] - scan_stats["items_stored"])
        scan_stats["important_stories_count"] = imp_count
        scan_stats["last_status"] = "success"

        logger.info(
            f"✅ [CLIVE RADAR] Scan complete: {scan_stats['items_stored']} new signals saved "
            f"({scan_stats['items_duplicates']} dups, {scan_stats['items_rejected_non_ai']} rejected) "
            f"across {scan_stats['sources_scanned']} feeds in {time.time() - start_time:.2f}s."
        )
    except Exception as ex:
        logger.error(f"❌ [CLIVE RADAR] Error during scheduled scan: {ex}", exc_info=True)
        scan_stats["last_status"] = f"error: {str(ex)[:100]}"
    finally:
        db.close()
        scan_stats["is_scanning"] = False
        scan_stats["last_scan_completed_at"] = datetime.now(timezone.utc)
        scan_stats["last_scan_duration_sec"] = round(time.time() - start_time, 2)

    return scan_stats

def get_scan_telemetry() -> Dict[str, Any]:
    """Returns current live scan telemetry stats."""
    return scan_stats

def is_scan_running() -> bool:
    return scan_stats["is_scanning"]

def start_scheduler():
    """Starts the background feed scheduler once, preventing duplicate reload instances."""
    global _is_initialized
    if _is_initialized or scheduler.running:
        logger.info("CLIVE scheduler already running (skipping duplicate startup).")
        return

    try:
        scheduler.add_job(
            func=run_scheduled_intelligence_scan,
            trigger=IntervalTrigger(minutes=settings.SCAN_INTERVAL_MINUTES),
            id="clive_scheduled_feed_scan",
            name="CLIVE AI Feed Ingestion",
            replace_existing=True
        )
        scheduler.start()
        _is_initialized = True
        logger.info(f"🚀 CLIVE scheduler initialized. Auto-scanning every {settings.SCAN_INTERVAL_MINUTES} minutes.")
    except Exception as e:
        logger.warning(f"Scheduler startup notice: {e}")

def shutdown_scheduler():
    """Gracefully shuts down scheduler."""
    global _is_initialized
    if scheduler.running:
        scheduler.shutdown(wait=False)
        _is_initialized = False
        logger.info("CLIVE scheduler stopped.")
