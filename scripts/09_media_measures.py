"""Media measures (monthly, survey-aligned; weekly for 2026): own Opus news and Reddit series, the
LM-dictionary and TF-IDF (Tier C) full-corpus series, the SF Fed index and news-based EPU; split-half
reliability and convergent validity.
    python scripts/09_media_measures.py
Writes data/processed/media_{monthly,weekly}.parquet, outputs/tables/media_*.csv, outputs/results_media.json.
"""
import _bootstrap  # noqa: F401
import json

import numpy as np
import pandas as pd

from src.baselines import train
from src.coded import as_list, TOPICS
from src.config import END, CODED, INTERIM, OUTLET_GROUPS, OUTPUTS, PROCESSED, TABLES
from src.dictionary import code as dict_code
from src.media import MEASURES, monthly_news, monthly_simple, sffed_monthly, split_half
from src.sources import epu_news

C = pd.read_parquet(CODED / "codes.parquet")
K = pd.read_csv(CODED / "sample_key.csv", parse_dates=["date", "survey_month"])
X = C.merge(K, on="item_id")
months = pd.date_range("2010-01-01", END, freq="MS")
R = {}

news = X[X["tier"].isin(["B_news", "A_news2026"]) & (X["relevant"] == "yes")].copy()
red = X[X["tier"].isin(["B_reddit", "A_reddit2026"]) & (X["relevant"] == "yes")].copy()
R["coded_counts"] = {"news_coded": int(X["tier"].isin(["B_news", "A_news2026"]).sum()), "news_relevant": int(len(news)),
                     "reddit_coded": int(X["tier"].isin(["B_reddit", "A_reddit2026"]).sum()), "reddit_relevant": int(len(red)),
                     "relevance_rate_news": float(len(news) / max(1, X["tier"].isin(["B_news", "A_news2026"]).sum())),
                     "relevance_rate_reddit": float(len(red) / max(1, X["tier"].isin(["B_reddit", "A_reddit2026"]).sum()))}

own = monthly_news(news).reindex(months)
own_red = monthly_simple(red).reindex(months)
# quarterly own-Opus series (PREREG kill switch + dated deviation of Oct 13, 02:46): survey months grouped by quarter
news["quarter"] = news["survey_month"].dt.to_period("Q").dt.start_time
ownq = monthly_news(news, key="quarter")
red["quarter"] = red["survey_month"].dt.to_period("Q").dt.start_time
redq = monthly_simple(red, key="quarter")
ownq.to_parquet(PROCESSED / "media_quarterly_own.parquet")
redq.to_parquet(PROCESSED / "media_quarterly_reddit.parquet")
cov_m = own["covered"].fillna(False).astype(bool)
R["coverage"] = {"months_covered": int(cov_m.sum()), "months": len(months),
                 "months_covered_2026": int(cov_m.loc["2026-01-01":].sum()),
                 "median_items_per_month_history": float(own.loc[:"2025-12-01", "n_items"].median()),
                 "median_items_per_month_2026": float(own.loc["2026-01-01":, "n_items"].median()),
                 "quarters_covered": int(ownq["covered"].sum()), "quarters": int(len(ownq)),
                 "median_items_per_quarter": float(ownq["n_items"].median())}
R["split_half_news_NEGNET"] = split_half(news, "NEGNET")
R["split_half_news_SAL_prices_high"] = split_half(news, "SAL_prices_high")
R["split_half_reddit_NEGNET"] = split_half(red, "NEGNET")

# weekly 2026 (display only)
w = news[news["date"] >= "2025-12-29"].copy()
w["week"] = w["date"] - pd.to_timedelta(w["date"].dt.weekday, unit="D")
weekly = monthly_news(w, key="week")

# ---------------- dictionary and Tier C on the full corpus (economic-term headlines of the site pulls)
N = pd.read_parquet(INTERIM / "news.parquet")
F = N[(N["pull"] != "release") & N["econ_term"] & N["group"].isin(OUTLET_GROUPS)].copy()
D = dict_code(F["clean"])
F["dict_neg"] = (D["tone"] == "negative").astype(float)
F["dict_pos"] = (D["tone"] == "positive").astype(float)
F["dict_NEGNET"] = F["dict_neg"] - F["dict_pos"]
pd.read_parquet(INTERIM / "reddit.parquet")[["doc_id", "score", "num_comments", "sub"]].to_parquet(PROCESSED / "reddit_scores.parquet")
corpus = pd.concat([pd.read_parquet(INTERIM / "news.parquet")[["doc_id", "clean"]],
                    pd.read_parquet(INTERIM / "reddit.parquet")[["doc_id", "clean"]]])
