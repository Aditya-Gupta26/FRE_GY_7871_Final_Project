"""Reddit posts through the Arctic Shift archive (free, no auth). Adapted from A4/A5.

Design (time-stratified, so no window clusters at midnight or at the start of a month):
- history (Dec 2009 to Dec 2025): per sub and month, REDDIT_WINDOWS_PER_MONTH six-hour windows;
  window k starts at a seeded random time inside the k-th equal slice of the month; up to
  REDDIT_PER_WINDOW posts each (ascending, i.e. the first posts after that start time).
- monitoring (from REDDIT_DAILY_FROM): 4 six-hour windows a day (00, 06, 12, 18 UTC), 25 posts each.
Every window is cached to its own file, so an interrupted run resumes. Authors are replaced
by a SHA-256 hash at ingest (privacy); usernames are never written to disk.
"""
from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import numpy as np
import requests

from src.config import (DATA_CUTOFF, NEWS_HISTORY_START, POST_FIELDS, RANDOM_SEED, RAW,
                        REDDIT_API, REDDIT_DAILY_FROM, REDDIT_DAILY_PER_WINDOW,
                        REDDIT_DAILY_WINDOWS, REDDIT_PER_WINDOW, REDDIT_SUBS,
                        REDDIT_WINDOW_HOURS, REDDIT_WINDOWS_PER_MONTH)

OUT = RAW / "reddit"
UTC = timezone.utc


def _get(params: dict, retries: int = 8) -> list[dict]:
    for attempt in range(retries):
        try:
            r = requests.get(f"{REDDIT_API}/posts/search", params=params, timeout=90)
            if r.status_code == 200:
                js = json.loads(r.text, strict=False)   # some old posts carry raw control chars
                if js.get("error"):
                    raise RuntimeError(js["error"])
                return js.get("data") or []
            if r.status_code == 429:
                reset = float(r.headers.get("X-RateLimit-Reset", 2 ** attempt))
                time.sleep(min(max(reset, 1), 60))
                continue
            if r.status_code >= 500 or "Timeout" in r.text:
                time.sleep(3 * 2 ** min(attempt, 4))
                continue
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        except (requests.RequestException, RuntimeError, json.JSONDecodeError) as e:
            if isinstance(e, RuntimeError) and "Timeout" not in str(e) and "slow down" not in str(e):
                raise
            time.sleep(3 * 2 ** min(attempt, 4))
    raise RuntimeError(f"gave up on {params}")


def _hash_author(a: str | None) -> str | None:
    if a is None or a in ("[deleted]", "[removed]"):
        return a
    return hashlib.sha256(("fre7871:" + a).encode()).hexdigest()[:16]


def _windows(sub: str) -> list[tuple[datetime, datetime, int]]:
    """(start, end, limit) for every window, deterministic given the seed."""
    wins = []
    m = date(NEWS_HISTORY_START.year, NEWS_HISTORY_START.month, 1)
    rng_base = int(hashlib.md5(sub.encode()).hexdigest()[:8], 16)
    while m < REDDIT_DAILY_FROM:
        nxt = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        t0 = datetime(m.year, m.month, m.day, tzinfo=UTC)
        span = (datetime(nxt.year, nxt.month, 1, tzinfo=UTC) - t0).total_seconds()
        rng = np.random.default_rng([RANDOM_SEED, rng_base, m.year, m.month])
        k = REDDIT_WINDOWS_PER_MONTH
        for i in range(k):
            lo = span * i / k
            hi = span * (i + 1) / k - REDDIT_WINDOW_HOURS * 3600
            s = t0 + timedelta(seconds=float(rng.uniform(lo, max(lo, hi))))
            s = s.replace(microsecond=0)
            wins.append((s, s + timedelta(hours=REDDIT_WINDOW_HOURS), REDDIT_PER_WINDOW))
        m = nxt
    d = datetime(REDDIT_DAILY_FROM.year, REDDIT_DAILY_FROM.month, REDDIT_DAILY_FROM.day, tzinfo=UTC)
    end = datetime(DATA_CUTOFF.year, DATA_CUTOFF.month, DATA_CUTOFF.day, tzinfo=UTC)
    step = 24 // REDDIT_DAILY_WINDOWS
    while d < end:
        for h in range(0, 24, step):
            s = d + timedelta(hours=h)
            wins.append((s, s + timedelta(hours=REDDIT_WINDOW_HOURS), REDDIT_DAILY_PER_WINDOW))
        d += timedelta(days=1)
    return wins


def pull_sub(sub: str) -> int:
    cache = OUT / "windows" / sub
    cache.mkdir(parents=True, exist_ok=True)
    n = 0
    for s, u, lim in _windows(sub):
        f = cache / f"{int(s.timestamp())}_{int(u.timestamp())}.json"
        if f.exists():
            n += len(json.loads(f.read_text())["data"])
            continue
        page = _get({"subreddit": sub, "after": int(s.timestamp()), "before": int(u.timestamp()),
                     "limit": lim, "sort": "asc", "fields": POST_FIELDS})
        for p in page:
            p["author"] = _hash_author(p.get("author"))
            p["selftext"] = (p.get("selftext") or "")[:1000]
        f.write_text(json.dumps({"sub": sub, "start": s.isoformat(), "end": u.isoformat(),
                                 "limit": lim, "data": page}))
        n += len(page)
        time.sleep(0.4)
    print("reddit", sub, n, flush=True)
    return n


def collect_all(workers: int = 3) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return dict(zip(REDDIT_SUBS, ex.map(pull_sub, REDDIT_SUBS)))


def load_raw() -> list[dict]:
    rows = []
    for sub in REDDIT_SUBS:
        for f in sorted((OUT / "windows" / sub).glob("*.json")):
            j = json.loads(f.read_text())
            for p in j["data"]:
                p["window_start"], p["window_limit"] = j["start"], j["limit"]
                rows.append(p)
    return rows
