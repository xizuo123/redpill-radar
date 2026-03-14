from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Content
from app.schemas import (
    ContentCreate,
    ContentListResponse,
    ContentResponse,
    ContentStatusUpdate,
)
from app.services.analyzer import analyze_content

router = APIRouter(prefix="/api/v1/content", tags=["Content"])


@router.post("", response_model=ContentResponse, status_code=201)
async def ingest_content(payload: ContentCreate, db: AsyncSession = Depends(get_db)):
    """Accept content from the crawler, analyze it with Groq, and store results."""
    existing = await db.execute(
        select(Content).where(Content.twitter_id == payload.twitter_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Content with twitter_id '{payload.twitter_id}' already exists",
        )

    analysis, raw_response = await analyze_content(payload.content_text, db)

    record = Content(
        twitter_id=payload.twitter_id,
        content_text=payload.content_text,
        age_category=analysis.age_category,
        content_type=analysis.content_type,
        harmful_subcategories=analysis.harmful_subcategories,
        labels=analysis.model_dump(),
        raw_analysis=raw_response,
        is_processed=False,
        processing_history=[],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("", response_model=ContentListResponse)
async def list_content(
    is_processed: bool | None = Query(None),
    content_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List content with optional filters and pagination."""
    query = select(Content)
    count_query = select(func.count(Content.id))

    if is_processed is not None:
        query = query.where(Content.is_processed == is_processed)
        count_query = count_query.where(Content.is_processed == is_processed)
    if content_type:
        query = query.where(Content.content_type == content_type)
        count_query = count_query.where(Content.content_type == content_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Content.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return ContentListResponse(items=items, total=total, page=page, limit=limit)


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a single content item by its internal UUID."""
    result = await db.execute(select(Content).where(Content.id == content_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Content not found")
    return record


@router.patch("/{content_id}/status", response_model=ContentResponse)
async def update_content_status(
    content_id: str,
    payload: ContentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Mark content as processed/unprocessed and optionally add a review comment."""
    result = await db.execute(select(Content).where(Content.id == content_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Content not found")

    old_processed = record.is_processed
    record.is_processed = payload.is_processed

    if payload.review_comment is not None:
        record.review_comment = payload.review_comment

    history = list(record.processing_history or [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "status_update",
            "old_value": old_processed,
            "new_value": payload.is_processed,
            "comment": payload.review_comment,
        }
    )
    record.processing_history = history

    await db.commit()
    await db.refresh(record)
    return record
