"""Build the cleaned news and Reddit corpora, the filter waterfalls and the coverage tables.
    python scripts/05_build_corpus.py
Writes data/interim/{news,reddit}.parquet and outputs/tables/corpus_*.csv|json.
"""
import _bootstrap  # noqa: F401
import json

import pandas as pd

from src.config import INTERIM, OUTLETS, TABLES
from src import news
from src.corpus import build_news, build_reddit

INTERIM.mkdir(parents=True, exist_ok=True)
N, WN = build_news()
R, WR = build_reddit()
N.to_parquet(INTERIM / "news.parquet")
R.to_parquet(INTERIM / "reddit.parquet")
WN.to_csv(TABLES / "corpus_waterfall_news.csv", index=False)
WR.to_csv(TABLES / "corpus_waterfall_reddit.csv", index=False)

site = N[N["pull"] != "release"]
site_y = site.assign(year=site["date"].dt.year)
cov = site_y.pivot_table(index="outlet", columns="year", values="doc_id", aggfunc="count", fill_value=0)
cov.insert(0, "group", [OUTLETS[o][0] for o in cov.index])
cov.insert(1, "region", [OUTLETS[o][2] for o in cov.index])
cov.to_csv(TABLES / "corpus_outlet_year_counts.csv")
econ = site_y[site_y["econ_term"]].pivot_table(index="group", columns="year", values="doc_id", aggfunc="count", fill_value=0)
econ.to_csv(TABLES / "corpus_group_year_econ_counts.csv")
red = R.assign(year=R["date"].dt.year).pivot_table(index="sub", columns="year", values="doc_id", aggfunc="count", fill_value=0)
red.to_csv(TABLES / "corpus_reddit_sub_year_counts.csv")
score_by_year = R.assign(year=R["date"].dt.year).groupby("year")["score"].describe()[["count", "50%", "mean", "max"]]
score_by_year.to_csv(TABLES / "corpus_reddit_score_by_year.csv")

# share of site windows that hit Google's ~100-item cap (so the window is a relevance-ranked sample)
raw = news.load_raw()
wins = raw[raw["pull"] != "release"].drop_duplicates(["query_site", "win_since"])
wins = wins.assign(year=pd.to_datetime(wins["win_since"]).dt.year, capped=wins["n_in_window"] >= 100)
wins.groupby(["pull", "year"])["capped"].mean().unstack(0).to_csv(TABLES / "corpus_capped_share.csv")
summary = {
    "news_headlines": int(len(N)), "news_site_pulls": int(len(site)), "news_release_pulls": int((N["pull"] == "release").sum()),
    "news_econ_term_share": float(site["econ_term"].mean()), "news_syndicated_share": float(N["syndicated"].mean()),
    "news_opinion_share": float(N["opinion"].mean()),
    "site_windows": int(len(wins)), "site_windows_capped_share": float(wins["capped"].mean()),
    "news_by_group": site.groupby("group").size().to_dict(),
    "news_econ_by_group": site[site["econ_term"]].groupby("group").size().to_dict(),
    "reddit_posts": int(len(R)), "reddit_by_sub": R.groupby("sub").size().to_dict(),
    "reddit_by_kind": R.groupby("kind").size().to_dict(),
    "outlets_with_zero_items_2010": [o for o in cov.index if cov.loc[o].get(2010, 0) == 0],
    "first_date": str(N["date"].min().date()), "last_date": str(N["date"].max().date()),
}
(TABLES / "corpus_summary.json").write_text(json.dumps(summary, indent=1, default=str))
print(json.dumps(summary, indent=1, default=str))
print(WN.to_string()); print(WR.to_string())
