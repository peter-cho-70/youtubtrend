from __future__ import annotations

from datetime import date

from fastapi import FastAPI

from backend.db import init_db
from backend.youtube_client import _get_api_key

app = FastAPI()


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/")
def health():
    return {"ok": True, "date": date.today().isoformat(), "has_api_key": bool(_get_api_key())}

