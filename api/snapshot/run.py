from __future__ import annotations

from fastapi import FastAPI, HTTPException

from backend.db import init_db
from backend.snapshot_job import run_all

app = FastAPI()


@app.on_event("startup")
def _startup():
    init_db()


@app.post("/")
def snapshot_run():
    try:
        return run_all()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

