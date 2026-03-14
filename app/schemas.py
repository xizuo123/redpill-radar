from datetime import datetime

from pydantic import BaseModel, Field


# ── Content ──────────────────────────────────────────────────────────────────


class ContentCreate(BaseModel):
    twitter_id: str = Field(..., min_length=1, description="Unique Twitter/X post ID")
    content_text: str = Field(..., min_length=1, description="Raw tweet text")


class ContentStatusUpdate(BaseModel):
    is_processed: bool
    review_comment: str | None = Field(
        None, description="Optional reviewer comment when processing"
    )


class ProcessingHistoryEntry(BaseModel):
    timestamp: str
    action: str
    old_value: bool | None = None
    new_value: bool | None = None
    comment: str | None = None


class AnalysisResult(BaseModel):
    age_category: str | None = None
    content_type: str | None = None
    harmful_subcategories: list[str] = []
    confidence: float = 0.0
    reasoning: str = ""


class ContentResponse(BaseModel):
    id: str
    twitter_id: str
    content_text: str
    age_category: str | None = None
    content_type: str | None = None
    harmful_subcategories: list[str] | None = None
    labels: dict | None = None
    raw_analysis: dict | None = None
    is_processed: bool
    review_comment: str | None = None
    processing_history: list[dict] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ContentListResponse(BaseModel):
    items: list[ContentResponse]
    total: int
    page: int
    limit: int


# ── Categories ───────────────────────────────────────────────────────────────


class CategoryCreate(BaseModel):
    category_group: str = Field(
        ..., description="e.g. age_category, content_type, harmful_subcategory"
    )
    category_value: str = Field(..., description="e.g. 12-18, female_abuse")
    description: str | None = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    category_group: str | None = None
    category_value: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: int
    category_group: str
    category_value: str
    description: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Generic ──────────────────────────────────────────────────────────────────


class MessageResponse(BaseModel):
    message: str
    detail: str | None = None
