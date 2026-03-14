from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import ContentResponse, MessageResponse
from app.services.processor import reprocess_all_unprocessed, reprocess_single

router = APIRouter(prefix="/api/v1/content/reprocess", tags=["Reprocess"])


@router.post("/{content_id}", response_model=ContentResponse)
async def reprocess_content(
    content_id: str, db: AsyncSession = Depends(get_db)
):
    """Re-analyze a single content item with Groq."""
    try:
        record = await reprocess_single(content_id, db)
        return record
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", response_model=MessageResponse)
async def reprocess_all(background_tasks: BackgroundTasks):
    """Trigger background re-analysis of all unprocessed content."""
    background_tasks.add_task(reprocess_all_unprocessed)
    return MessageResponse(
        message="Bulk reprocessing started",
        detail="All unprocessed content items will be re-analyzed in the background",
    )
