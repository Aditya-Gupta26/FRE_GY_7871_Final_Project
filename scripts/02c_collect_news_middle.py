"""Third news worker: the same pulls, starting mid-list (cache-safe, like 02b)."""
import _bootstrap  # noqa: F401
from concurrent.futures import ThreadPoolExecutor

from src.config import OUTLETS
from src.news import _outlet_job

if __name__ == "__main__":
    o = list(OUTLETS)
    order = o[17:] + o[:17]
    with ThreadPoolExecutor(max_workers=2) as ex:
        print(sum(ex.map(_outlet_job, order)))
