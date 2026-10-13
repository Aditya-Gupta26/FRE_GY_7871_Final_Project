"""News headlines through Google News RSS (free). Adapted from A4/A5.

Three pulls, all with one stable economic query (config.NEWS_QUERY):
- history: per outlet (`site:`) and calendar month, Dec 2009 to Dec 2025
- weekly: per outlet and week (Mondays), Dec 29, 2025 to the Oct 12, 2026 cutoff
- release days: US-wide (no site filter) on [D, D+2) for every jobs and CPI release date D
A feed returns at most 100 items (relevance-ranked), so a capped window is a sample, not
a census; in date-bounded feeds most items carry 07:00 GMT, i.e. a date and not a time.
Every window is cached to its own file; None (failed call) is retried on the next run.
"""
from __future__ import annotations

import json
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import feedparser
import pandas as pd
import requests

from src.config import (DATA_CUTOFF, GOOGLE_NEWS_RSS, NEWS_HISTORY_START, NEWS_QUERY,
                        NEWS_WEEKLY_START, OUTLETS, PROCESSED, RAW, RELEASE_QUERIES, RSS_SLEEP_S)

OUT = RAW / "news"
UA = {"User-Agent": "Mozilla/5.0 (academic research; NYU FRE-GY 7871 course project)"}


def rss_get(q: str) -> list[dict] | None:
    url = f"{GOOGLE_NEWS_RSS}?q={urllib.parse.quote(q)}&hl=en-US&gl=US&ceid=US:en"
    for attempt in range(6):
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code == 200:
                feed = feedparser.parse(r.content)
                return [{"title": e.get("title"), "link": e.get("link"),
                         "published": e.get("published"),
                         "source": (e.get("source") or {}).get("title"),
                         "source_href": (e.get("source") or {}).get("href")} for e in feed.entries]
            if r.status_code in (429, 503):
                time.sleep(30 * (attempt + 1))
                continue
        except requests.RequestException:
            pass
        time.sleep(5 * (attempt + 1))
    return None


def _months() -> list[tuple[date, date]]:
    out, m = [], NEWS_HISTORY_START
    while m < date(2026, 1, 1):
        nxt = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        out.append((m, nxt))
        m = nxt
    return out


def _weeks() -> list[tuple[date, date]]:
    out, w = [], NEWS_WEEKLY_START
    while w < DATA_CUTOFF:
        out.append((w, min(w + timedelta(days=7), DATA_CUTOFF)))
        w += timedelta(days=7)
    return out


def _pull(kind: str, key: str, q: str, a: date, b: date, meta: dict) -> int:
    d = OUT / kind
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{key}_{a:%Y%m%d}.json"
    if path.exists():
        return len(json.loads(path.read_text())["items"])
    items = rss_get(f"{q} after:{a:%Y-%m-%d} before:{b:%Y-%m-%d}")
    time.sleep(RSS_SLEEP_S)
    if items is None:
        print("failed", kind, key, a, flush=True)
        return 0
    path.write_text(json.dumps({**meta, "since": a.isoformat(), "until": b.isoformat(), "query": q,
                                "retrieved_at": datetime.now(timezone.utc).isoformat(), "items": items}))
    return len(items)


def _outlet_job(site: str) -> int:
    q = f"{NEWS_QUERY} site:{site}"
    n = 0
    for a, b in _months():
        n += _pull("history", site, q, a, b, {"site": site})
    for a, b in _weeks():
        n += _pull("weekly", site, q, a, b, {"site": site})
    print("news", site, n, flush=True)
    return n


def collect_outlets(workers: int = 2) -> int:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return sum(ex.map(_outlet_job, list(OUTLETS)))


def collect_release_days() -> int:
    """Needs data/processed/release_calendar.csv (built by scripts/01_get_econ.py)."""
    cal = pd.read_csv(PROCESSED / "release_calendar.csv", parse_dates=["release_date"])
    n = 0
    for kind, series in (("jobs", "UNRATE"), ("cpi", "CPIAUCSL")):
        dates = sorted(set(cal.loc[cal.series == series, "release_date"].dt.date))
        for d in dates:
            if d < date(2010, 1, 1) or d >= DATA_CUTOFF:
                continue
            n += _pull("release", kind, RELEASE_QUERIES[kind], d, d + timedelta(days=2),
                       {"release": kind, "release_date": d.isoformat()})
    print("release-day items", n, flush=True)
    return n


def load_raw() -> pd.DataFrame:
    rows = []
    for kind in ("history", "weekly", "release"):
        for f in sorted((OUT / kind).glob("*.json")):
            j = json.loads(f.read_text())
            for it in j["items"]:
                rows.append({"pull": kind, "query_site": j.get("site"), "release": j.get("release"),
                             "release_date": j.get("release_date"), "win_since": j["since"],
                             "win_until": j["until"], "n_in_window": len(j["items"]), **it})
    return pd.DataFrame(rows)
