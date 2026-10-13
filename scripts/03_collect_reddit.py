"""Collect Reddit posts (r/Economics, r/economy, r/personalfinance) through Arctic Shift.
Time-stratified windows (see src/reddit.py); resumable. Run: python scripts/03_collect_reddit.py"""
import _bootstrap  # noqa: F401

from src.reddit import collect_all

if __name__ == "__main__":
    print(collect_all())
