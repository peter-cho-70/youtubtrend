from __future__ import annotations

import os
from datetime import date
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .aggregate import (
    aggregate_trending,
    list_channel_growth_top10,
    list_channel_top10,
)
from .db import init_db
from .snapshot_job import run_all
from .youtube_client import _get_api_key


load_dotenv()

app = FastAPI(title="KR YouTube Trends (Local)")
app.add_middleware(
    CORSMiddleware,
    # 로컬 프론트(정적 서버)에서 POST(프리플라이트 포함) 호출이 막히지 않도록
    # 출처를 구체적으로 허용한다.
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/api/health")
def health():
    return {"ok": True, "date": date.today().isoformat(), "has_api_key": bool(_get_api_key())}


@app.post("/api/snapshot/run")
def snapshot_run():
    """
    로컬 개발용: 클릭/호출로 스냅샷을 저장한다.
    - trending: 10카테고리×10개
    - channels: config/channels.json의 채널들(배치 50개)
    """
    try:
        return run_all()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/trending")
def trending(
    cat: str = "all",
    period: Literal["daily", "weekly", "monthly"] = "daily",
):
    try:
        items = aggregate_trending(category=cat, period=period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"generatedAt": date.today().isoformat(), "cat": cat, "period": period, "items": items}


@app.get("/api/channels")
def channels(sort: Literal["subs", "views"] = "subs"):
    items = list_channel_top10(snapshot_date=date.today().isoformat(), sort_by=sort)
    return {"generatedAt": date.today().isoformat(), "sort": sort, "items": items}


@app.get("/api/growth")
def growth(period: Literal["daily", "weekly", "monthly"] = "daily"):
    try:
        items = list_channel_growth_top10(period=period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"generatedAt": date.today().isoformat(), "period": period, "items": items}

