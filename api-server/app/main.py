from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db import async_session_maker, init_db
from app.routers.problems import router as problems_router
from app.routers.submissions import router as submissions_router
from app.services.problem_loader import seed_problems


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings = get_settings()
    async with async_session_maker() as session:
        await seed_problems(session, settings.problems_dir)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(problems_router)
app.include_router(submissions_router)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
