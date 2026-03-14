from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CategoryConfig
from app.schemas import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])

SEED_CATEGORIES = [
    ("age_category", "12-18", "Content targeting minors aged 12-18"),
    ("age_category", "18+", "Content targeting adults 18 and above"),
    ("content_type", "safe", "Content deemed safe and non-harmful"),
    ("content_type", "harmful", "Content identified as harmful"),
    ("harmful_subcategory", "female_abuse", "Content involving abuse of women/girls"),
    (
        "harmful_subcategory",
        "female_sexual_content",
        "Sexualized content targeting women/girls",
    ),
]


async def seed_categories(db: AsyncSession):
    """Insert default categories if the table is empty."""
    result = await db.execute(select(CategoryConfig).limit(1))
    if result.scalar_one_or_none() is not None:
        return

    for group, value, description in SEED_CATEGORIES:
        db.add(
            CategoryConfig(
                category_group=group,
                category_value=value,
                description=description,
                is_active=True,
            )
        )
    await db.commit()


@router.get("", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all configurable categories."""
    result = await db.execute(
        select(CategoryConfig).order_by(
            CategoryConfig.category_group, CategoryConfig.id
        )
    )
    return result.scalars().all()


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    payload: CategoryCreate, db: AsyncSession = Depends(get_db)
):
    """Add a new category value."""
    record = CategoryConfig(**payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update or deactivate an existing category."""
    result = await db.execute(
        select(CategoryConfig).where(CategoryConfig.id == category_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int, db: AsyncSession = Depends(get_db)
):
    """Remove a category."""
    result = await db.execute(
        select(CategoryConfig).where(CategoryConfig.id == category_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Category not found")

    await db.delete(record)
    await db.commit()
