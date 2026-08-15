from typing import Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db, SessionLocal
from backend.app.models.source import Source
from backend.app.models.story import Story
from backend.app.models.interaction import Interaction
from backend.app.models.preference import TopicWeight
from backend.app.schemas.stats import RadarStatsOut, CategoryCount
from backend.app.services.scheduler import get_scan_telemetry, is_scan_running
from backend.app.services.collector import FeedCollectorService

router = APIRouter(tags=["Status & Admin"])

def _run_admin_scan():
    db = SessionLocal()
    try:
        collector = FeedCollectorService(db)
        collector.scan_all_active_sources()
    finally:
        db.close()

@router.get("/api/stats", response_model=RadarStatsOut)
@router.get("/api/status", response_model=RadarStatsOut)
def get_radar_status_and_stats(db: Session = Depends(get_db)):
    """
    GET /api/status & GET /api/stats: Complete radar telemetry and system statistics.
    """
    total_sources = db.query(func.count(Source.id)).scalar() or 0
    active_sources = db.query(func.count(Source.id)).filter(Source.is_active == True).scalar() or 0
    total_stories = db.query(func.count(Story.id)).scalar() or 0
    breaking_count = db.query(func.count(Story.id)).filter(Story.is_breaking == True).scalar() or 0
    saved_count = db.query(func.count(Interaction.id)).filter(Interaction.interaction_type == "save").scalar() or 0
    total_interactions = db.query(func.count(Interaction.id)).scalar() or 0

    # Last scan time
    last_scan = db.query(func.max(Source.last_scanned_at)).scalar()

    # Category distribution
    cat_rows = db.query(Story.category, func.count(Story.id)).group_by(Story.category).all()
    categories = [CategoryCount(category=c[0], count=c[1]) for c in cat_rows if c[0]]

    # Top topics
    topic_rows = db.query(TopicWeight.topic).filter(
        TopicWeight.user_id == "default_user"
    ).order_by(TopicWeight.weight.desc()).limit(8).all()
    top_topics = [t[0] for t in topic_rows]

    # Live telemetry
    telemetry = get_scan_telemetry()

    return RadarStatsOut(
        total_sources=total_sources,
        active_sources=active_sources,
        total_stories=total_stories,
        breaking_stories_count=breaking_count,
        saved_stories_count=saved_count,
        total_interactions=total_interactions,
        last_scan_time=last_scan or telemetry.get("last_scan_completed_at"),
        is_scanning=is_scan_running(),
        sources_scanned=telemetry.get("sources_scanned", 0),
        sources_failed=telemetry.get("sources_failed", 0),
        items_discovered=telemetry.get("items_discovered", 0),
        items_duplicates=telemetry.get("items_duplicates", 0),
        items_rejected_non_ai=telemetry.get("items_rejected_non_ai", 0),
        items_stored=telemetry.get("items_stored", 0),
        important_stories_count=telemetry.get("important_stories_count", 0),
        last_scan_duration_sec=telemetry.get("last_scan_duration_sec", 0.0),
        category_distribution=categories,
        top_topics=top_topics
    )

@router.post("/api/admin/scan")
def trigger_admin_scan(background_tasks: BackgroundTasks):
    """
    POST /api/admin/scan: Trigger full intelligence scan across all active sources.
    """
    if is_scan_running():
        return {
            "status": "already_running",
            "is_scanning": True,
            "message": "A scan is already active in the background."
        }

    background_tasks.add_task(_run_admin_scan)
    return {
        "status": "started",
        "is_scanning": True,
        "message": "Manual intelligence scan initiated across all active sources."
    }
