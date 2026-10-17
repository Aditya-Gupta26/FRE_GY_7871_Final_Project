"""Real-time Tier C vintages for the out-of-sample nowcasts (a fix after the final
scrutiny found that the Tier C classifier in 09 is trained on Opus codes from every month, including
months after a nowcast's origin). For each origin month t (2017-01 to 2026-10, COVID window skipped), the
relevance, tone and inflation-direction classifiers are re-trained on coded items dated before day 15 of t
only, every economic headline in survey months up to t is re-scored, and the monthly measures are rebuilt
(equal outlet-group weights, as in 09). The nowcast for t then uses vintage t of the whole series.
    python scripts/09b_tierc_realtime.py
Writes data/processed/tierC_realtime.parquet (origin, survey_month, TC_NEGNET, TC_INFL_BAL, n_train).
"""
import _bootstrap  # noqa: F401
import time

import numpy as np
import pandas as pd

from src.baselines import train
from src.coded import as_list
from src.config import END, CODED, INTERIM, OUTLET_GROUPS, PROCESSED

C = pd.read_parquet(CODED / "codes.parquet")
K = pd.read_csv(CODED / "sample_key.csv", parse_dates=["date", "survey_month"])
X = C.merge(K, on="item_id")
N = pd.read_parquet(INTERIM / "news.parquet")
F = N[(N["pull"] != "release") & N["econ_term"] & N["group"].isin(OUTLET_GROUPS)][["doc_id", "survey_month", "group", "clean"]].copy()
corpus = pd.concat([N[["doc_id", "clean"]], pd.read_parquet(INTERIM / "reddit.parquet")[["doc_id", "clean"]]])
TR = X[X["tier"].isin(["B_news", "A_news2026", "B_reddit", "A_reddit2026", "A_release"])].merge(corpus, on="doc_id")
origins = [t for t in pd.date_range("2017-01-01", END, freq="MS")
           if not (pd.Timestamp("2020-03-01") <= t <= pd.Timestamp("2021-01-01"))]


def vintage(t: pd.Timestamp) -> pd.DataFrame:
    tr = TR[TR["date"] < t + pd.Timedelta(days=14)]          # coded items published before day 15 of t
    rel = tr[tr["relevant"] == "yes"]
    f = F[F["survey_month"] <= t].copy()
    f["rel"] = train(tr["clean"], tr["relevant"]).predict(f["clean"]) == "yes"
    f = f[f["rel"]]
    tone = train(rel["clean"], rel["tone"]).predict(f["clean"])
    f["NEGNET"] = (tone == "negative").astype(float) - (tone == "positive").astype(float)
    for tp in ["inflation_up", "inflation_down"]:
        yb = rel["topics"].map(lambda v, tp=tp: "yes" if tp in as_list(v) else "no")
        f[tp] = (train(rel["clean"], yb).predict(f["clean"]) == "yes").astype(float)
    g = f.groupby(["survey_month", "group"])
    neg = g["NEGNET"].mean().unstack().mean(axis=1)
    s = g[["inflation_up", "inflation_down"]].sum()
    bal = (s["inflation_up"] / (s["inflation_up"] + s["inflation_down"])).unstack().mean(axis=1)
    return pd.DataFrame({"TC_NEGNET": neg, "TC_INFL_BAL": bal}).assign(origin=t, n_train=len(tr))


out, t0 = [], time.time()
for t in origins:
    out.append(vintage(t))
    print(t.date(), int(out[-1]["n_train"].iloc[0]), f"{time.time() - t0:.0f}s", flush=True)
V = pd.concat(out).rename_axis("survey_month").reset_index()
V.to_parquet(PROCESSED / "tierC_realtime.parquet")
print("wrote tierC_realtime.parquet", V.shape)
