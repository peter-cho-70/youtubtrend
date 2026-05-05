from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException

from backend.aggregate import aggregate_trending
from backend.db import init_db

app = FastAPI()


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/")
def trending(cat: str = "all", period: Literal["daily", "weekly", "monthly"] = "daily"):
    try:
        items = aggregate_trending(category=cat, period=period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"generatedAt": date.today().isoformat(), "cat": cat, "period": period, "items": items}

