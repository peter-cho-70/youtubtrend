from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException

from backend.aggregate import list_channel_growth_top10
from backend.db import init_db

app = FastAPI()


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/")
def growth(period: Literal["daily", "weekly", "monthly"] = "daily"):
    try:
        items = list_channel_growth_top10(period=period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"generatedAt": date.today().isoformat(), "period": period, "items": items}

