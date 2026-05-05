from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


CATEGORY_MAP: dict[str, str] = {
    "all": "",
    "music": "10",
    "game": "20",
    "ent": "24",
    "news": "25",
    "edu": "27",
    "beauty": "26",
    "food": "22",  # People & Blogs (PRD v1.0의 먹방 카테고리 기준)
    "travel": "19",
    "it": "28",
}

YOUTUBE_CATEGORY_ID_TO_PRD: dict[str, str] = {
    "10": "music",
    "20": "game",
    "24": "ent",
    "25": "news",
    "27": "edu",
    "28": "it",
    "19": "travel",
    "26": "beauty",
    "22": "food",
}


@dataclass(frozen=True)
class VideoItem:
    video_id: str
    yt_category_id: str
    title: str
    channel_title: str
    view_count: int
    thumbnail_url: str
    published_at: str


@dataclass(frozen=True)
class ChannelItem:
    channel_id: str
    title: str
    subscriber_count: int
    view_count: int
    thumbnail_url: str


def _get_api_key() -> str | None:
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        return None
    # .env.example 기본값을 그대로 둔 상태면 "없음"으로 취급
    if key.strip() in {"your_youtube_api_key_here", "YOUR_YOUTUBE_API_KEY"}:
        return None
    return key


def _youtube():
    key = _get_api_key()
    if not key:
        raise RuntimeError("Missing YOUTUBE_API_KEY")
    return build("youtube", "v3", developerKey=key)


def fetch_most_popular_videos(max_results: int = 50) -> list[VideoItem]:
    """
    chart=mostPopular은 기간(일/주/월) 필터를 제공하지 않으므로
    'daily/weekly/monthly'는 스냅샷 집계로 해결한다.
    """
    yt = _youtube()
    # videos.list maxResults 최대는 50이므로, 50을 초과하면 pageToken으로 여러 번 호출한다.
    if max_results < 1:
        return []

    want = max_results
    page_token: str | None = None
    collected: list[dict[str, Any]] = []

    while len(collected) < want:
        batch = min(50, want - len(collected))
        params: dict[str, Any] = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": "KR",
            "maxResults": batch,
        }
        if page_token:
            params["pageToken"] = page_token

        res = yt.videos().list(**params).execute()
        collected.extend(res.get("items", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break

    items: list[VideoItem] = []
    for v in collected:
        snippet = v.get("snippet") or {}
        stats = v.get("statistics") or {}
        thumbs = (snippet.get("thumbnails") or {}).get("medium") or (snippet.get("thumbnails") or {}).get("default") or {}
        items.append(
            VideoItem(
                video_id=v["id"],
                yt_category_id=str(snippet.get("categoryId") or ""),
                title=snippet.get("title", ""),
                channel_title=snippet.get("channelTitle", ""),
                view_count=int(stats.get("viewCount") or 0),
                thumbnail_url=thumbs.get("url") or f"https://i.ytimg.com/vi/{v['id']}/mqdefault.jpg",
                published_at=snippet.get("publishedAt", ""),
            )
        )
    return items


def _chunks(xs: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(xs), size):
        yield xs[i : i + size]


def fetch_channels_batch(channel_ids: list[str]) -> list[ChannelItem]:
    yt = _youtube()
    out: list[ChannelItem] = []

    # channels.list cost is 1 unit per request; batch 50 IDs per request.
    for part_ids in _chunks(channel_ids, 50):
        res = (
            yt.channels()
            .list(part="snippet,statistics", id=",".join(part_ids), maxResults=50)
            .execute()
        )
        for c in res.get("items", []):
            snippet = c.get("snippet") or {}
            stats = c.get("statistics") or {}
            thumbs = (snippet.get("thumbnails") or {}).get("default") or {}
            out.append(
                ChannelItem(
                    channel_id=c["id"],
                    title=snippet.get("title", ""),
                    subscriber_count=int(stats.get("subscriberCount") or 0),
                    view_count=int(stats.get("viewCount") or 0),
                    thumbnail_url=thumbs.get("url") or "",
                )
            )
    return out

