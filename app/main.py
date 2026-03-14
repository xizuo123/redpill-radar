import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import async_session, init_db
from app.routers import categories, content, reprocess
from app.routers.categories import seed_categories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing database")
    await init_db()
    async with async_session() as db:
        await seed_categories(db)
    logger.info("Database ready with seed categories")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="RedPill Radar",
    description=(
        "Content analysis & moderation API for detecting harmful/hateful "
        "content targeting women on social media."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers — reprocess must come before content so that
# /api/v1/content/reprocess is matched before /api/v1/content/{content_id}
app.include_router(reprocess.router)
app.include_router(content.router)
app.include_router(categories.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
