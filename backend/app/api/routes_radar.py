from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.app.database import get_db
from backend.app.models.story import Story
from backend.app.models.source import Source
from backend.app.models.interaction import Interaction
from backend.app.schemas.story import StoryOut
from backend.app.schemas.interaction import InteractionCreate, RadarInteractResponse
from backend.app.services.personalization import PersonalizationService
from backend.app.services.ranker import calculate_story_rank
from backend.app.config import settings

router = APIRouter(prefix="/api/radar", tags=["Radar"])

class AskRadarRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

class AskRadarResponse(BaseModel):
    query: str
    answer: str
    key_takeaways: List[str]
    cited_stories: List[StoryOut]
    total_matches: int

class OvernightDispatchResponse(BaseModel):
    period: str
    total_signals_detected: int
    top_breakthroughs_count: int
    executive_summary: str
    key_developments: List[Dict[str, Any]]
    stories: List[StoryOut]

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from backend.app.services.scheduler import is_scan_running, run_scheduled_intelligence_scan

@router.get("/deck", response_model=List[StoryOut])
def get_radar_deck(
    background_tasks: BackgroundTasks,
    limit: int = Query(25, ge=5, le=100),
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    Returns prioritized cards for the interactive swipe deck.
    Automatically triggers minute-to-minute live background scanning on reload.
    """
    if not is_scan_running():
        background_tasks.add_task(run_scheduled_intelligence_scan)

    personalization = PersonalizationService(db)
    user_weights = personalization.get_user_topic_weights(user_id)

    
    swiped_story_ids = set(
        row[0] for row in db.query(Interaction.story_id).filter(
            Interaction.session_id == user_id,
            Interaction.interaction_type.in_(["swipe_right", "swipe_left", "interested", "skip", "like", "dislike"])
        ).all()
    )

    candidate_stories = db.query(Story).filter(
        Story.is_ai_related == True,
        Story.status == "processed"
    ).order_by(desc(Story.published_at)).limit(100).all()

    saved_ids = set(
        row[0] for row in db.query(Interaction.story_id).filter(
            Interaction.session_id == user_id,
            Interaction.interaction_type == "save"
        ).all()
    )

    deck: List[StoryOut] = []
    
    for story in candidate_stories:
        rank_score = calculate_story_rank(
            importance_score=story.importance_score or 50.0,
            novelty_score=story.novelty_score or 50.0,
            published_at=story.published_at,
            story_category=story.category,
            story_topics=story.topics or [],
            story_companies=story.companies or [],
            story_technologies=story.technologies or [],
            user_topic_weights=user_weights,
            is_breaking=story.is_breaking or False
        )
        s_out = StoryOut.model_validate(story)
        s_out.source_name = story.source.name if story.source else "AI Source"
        s_out.source_icon = story.source.icon_url if story.source else None
        s_out.is_saved = story.id in saved_ids
        s_out.rank_score = rank_score
        
        if story.id in swiped_story_ids:
            s_out.interaction_state = "swiped"
            
        deck.append(s_out)

    unswiped = [s for s in deck if s.interaction_state != "swiped"]
    unswiped.sort(key=lambda x: x.rank_score or 0.0, reverse=True)
    
    if len(unswiped) < 5:
        return deck[:limit]
        
    return unswiped[:limit]

@router.post("/interact", response_model=RadarInteractResponse)
def record_radar_interaction(
    payload: InteractionCreate,
    db: Session = Depends(get_db)
):
    """
    Records a swipe or save action and updates personal preference weights.
    """
    story = db.query(Story).filter(Story.id == payload.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    personalization = PersonalizationService(db)
    updated_topics = personalization.record_interaction(
        story_id=payload.story_id,
        interaction_type=payload.interaction_type,
        user_id=payload.session_id or "default_user"
    )

    action_name = payload.interaction_type.replace("_", " ").title()
    return RadarInteractResponse(
        success=True,
        interaction_type=payload.interaction_type,
        story_id=payload.story_id,
        topics_updated=updated_topics,
        message=f"{action_name} recorded. Preference vector updated for {len(updated_topics)} topics."
    )

@router.get("/overnight", response_model=OvernightDispatchResponse)
def get_overnight_dispatch(
    hours: int = Query(48, ge=6, le=168),
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    FEATURE: WHAT CHANGED OVERNIGHT?
    Synthesizes executive intelligence briefing for the last 24-48 hours.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stories = db.query(Story).filter(
        Story.is_ai_related == True,
        Story.published_at >= cutoff
    ).order_by(desc(Story.importance_score), desc(Story.published_at)).limit(15).all()

    if not stories:
        stories = db.query(Story).filter(Story.is_ai_related == True).order_by(desc(Story.importance_score)).limit(8).all()

    saved_ids = set(
        row[0] for row in db.query(Interaction.story_id).filter(
            Interaction.session_id == user_id,
            Interaction.interaction_type == "save"
        ).all()
    )
    personalizer = PersonalizationService(db)
    user_weights = personalizer.get_user_topic_weights(user_id)

    formatted_stories = []
    for s in stories:
        s_out = StoryOut.model_validate(s)
        s_out.source_name = s.source.name if s.source else "AI Source"
        s_out.source_icon = s.source.icon_url if s.source else None
        s_out.is_saved = s.id in saved_ids
        s_out.rank_score = calculate_story_rank(
            importance_score=s.importance_score or 50.0,
            novelty_score=s.novelty_score or 50.0,
            published_at=s.published_at,
            story_category=s.category,
            story_topics=s.topics or [],
            story_companies=s.companies or [],
            story_technologies=s.technologies or [],
            user_topic_weights=user_weights,
            is_breaking=s.is_breaking or False
        )
        formatted_stories.append(s_out)

    breaking_count = sum(1 for s in stories if s.is_breaking)
    top_labs = list(set([c for s in stories for c in (s.companies or [])]))[:4]

    exec_summary = (
        f"Over the last {hours} hours, CLIVE detected {len(stories)} high-signal developments across "
        f"{', '.join(top_labs) if top_labs else 'major AI research labs'}. Key shifts emphasize frontier reasoning architectures, "
        f"agentic developer workflows, and hardware inference optimizations."
    )

    key_developments = [
        {
            "category": s.category,
            "headline": s.headline or s.title,
            "importance": s.importance_score,
            "company": s.companies[0] if s.companies else "Research Lab",
            "impact": s.why_it_matters[0] if s.why_it_matters else s.summary
        }
        for s in stories[:4]
    ]

    return OvernightDispatchResponse(
        period=f"Last {hours} Hours",
        total_signals_detected=len(stories),
        top_breakthroughs_count=breaking_count,
        executive_summary=exec_summary,
        key_developments=key_developments,
        stories=formatted_stories
    )

@router.post("/ask", response_model=AskRadarResponse)
def ask_radar_rag(
    payload: AskRadarRequest,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    FEATURE: ASK RADAR (RAG over collected intelligence stories)
    Synthesizes answers citing specific collected intelligence stories.
    """
    q_clean = payload.query.strip().lower()
    terms = q_clean.split()
    
    # Query stories by relevance
    query = db.query(Story).filter(Story.is_ai_related == True)
    
    filter_clauses = [
        Story.title.ilike(f"%{q_clean}%"),
        Story.headline.ilike(f"%{q_clean}%"),
        Story.summary.ilike(f"%{q_clean}%"),
        Story.extracted_content.ilike(f"%{q_clean}%"),
        Story.category.ilike(f"%{q_clean}%")
    ]
    for t in terms:
        if len(t) > 2:
            filter_clauses.append(Story.title.ilike(f"%{t}%"))
            filter_clauses.append(Story.summary.ilike(f"%{t}%"))
            
    matching_stories = query.filter(or_(*filter_clauses)).order_by(desc(Story.importance_score), desc(Story.published_at)).limit(payload.limit or 5).all()
    
    if not matching_stories:
        matching_stories = db.query(Story).filter(Story.is_ai_related == True).order_by(desc(Story.importance_score)).limit(3).all()

    saved_ids = set(
        row[0] for row in db.query(Interaction.story_id).filter(
            Interaction.session_id == user_id,
            Interaction.interaction_type == "save"
        ).all()
    )
    personalizer = PersonalizationService(db)
    user_weights = personalizer.get_user_topic_weights(user_id)

    cited = []
    for s in matching_stories:
        s_out = StoryOut.model_validate(s)
        s_out.source_name = s.source.name if s.source else "AI Source"
        s_out.source_icon = s.source.icon_url if s.source else None
        s_out.is_saved = s.id in saved_ids
        s_out.rank_score = calculate_story_rank(
            importance_score=s.importance_score or 50.0,
            novelty_score=s.novelty_score or 50.0,
            published_at=s.published_at,
            story_category=s.category,
            story_topics=s.topics or [],
            story_companies=s.companies or [],
            story_technologies=s.technologies or [],
            user_topic_weights=user_weights,
            is_breaking=s.is_breaking or False
        )
        cited.append(s_out)

    # Structured answer generation
    top_headlines = [f"• {s.headline or s.title} ({s.source.name if s.source else 'Source'})" for s in matching_stories[:3]]
    answer = (
        f"Based on first-party intelligence reports on '{payload.query}', here is the current state of development:\n\n"
        + "\n".join(top_headlines)
    )
    takeaways = [
        f"Primary momentum centers around {matching_stories[0].category if matching_stories else 'AI architectures'}.",
        f"Key participating organizations include {', '.join(matching_stories[0].companies or ['frontier labs'])}.",
        "Key impact: Shifts development velocity and reduces production latency for practitioner pipelines."
    ]

    return AskRadarResponse(
        query=payload.query,
        answer=answer,
        key_takeaways=takeaways,
        cited_stories=cited,
        total_matches=len(matching_stories)
    )
