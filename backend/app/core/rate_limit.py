"""Per-client-IP rate limiting for routes that call paid/quota-limited external APIs.

POST /api/v1/explanations and POST /api/analysis/date require no auth and each call SOLAR/
Gemini/KIS on the backend's own credentials — without this, anyone who finds the deployed URL
could script repeated calls and run up API cost or exhaust KIS's per-minute quota (see
CLAUDE.md section 11 for a prior real incident with that quota). Same in-memory,
threading.Lock-guarded style as the caches in market_data_service.py/retrieval_service.py —
fine for this app's single-instance GCE deployment, not meant to survive a multi-instance setup.
"""

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request

WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 10

_lock = threading.Lock()
_hits: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def reset() -> None:
    """Test-only: clear all tracked hits so test cases don't bleed rate-limit state into
    each other (they all share TestClient's fixed client host)."""
    with _lock:
        _hits.clear()


def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency — raises 429 once a client IP exceeds MAX_REQUESTS_PER_WINDOW calls
    within WINDOW_SECONDS on whichever route depends on this."""
    key = _client_key(request)
    now = time.monotonic()

    with _lock:
        recent = [t for t in _hits[key] if now - t < WINDOW_SECONDS]
        if len(recent) >= MAX_REQUESTS_PER_WINDOW:
            retry_after = int(WINDOW_SECONDS - (now - recent[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
                headers={"Retry-After": str(retry_after)},
            )
        recent.append(now)
        _hits[key] = recent
