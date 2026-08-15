from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_

from backend.app.database import get_db
from backend.app.models.story import Story
from backend.app.models.interaction import Interaction
from backend.app.schemas.story import StoryOut, StoryFeedResponse
from backend.app.schemas.interaction import RadarInteractResponse
from backend.app.services.personalization import PersonalizationService
from backend.app.services.ranker import calculate_story_rank

router = APIRouter(prefix="/api/stories", tags=["Stories"])

def _format_story_out(story: Story, user_id: str, saved_ids: set, user_weights: dict) -> StoryOut:
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
def list_stories(
    category: Optional[str] = Query(None, description="Filter by category"),
    q: Optional[str] = Query(None, description="Search query across title, headline, summary"),
    is_breaking: Optional[bool] = Query(None, description="Filter by breaking flag"),
    min_importance: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum importance score"),
    sort_by: str = Query("published_at", description="Sort field: published_at, importance, novelty, technical"),
    order: str = Query("desc", description="Sort order: desc or asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    GET /api/stories: General stories list with filtering, searching, and sorting.
    """
    saved_ids = set(
        row[0] for row in db.query(Interaction.story_id).filter(
            Interaction.session_id == user_id,
            Interaction.interaction_type == "save"
        ).all()
    )
    
    personalizer = PersonalizationService(db)
    user_weights = personalizer.get_user_topic_weights(user_id)

    query = db.query(Story).filter(Story.is_ai_related == True)

    if category and category.lower() != "all":
        query = query.filter(Story.category == category)

    if is_breaking is not None:
        query = query.filter(Story.is_breaking == is_breaking)

    if min_importance is not None:
        query = query.filter(Story.importance_score >= min_importance)

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Story.title.ilike(search_pattern),
                Story.headline.ilike(search_pattern),
                Story.summary.ilike(search_pattern)
            )
        )

    # Sorting
    if sort_by == "importance":
        sort_col = Story.importance_score
    elif sort_by == "novelty":
        sort_col = Story.novelty_score
    elif sort_by == "technical":
        sort_col = Story.technical_score
    else:
        sort_col = Story.published_at

    query = query.order_by(desc(sort_col) if order == "desc" else asc(sort_col))

    total = query.count()
    stories = query.offset((page - 1) * limit).limit(limit).all()

    formatted = [_format_story_out(s, user_id, saved_ids, user_weights) for s in stories]

    return StoryFeedResponse(
        stories=formatted,
        total=total,
        page=page,
        has_more=(page * limit) < total
    )

@router.get("/{id}", response_model=StoryOut)
def get_story(
    id: int,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    GET /api/stories/{id}: Single story detail briefing.
    """
    story = db.query(Story).filter(Story.id == id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    saved_ids = set(
        row[0] for row in db.query(Interaction.story_id).filter(
            Interaction.session_id == user_id,
            Interaction.interaction_type == "save"
        ).all()
    )
    personalizer = PersonalizationService(db)
    user_weights = personalizer.get_user_topic_weights(user_id)

    return _format_story_out(story, user_id, saved_ids, user_weights)

@router.post("/{id}/like", response_model=RadarInteractResponse)
def like_story(
    id: int,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    POST /api/stories/{id}/like: Swipes right / marks interested and boosts topic weights (+0.25).
    """
    story = db.query(Story).filter(Story.id == id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    personalizer = PersonalizationService(db)
    updated = personalizer.record_interaction(story_id=id, interaction_type="swipe_right", user_id=user_id)
    return RadarInteractResponse(
        success=True,
        interaction_type="like",
        story_id=id,
        topics_updated=updated,
        message=f"Story liked. Topic weights boosted for {len(updated)} topics."
    )

@router.post("/{id}/dislike", response_model=RadarInteractResponse)
def dislike_story(
    id: int,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    POST /api/stories/{id}/dislike: Swipes left / skips story and gently discounts topic weights (-0.08).
    """
    story = db.query(Story).filter(Story.id == id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    personalizer = PersonalizationService(db)
    updated = personalizer.record_interaction(story_id=id, interaction_type="swipe_left", user_id=user_id)
    return RadarInteractResponse(
        success=True,
        interaction_type="dislike",
        story_id=id,
        topics_updated=updated,
        message=f"Story skipped. Topic weights discounted for {len(updated)} topics."
    )

@router.post("/{id}/save", response_model=RadarInteractResponse)
def save_story(
    id: int,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    POST /api/stories/{id}/save: Bookmarks story and heavily boosts topic weights (+0.45).
    """
    story = db.query(Story).filter(Story.id == id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check if already saved
    existing = db.query(Interaction).filter(
        Interaction.story_id == id,
        Interaction.session_id == user_id,
        Interaction.interaction_type == "save"
    ).first()

    personalizer = PersonalizationService(db)
    if existing:
        # Unsave
        db.delete(existing)
        db.commit()
        return RadarInteractResponse(
            success=True,
            interaction_type="unsave",
            story_id=id,
            topics_updated=[],
            message="Story removed from saved collection."
        )

    updated = personalizer.record_interaction(story_id=id, interaction_type="save", user_id=user_id)
    return RadarInteractResponse(
        success=True,
        interaction_type="save",
        story_id=id,
        topics_updated=updated,
        message=f"Story bookmarked. Topic weights boosted for {len(updated)} topics."
    )

@router.post("/{id}/source-open", response_model=RadarInteractResponse)
def open_story_source(
    id: int,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """
    POST /api/stories/{id}/source-open: Records external link click and reinforces topic weights (+0.15).
    """
    story = db.query(Story).filter(Story.id == id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    personalizer = PersonalizationService(db)
    updated = personalizer.record_interaction(story_id=id, interaction_type="open_source", user_id=user_id)
    return RadarInteractResponse(
        success=True,
        interaction_type="source-open",
        story_id=id,
        topics_updated=updated,
        message=f"Source link opened. Topic weights reinforced for {len(updated)} topics."
    )
