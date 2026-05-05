from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def get_db_path() -> str:
    return os.getenv("APP_DB_PATH", "./data/snapshots.db")


def ensure_parent_dir(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def db_conn():
    db_path = get_db_path()
    ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with db_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trending_snapshots (
              snapshot_date TEXT NOT NULL,
              category TEXT NOT NULL,
              rank INTEGER NOT NULL,
              video_id TEXT NOT NULL,
              yt_category_id TEXT NOT NULL,
              title TEXT NOT NULL,
              channel_title TEXT NOT NULL,
              view_count INTEGER NOT NULL,
              thumbnail_url TEXT NOT NULL,
              published_at TEXT NOT NULL,
              PRIMARY KEY (snapshot_date, category, rank)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS channel_snapshots (
              snapshot_date TEXT NOT NULL,
              channel_id TEXT NOT NULL,
              title TEXT NOT NULL,
              subscriber_count INTEGER NOT NULL,
              view_count INTEGER NOT NULL,
              thumbnail_url TEXT NOT NULL,
              PRIMARY KEY (snapshot_date, channel_id)
            )
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_trending_video ON trending_snapshots (video_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_channel_date ON channel_snapshots (snapshot_date)"
        )
        conn.commit()

        # migrate: add yt_category_id if older db exists
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(trending_snapshots)").fetchall()]
        if "yt_category_id" not in cols:
            conn.execute("ALTER TABLE trending_snapshots ADD COLUMN yt_category_id TEXT NOT NULL DEFAULT ''")
            conn.commit()
