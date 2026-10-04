from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.app.database import get_db
from backend.app.models.story import Story
from backend.app.models.interaction import Interaction
from backend.app.schemas.story import StoryOut, StoryFeedResponse
from backend.app.services.personalization import PersonalizationService
from backend.app.services.ranker import calculate_story_rank
from backend.app.services.scheduler import is_scan_running, run_scheduled_intelligence_scan

router = APIRouter(prefix="/api/feed", tags=["Feed"])


def format_ranked_story(story: Story, user_id: str, saved_ids: set, user_weights: dict) -> StoryOut:
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
    return s_out

@router.get("", response_model=StoryFeedResponse)
def get_personalized_feed(
    background_tasks: BackgroundTasks,
    category: Optional[str] = Query(None, description="Filter by category"),
    q: Optional[str] = Query(None, description="Search term across title, headline, summary"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    GET /api/feed: Personalized ranked feed calculated using:
    40% Importance + 30% Personal Relevance + 20% Recency + 10% Novelty + Breaking Boost.
    Automatically triggers minute-to-minute live background scanning on reload.
    """
    if not is_scan_running():
        background_tasks.add_task(run_scheduled_intelligence_scan)

    personalizer = PersonalizationService(db)
    user_weights = personalizer.get_user_topic_weights(user_id)

    saved_ids = set(
        row[0] for row in db.query(Interaction.story_id).filter(
            Interaction.session_id == user_id,
            Interaction.interaction_type == "save"
        ).all()
    )

    query = db.query(Story).filter(Story.is_ai_related == True)

    if category and category.lower() != "all":
        query = query.filter(Story.category == category)

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Story.title.ilike(search_term),
                Story.headline.ilike(search_term),
                Story.summary.ilike(search_term),
                Story.category.ilike(search_term)
            )
        )

    all_stories = query.all()

    ranked_stories = [
        format_ranked_story(s, user_id, saved_ids, user_weights)
        for s in all_stories
    ]

    # Sort descending by computed rank score
    ranked_stories.sort(key=lambda s: s.rank_score or 0.0, reverse=True)

    total = len(ranked_stories)
    start = (page - 1) * limit
    end = start + limit
    page_items = ranked_stories[start:end]
    has_more = end < total

    return StoryFeedResponse(
        stories=page_items,
        total=total,
        page=page,
        has_more=has_more
    )

@router.get("/trending", response_model=StoryFeedResponse)
def get_trending_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    GET /api/feed/trending: High-velocity & breaking radar alerts.
    """
    personalizer = PersonalizationService(db)
    user_weights = personalizer.get_user_topic_weights(user_id)
    
    saved_ids = set(
        row[0] for row in db.query(Interaction.story_id).filter(
            Interaction.session_id == user_id,
            Interaction.interaction_type == "save"
        ).all()
    )

    query = db.query(Story).filter(Story.is_ai_related == True)
    # Order prioritizing breaking status and importance
    all_stories = query.order_by(desc(Story.is_breaking), desc(Story.importance_score), desc(Story.published_at)).all()

    ranked_stories = [
        format_ranked_story(s, user_id, saved_ids, user_weights)
        for s in all_stories
    ]

    total = len(ranked_stories)
    start = (page - 1) * limit
    end = start + limit
    page_items = ranked_stories[start:end]

    return StoryFeedResponse(
        stories=page_items,
        total=total,
        page=page,
        has_more=end < total
    )

@router.get("/saved", response_model=StoryFeedResponse)
def get_saved_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    GET /api/feed/saved: Bookmarked intelligence signals collection.
    """
    personalizer = PersonalizationService(db)
    user_weights = personalizer.get_user_topic_weights(user_id)

    saved_interactions = db.query(Interaction).filter(
        Interaction.session_id == user_id,
        Interaction.interaction_type == "save"
    ).order_by(desc(Interaction.created_at)).all()

    saved_story_ids = [inter.story_id for inter in saved_interactions]
    saved_set = set(saved_story_ids)

    if not saved_story_ids:
        return StoryFeedResponse(stories=[], total=0, page=page, has_more=False)

    stories_map = {
        s.id: s for s in db.query(Story).filter(Story.id.in_(saved_story_ids)).all()
    }

    ordered_stories = []
    for sid in saved_story_ids:
        if sid in stories_map:
            ordered_stories.append(
                format_ranked_story(stories_map[sid], user_id, saved_set, user_weights)
            )

    total = len(ordered_stories)
    start = (page - 1) * limit
    end = start + limit
    page_items = ordered_stories[start:end]

    return StoryFeedResponse(
        stories=page_items,
        total=total,
        page=page,
        has_more=end < total
    )
