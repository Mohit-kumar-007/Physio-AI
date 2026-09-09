"""Sliding-window rate limiting for the endpoints worth brute-forcing.

Deliberately in-memory and dependency-free. The counter lives in one process,
so with N uvicorn workers the effective limit is N x the configured value --
fine for a single-instance deployment, and the point at which you outgrow that
is the point you want Redis anyway.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

# Password guessing is the threat. Legitimate users mistype a few times;
# nobody makes 10 attempts a minute from one address on purpose.
LOGIN_ATTEMPTS, LOGIN_WINDOW = 10, 60
SIGNUP_ATTEMPTS, SIGNUP_WINDOW = 5, 300

# Stop the key table growing without bound when addresses churn.
PRUNE_EVERY = 500


class SlidingWindow:
    """Counts hits per key over a moving time window."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._since_prune = 0

    def _drop_expired(self, key: str, now: float) -> deque[float]:
        hits = self._hits[key]
        cutoff = now - self.window
        while hits and hits[0] <= cutoff:
            hits.popleft()
        return hits

    def check(self, key: str) -> float | None:
        """Record a hit. Returns seconds to wait if the caller is over budget."""
        now = time.monotonic()
        hits = self._drop_expired(key, now)

        if len(hits) >= self.limit:
            return max(0.0, self.window - (now - hits[0]))

        hits.append(now)
        self._prune(now)
        return None

    def _prune(self, now: float) -> None:
        self._since_prune += 1
        if self._since_prune < PRUNE_EVERY:
            return
        self._since_prune = 0
        cutoff = now - self.window
        for key in [k for k, v in self._hits.items() if not v or v[-1] <= cutoff]:
            del self._hits[key]

    def reset(self) -> None:
        self._hits.clear()
        self._since_prune = 0


def client_ip(request: Request) -> str:
    """The caller's address, as seen through the reverse proxy.

    Uvicorn rewrites request.client from X-Forwarded-For only for hosts listed
    in --forwarded-allow-ips, so a client cannot spoof this by sending the
    header itself.
    """
    return request.client.host if request.client else "unknown"


def limiter(window: SlidingWindow, what: str):
    """Build a FastAPI dependency that guards an endpoint with `window`."""

    def dependency(request: Request) -> None:
        retry_after = window.check(client_ip(request))
        if retry_after is None:
            return
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many {what} attempts. Try again in "
                   f"{int(retry_after) + 1} seconds.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    return dependency


login_window = SlidingWindow(LOGIN_ATTEMPTS, LOGIN_WINDOW)
signup_window = SlidingWindow(SIGNUP_ATTEMPTS, SIGNUP_WINDOW)

login_limit = limiter(login_window, "login")
signup_limit = limiter(signup_window, "signup")