tr = X[X["tier"].isin(["B_news", "A_news2026", "B_reddit", "A_reddit2026", "A_release"])].merge(corpus, on="doc_id")
m_rel = train(tr["clean"], tr["relevant"])
tr_rel = tr[tr["relevant"] == "yes"]
m_tone = train(tr_rel["clean"], tr_rel["tone"])
F["tc_relevant"] = m_rel.predict(F["clean"])
F["tc_tone"] = m_tone.predict(F["clean"])
F["tc_NEGNET"] = (F["tc_tone"] == "negative").astype(float) - (F["tc_tone"] == "positive").astype(float)
for tp in ["inflation_up", "inflation_down", "prices_high", "layoffs", "hiring"]:
    yb = tr_rel["topics"].map(lambda v, tp=tp: "yes" if tp in as_list(v) else "no")
    F[f"tc_{tp}"] = (train(tr_rel["clean"], yb).predict(F["clean"]) == "yes").astype(float)
F.loc[F["tc_relevant"] != "yes", [c for c in F.columns if c.startswith("tc_") and c not in ("tc_relevant", "tc_tone")]] = np.nan


def eq_group_month(df, col, mask=None):
    d = df if mask is None else df[mask]
    g = d.groupby(["survey_month", "group"])[col].mean().unstack()
    return g.mean(axis=1)


dict_m = eq_group_month(F, "dict_NEGNET").reindex(months).rename("DICT_NEGNET")
relF = F["tc_relevant"] == "yes"
tc_m = eq_group_month(F, "tc_NEGNET", relF).reindex(months).rename("TC_NEGNET")
tc_n = F[relF].groupby("survey_month").size().reindex(months).rename("TC_n")
up = F[relF].groupby(["survey_month", "group"])["tc_inflation_up"].sum().unstack()
dn = F[relF].groupby(["survey_month", "group"])["tc_inflation_down"].sum().unstack()
tc_bal = (up / (up + dn)).mean(axis=1).reindex(months).rename("TC_INFL_BAL")
tc_ph = eq_group_month(F, "tc_prices_high", relF).reindex(months).rename("TC_SAL_prices_high")
F[["doc_id", "survey_month", "group", "tc_relevant", "tc_tone", "tc_inflation_up", "tc_inflation_down",
   "tc_prices_high", "tc_layoffs", "tc_hiring", "dict_NEGNET"]].to_parquet(PROCESSED / "tierC_items.parquet")

sf = pd.read_parquet(PROCESSED / "sffed_daily.parquet")["sffed"]
SF = sffed_monthly(sf, months)
EPU = epu_news().shift(1).reindex(months).rename("EPU_news_lag1")   # month t-1 (published early in t)

M = own.add_prefix("own_").join(own_red.add_prefix("red_")).join(dict_m).join(tc_m).join(tc_n).join(tc_bal).join(tc_ph).join(SF).join(EPU)
M.to_parquet(PROCESSED / "media_monthly.parquet")
weekly.to_parquet(PROCESSED / "media_weekly.parquet")
M.to_csv(TABLES / "media_monthly.csv")
weekly.to_csv(TABLES / "media_weekly_2026.csv")

# ---------------- convergent validity (levels and changes), covered months only
Mq = M[["TC_NEGNET", "SFFED", "DICT_NEGNET"]].groupby(M.index.to_period("Q").start_time).mean().join(
    ownq[["NEGNET"]].rename(columns={"NEGNET": "ownQ_NEGNET"})).join(ownq["covered"].rename("ownQ_covered"))
Mq.to_parquet(PROCESSED / "media_quarterly.parquet")
cvq = Mq[Mq["ownQ_covered"].fillna(False).astype(bool)]
pairs = [("TC_NEGNET", "SFFED", M), ("DICT_NEGNET", "SFFED", M), ("TC_NEGNET", "DICT_NEGNET", M),
         ("ownQ_NEGNET", "SFFED", cvq), ("ownQ_NEGNET", "TC_NEGNET", cvq), ("ownQ_NEGNET", "DICT_NEGNET", cvq)]
conv = []
for a, b, cv in pairs:
    j = cv[[a, b]].dropna()
    conv.append({"a": a, "b": b, "freq": "quarterly" if cv is cvq else "monthly", "N": len(j), "r_levels": float(j.corr().iloc[0, 1]),
                 "r_changes": float(j.diff().dropna().corr().iloc[0, 1])})
pd.DataFrame(conv).to_csv(TABLES / "media_convergent_validity.csv", index=False)
R["convergent_validity"] = conv
R["tierC_train_N"] = int(len(tr))
(OUTPUTS / "results_media.json").write_text(json.dumps(R, indent=1, default=str))
print(json.dumps(R, indent=1, default=str)[:3000])
