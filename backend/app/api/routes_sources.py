from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db, SessionLocal
from backend.app.models.source import Source
from backend.app.models.story import Story
from backend.app.schemas.source import SourceCreate, SourceUpdate, SourceOut
from backend.app.services.collector import FeedCollectorService
from backend.app.services.scheduler import is_scan_running

router = APIRouter(prefix="/api/sources", tags=["Sources"])

def _run_background_scan():
    db = SessionLocal()
    try:
        collector = FeedCollectorService(db)
        collector.scan_all_active_sources()
    finally:
        db.close()

@router.get("", response_model=List[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    """GET /api/sources: List all tracked AI feeds with story counts and health status."""
    sources = db.query(Source).all()
    out = []
    for s in sources:
        cnt = db.query(func.count(Story.id)).filter(Story.source_id == s.id).scalar() or 0
        s_out = SourceOut.model_validate(s)
        s_out.story_count = cnt
        out.append(s_out)
    return out

@router.post("", response_model=SourceOut)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    """POST /api/sources: Add a new RSS, Atom, or HTML intelligence source."""
    existing = db.query(Source).filter(Source.url == payload.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="A source with this URL already exists")
        
    src = Source(
        name=payload.name,
        url=payload.url,
        feed_type=payload.feed_type,
        category=payload.category,
        is_active=payload.is_active,
        icon_url=payload.icon_url
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    
    s_out = SourceOut.model_validate(src)
    s_out.story_count = 0
    return s_out

@router.patch("/{source_id}", response_model=SourceOut)
@router.put("/{source_id}", response_model=SourceOut)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    """PATCH & PUT /api/sources/{id}: Update source active state, name, url, or category."""
    src = db.query(Source).filter(Source.id == source_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
        
    if payload.name is not None:
        src.name = payload.name
    if payload.url is not None:
        src.url = payload.url
    if payload.feed_type is not None:
        src.feed_type = payload.feed_type
    if payload.category is not None:
        src.category = payload.category
    if payload.is_active is not None:
        src.is_active = payload.is_active
    if payload.icon_url is not None:
        src.icon_url = payload.icon_url

    db.commit()
    db.refresh(src)
    cnt = db.query(func.count(Story.id)).filter(Story.source_id == src.id).scalar() or 0
    s_out = SourceOut.model_validate(src)
    s_out.story_count = cnt
    return s_out

@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """DELETE /api/sources/{id}: Remove a source feed and its associated records."""
    src = db.query(Source).filter(Source.id == source_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
        
    db.delete(src)
    db.commit()
    return {"success": True, "message": f"Source {source_id} deleted successfully"}

@router.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    """Trigger manual scan in background."""
    if is_scan_running():
        return {"status": "already_running", "message": "Radar scan is already active."}
        
    background_tasks.add_task(_run_background_scan)
    return {"status": "started", "message": "Background scan initiated across all active sources."}
