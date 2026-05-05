"""
Vercel FastAPI entrypoint.

We serve the dashboard static files from ./public and keep backend API under /api/*.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.responses import FileResponse

from backend.main import app

_ROOT = Path(__file__).resolve().parents[1]
_PUBLIC = _ROOT / "public"


@app.get("/")
def _index():
    return FileResponse(_PUBLIC / "index.html")


@app.get("/app.js")
def _app_js():
    return FileResponse(_PUBLIC / "app.js")


@app.get("/style.css")
def _style_css():
    return FileResponse(_PUBLIC / "style.css")

