from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI

from backend.aggregate import list_channel_top10
from backend.db import init_db

app = FastAPI()


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/")
def channels(sort: Literal["subs", "views"] = "subs"):
    items = list_channel_top10(snapshot_date=date.today().isoformat(), sort_by=sort)
    return {"generatedAt": date.today().isoformat(), "sort": sort, "items": items}

