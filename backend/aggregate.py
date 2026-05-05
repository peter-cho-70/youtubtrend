from __future__ import annotations

from datetime import date, timedelta

from .db import db_conn


def _date_range(days: int) -> list[str]:
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(days)]


def list_trending_daily(category: str, snapshot_date: str) -> list[dict]:
    with db_conn() as conn:
        rows = conn.execute(
            """
            SELECT rank, video_id, title, channel_title, view_count, thumbnail_url, published_at
            FROM trending_snapshots
            WHERE snapshot_date = ? AND category = ?
            ORDER BY view_count DESC
            """,
            (snapshot_date, category),
        ).fetchall()
    out = [dict(r) for r in rows]
    # "진짜 조회수" 기준 정렬이므로, 저장 당시 rank 대신 정렬 결과에 맞춰 rank를 재부여한다.
    for i, item in enumerate(out, start=1):
        item["rank"] = i
    return out


def aggregate_trending(category: str, period: str) -> list[dict]:
    if period == "daily":
        return list_trending_daily(category=category, snapshot_date=date.today().isoformat())

    window = {"weekly": 7, "monthly": 30}.get(period)
    if not window:
        raise ValueError("period must be daily|weekly|monthly")

    dates = _date_range(window)
    placeholders = ",".join(["?"] * len(dates))

    # 주/월간은 스냅샷에 저장된 누적 viewCount를 날짜별로 합산(sum_views)해서 정렬한다.
    # (엄밀한 '기간 조회수 증가분'이 아니라, 해당 기간 동안 상위권에 있었던 영상의 조회수 합에 가깝다.)
    with db_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT
              video_id,
              MAX(title) AS title,
              MAX(channel_title) AS channel_title,
              MAX(thumbnail_url) AS thumbnail_url,
              MAX(published_at) AS published_at,
              SUM(view_count) AS sum_views
            FROM trending_snapshots
            WHERE category = ?
              AND snapshot_date IN ({placeholders})
            GROUP BY video_id
            ORDER BY sum_views DESC
            LIMIT 10
            """,
            (category, *dates),
        ).fetchall()

    out = []
    for r in rows:
        out.append(
            {
                "video_id": r["video_id"],
                "title": r["title"],
                "channel_title": r["channel_title"],
                "thumbnail_url": r["thumbnail_url"],
                "published_at": r["published_at"],
                "view_count": int(r["sum_views"]),  # 기간합 조회수
            }
        )
    for i, item in enumerate(out, start=1):
        item["rank"] = i
    return out


def list_channel_top10(snapshot_date: str, sort_by: str = "subs") -> list[dict]:
    order = "subscriber_count DESC" if sort_by == "subs" else "view_count DESC"
    with db_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT channel_id, title, subscriber_count, view_count, thumbnail_url
            FROM channel_snapshots
            WHERE snapshot_date = ?
            ORDER BY {order}
            LIMIT 10
            """,
            (snapshot_date,),
        ).fetchall()
    out = [dict(r) for r in rows]
    for i, item in enumerate(out, start=1):
        item["rank"] = i
    return out


def list_channel_growth_top10(period: str) -> list[dict]:
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(period)
    if not days:
        raise ValueError("period must be daily|weekly|monthly")

    today = date.today().isoformat()
    prev = (date.today() - timedelta(days=days)).isoformat()

    with db_conn() as conn:
        rows = conn.execute(
            """
            SELECT
              a.channel_id,
              a.title AS title,
              a.thumbnail_url AS thumbnail_url,
              (a.subscriber_count - b.subscriber_count) AS gain,
              CASE
                WHEN b.subscriber_count > 0 THEN ROUND((a.subscriber_count - b.subscriber_count) * 100.0 / b.subscriber_count, 2)
                ELSE NULL
              END AS rate
            FROM channel_snapshots a
            JOIN channel_snapshots b
              ON a.channel_id = b.channel_id
            WHERE a.snapshot_date = ?
              AND b.snapshot_date = ?
            ORDER BY gain DESC
            LIMIT 10
            """,
            (today, prev),
        ).fetchall()

        # sparkline: 최근 7일 subscribers
        spark_dates = _date_range(7)
        spark_placeholders = ",".join(["?"] * len(spark_dates))
        spark_rows = conn.execute(
            f"""
            SELECT snapshot_date, channel_id, subscriber_count
            FROM channel_snapshots
            WHERE snapshot_date IN ({spark_placeholders})
            """,
            (*spark_dates,),
        ).fetchall()

    spark_map: dict[str, dict[str, int]] = {}
    for r in spark_rows:
        spark_map.setdefault(r["channel_id"], {})[r["snapshot_date"]] = int(r["subscriber_count"])

    out = []
    for r in rows:
        cid = r["channel_id"]
        series = [spark_map.get(cid, {}).get(d, 0) for d in reversed(spark_dates)]
        out.append(
            {
                "channel_id": cid,
                "title": r["title"],
                "thumbnail_url": r["thumbnail_url"],
                "gain": int(r["gain"]),
                "rate": (float(r["rate"]) if r["rate"] is not None else None),
                "sparkline": series,
            }
        )
    for i, item in enumerate(out, start=1):
        item["rank"] = i
    return out

