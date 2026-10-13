"""Second news worker: the same pulls as 02_collect_news.py, outlets in reverse order (to finish sooner;
every window is cached, so the two workers never redo or corrupt each other's files)."""
import _bootstrap  # noqa: F401
from concurrent.futures import ThreadPoolExecutor

from src.config import OUTLETS
from src.news import _outlet_job

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as ex:
        print(sum(ex.map(_outlet_job, list(OUTLETS)[::-1])))
