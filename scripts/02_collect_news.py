"""Collect economic news headlines through Google News RSS.
    python scripts/02_collect_news.py outlets    # 34 outlets: monthly 2010-2025 + weekly 2026 (~3 h)
    python scripts/02_collect_news.py releases   # release-day pulls (needs 01_get_econ.py first)
Resumable: every window is cached."""
import _bootstrap  # noqa: F401
import sys

from src.news import collect_outlets, collect_release_days

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "outlets"
    print(collect_outlets() if what == "outlets" else collect_release_days())
