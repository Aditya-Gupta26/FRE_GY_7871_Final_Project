"""Second Reddit worker: the same windows as 03_collect_reddit.py, newest first (every window is its
own cache file, so the two workers never redo or corrupt each other's work)."""
import _bootstrap  # noqa: F401
import json
import time
from concurrent.futures import ThreadPoolExecutor

from src.config import POST_FIELDS, REDDIT_SUBS
from src.reddit import OUT, _get, _hash_author, _windows


def rev(sub: str) -> int:
    cache = OUT / "windows" / sub
    cache.mkdir(parents=True, exist_ok=True)
    n = 0
    for s, u, lim in _windows(sub)[::-1]:
        f = cache / f"{int(s.timestamp())}_{int(u.timestamp())}.json"
        if f.exists():
            continue
        page = _get({"subreddit": sub, "after": int(s.timestamp()), "before": int(u.timestamp()),
                     "limit": lim, "sort": "asc", "fields": POST_FIELDS})
        for p in page:
            p["author"] = _hash_author(p.get("author"))
            p["selftext"] = (p.get("selftext") or "")[:1000]
        f.write_text(json.dumps({"sub": sub, "start": s.isoformat(), "end": u.isoformat(), "limit": lim, "data": page}))
        n += 1
        time.sleep(0.4)
    return n


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as ex:
        print(dict(zip(REDDIT_SUBS, ex.map(rev, REDDIT_SUBS))))
