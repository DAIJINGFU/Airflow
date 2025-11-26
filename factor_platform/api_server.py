from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

from .factor_store import FactorStore

app = FastAPI(title="Factor Platform API", version="0.1.0")


def get_store() -> FactorStore:
    db_path = Path(os.environ.get("FACTOR_PLATFORM_DB", ""))
    if db_path:
        return FactorStore(db_path)
    return FactorStore()


class FactorRequest(BaseModel):
    code: str = Field(..., description="Unique factor code")
    expression: str = Field(..., description="Expression for the factor (QLib-like or Python)")
    name: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    note: Optional[str] = None


class JobRequest(BaseModel):
    factor_code: str
    start_date: str
    end_date: str
    freq: str = "day"
    instruments: List[str] = Field(default_factory=list)
    priority: int = 5
    owner: Optional[str] = None
    tags: Optional[List[str]] = None
    callback_url: Optional[str] = None
    context: Optional[Dict[str, str]] = None
    version: Optional[int] = None

    @validator("priority")
    def _priority_range(cls, value: int) -> int:
        if value < 1:
            return 1
        if value > 10:
            return 10
        return value


class DequeueRequest(BaseModel):
    limit: int = Field(default=8, ge=1, le=50)


class JobCompleteRequest(BaseModel):
    metrics: Dict[str, float]
    result_path: Optional[str] = None


class JobFailRequest(BaseModel):
    error_message: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/factors")
def list_factors() -> List[Dict[str, object]]:
    store = get_store()
    return store.list_factors()


@app.post("/factors")
def register_factor(payload: FactorRequest) -> Dict[str, object]:
    store = get_store()
    try:
        return store.register_factor(**payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/jobs")
def submit_job(payload: JobRequest) -> Dict[str, object]:
    store = get_store()
    try:
        return store.submit_job(**payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/jobs/dequeue")
def dequeue_jobs(payload: DequeueRequest) -> List[Dict[str, object]]:
    store = get_store()
    return store.dequeue_jobs(limit=payload.limit)


@app.post("/jobs/{job_id}/complete")
def job_complete(job_id: int, payload: JobCompleteRequest) -> Dict[str, str]:
    store = get_store()
    store.mark_job_succeeded(job_id, payload.metrics, payload.result_path)
    return {"status": "SUCCESS"}


@app.post("/jobs/{job_id}/fail")
def job_fail(job_id: int, payload: JobFailRequest) -> Dict[str, str]:
    store = get_store()
    store.mark_job_failed(job_id, payload.error_message)
    return {"status": "FAILED"}


@app.get("/jobs")
def list_jobs(status: Optional[str] = None, limit: int = 20) -> List[Dict[str, object]]:
    store = get_store()
    return store.list_jobs(status=status, limit=limit)
