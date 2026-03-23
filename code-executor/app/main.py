from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.job_manager import ExecutionStore, LocalJobManager
from app.schemas import ExecutionRequest, ExecutionStatus


settings = get_settings()
store = ExecutionStore()
manager = LocalJobManager(settings, store)
app = FastAPI(title=settings.app_name)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/execute", response_model=ExecutionStatus)
async def execute(request: ExecutionRequest) -> ExecutionStatus:
    return await manager.dispatch(request)


@app.get("/execute/{submission_id}/status", response_model=ExecutionStatus)
async def get_status(submission_id: str) -> ExecutionStatus:
    payload = store.get(submission_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return ExecutionStatus(**payload)

