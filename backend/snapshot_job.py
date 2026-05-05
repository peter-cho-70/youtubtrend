from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .db import db_conn, init_db
from .youtube_client import CATEGORY_MAP, YOUTUBE_CATEGORY_ID_TO_PRD, fetch_channels_batch, fetch_most_popular_videos


def _load_channel_ids() -> list[str]:
    path = Path(__file__).parent / "config" / "channels.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [x["id"] for x in data if isinstance(x, dict) and x.get("id")]


def save_trending_snapshot(snapshot_date: str | None = None) -> dict:
    init_db()
    snap = snapshot_date or date.today().isoformat()

    # 1회 호출로 전체 인기(최대 50개)를 받아서, YouTube의 snippet.categoryId 기반으로 PRD 카테고리로 분류한다.
    items = fetch_most_popular_videos(max_results=100)

    # group by PRD category
    buckets: dict[str, list] = {k: [] for k in CATEGORY_MAP.keys()}
    for v in items:
        prd_cat = YOUTUBE_CATEGORY_ID_TO_PRD.get(v.yt_category_id)
        if prd_cat:
            buckets[prd_cat].append(v)
        buckets["all"].append(v)

    inserted = 0
    with db_conn() as conn:
        for cat, vs in buckets.items():
            # 조회수 기준 정렬(“진짜 조회수”)
            limit = 100 if cat == "all" else 10
            top = sorted(vs, key=lambda x: x.view_count, reverse=True)[:limit]
            # 이전 실행에서 남아있는 행이 있으면(카테고리별 영상 수가 줄어든 경우) 정합성이 깨지므로
            # 해당 날짜+카테고리는 먼저 비운다.
            conn.execute(
                "DELETE FROM trending_snapshots WHERE snapshot_date = ? AND category = ?",
                (snap, cat),
            )
            for i, v in enumerate(top, start=1):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO trending_snapshots
                      (snapshot_date, category, rank, video_id, yt_category_id, title, channel_title, view_count, thumbnail_url, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snap,
                        cat,
                        i,
                        v.video_id,
                        v.yt_category_id,
                        v.title,
                        v.channel_title,
                        v.view_count,
                        v.thumbnail_url,
                        v.published_at,
                    ),
                )
                inserted += 1
        conn.commit()

    return {"snapshot_date": snap, "categories": len(buckets), "rows": inserted, "errors": []}


def save_channel_snapshot(snapshot_date: str | None = None) -> dict:
    init_db()
    snap = snapshot_date or date.today().isoformat()
    ids = _load_channel_ids()
    if not ids:
        return {"snapshot_date": snap, "rows": 0, "note": "No channel IDs configured (backend/config/channels.json)"}

    items = fetch_channels_batch(ids)
    with db_conn() as conn:
        for c in items:
            conn.execute(
                """
                INSERT OR REPLACE INTO channel_snapshots
                  (snapshot_date, channel_id, title, subscriber_count, view_count, thumbnail_url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snap,
                    c.channel_id,
                    c.title,
                    c.subscriber_count,
                    c.view_count,
                    c.thumbnail_url,
                ),
            )
        conn.commit()

    return {"snapshot_date": snap, "rows": len(items)}


def run_all(snapshot_date: str | None = None) -> dict:
    return {
        "trending": save_trending_snapshot(snapshot_date=snapshot_date),
        "channels": save_channel_snapshot(snapshot_date=snapshot_date),
    }

