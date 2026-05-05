# KR 유튜브 트렌드 대시보드 (Local)

PRD v1.0 기준의 **로컬 개발용** 구현입니다.

## 구성
- `frontend/`: 확정 UI(4-Zone) + 로컬 API 연동
- `backend/`: FastAPI + YouTube Data API v3 + SQLite 스냅샷/집계
- `data/`: 로컬 SQLite(`snapshots.db`)

## 사전 준비
- Python 3.11+ (현재 환경: 3.13 OK)
- YouTube Data API v3 키 발급 후 `.env`에 설정

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`의 `YOUTUBE_API_KEY`를 채웁니다.

## 실행

### 1) 백엔드 실행

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### 2) 프론트 실행

가장 간단한 방법은 VS Code의 Live Server로 `frontend/index.html`을 여는 것입니다.

또는 Python 내장 서버:

```bash
python3 -m http.server 5173 --directory frontend
```

그 후 브라우저에서 `http://localhost:5173` 접속.

## 데이터 갱신(스냅샷)

프론트 상단의 **“스냅샷 갱신”** 버튼이 아래 API를 호출합니다.

- `POST /api/snapshot/run`
  - 트렌딩(카테고리 10개 × TOP10) 저장
  - 채널 스냅샷 저장 (`backend/config/channels.json` 기반)

## 채널 ID 설정

`backend/config/channels.json`에 추적할 채널 ID를 넣습니다.

형식:

```json
[
  { "id": "UCxxxxxxxxxxxxxxxxxxxxxx", "name": "채널명(옵션)" }
]
```

## 기간(일/주/월) 동작 방식

YouTube `videos.list(chart=mostPopular)`는 “주간/월간” 필터를 제공하지 않습니다.
그래서 이 프로젝트는 **스냅샷을 저장**하고, **주간/월간은 스냅샷 집계로 생성**합니다.

