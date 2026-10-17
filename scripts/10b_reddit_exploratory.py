"""E3, EXPLORATORY (added after the main results; not in the pre-registration, recorded as note 14): does
Reddit tone move Michigan sentiment, the way RQ2 asks it of news? The Tier C classifier (the same training set
and settings as scripts/09) scores all 50,926 kept Reddit posts; a monthly Reddit net negativity series
(relevant posts, subreddit fixed effects so a change in which subreddits are present does not move it,
survey-month windows) then goes through the RQ2
tests: the level model with the economy and the six household costs, its implied contribution to the 2026
gap, month-to-month changes, which series moves first (Toda-Yamamoto with circular shifts), and whether it
adds anything once news tone is in. No forecast test: this classifier was trained on labels from all
months, so an out-of-sample forecast would look ahead.
    python scripts/10b_reddit_exploratory.py
Needs scripts 01, 04, 05, 07, 08, 09. Writes outputs/results_reddit.json and outputs/tables/e3_reddit_*.csv.
"""
import _bootstrap  # noqa: F401
import json
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import f1_score

from src.baselines import train
from src.config import CODED, END, INTERIM, LABELS, OUTPUTS, PREREG, PROCESSED, TABLES
from src.econ_model import fit
from src.tests import leave_one_year_out, robustness_value, toda_yamamoto

warnings.filterwarnings("ignore")
MONTHS = pd.date_range("2010-01-01", END, freq="MS")
COVID = pd.date_range("2020-03-01", "2021-01-01", freq="MS")
keep = MONTHS.difference(COVID)
BASE = ["U", "pi", "g_qoq"]
H1 = PREREG["h1_controls"]
OUT = {}

# ---------------- 1. the same Tier C classifiers as scripts/09
C = pd.read_parquet(CODED / "codes.parquet")
K = pd.read_csv(CODED / "sample_key.csv", parse_dates=["date", "survey_month"])
X = C.merge(K, on="item_id")
red = pd.read_parquet(INTERIM / "reddit.parquet")
corpus = pd.concat([pd.read_parquet(INTERIM / "news.parquet")[["doc_id", "clean"]], red[["doc_id", "clean"]]])
tr = X[X["tier"].isin(["B_news", "A_news2026", "B_reddit", "A_reddit2026", "A_release"])].merge(corpus, on="doc_id")
tr["clean"] = tr["clean"].fillna("")
m_rel = train(tr["clean"], tr["relevant"])
tr_rel = tr[tr["relevant"] == "yes"]
m_tone = train(tr_rel["clean"], tr_rel["tone"])

# ---------------- 2. how well it reads Reddit: the 150 Reddit gold items (never used in training)
gk = pd.read_csv(LABELS / "gold_final.csv")
gt = pd.read_csv(LABELS / "gold_sheet.csv")
g = gk[gk["source_type"] == "reddit"].merge(gt, on="item_id")
overlap = int(g["doc_id"].isin(tr["doc_id"]).sum())
g["p_rel"] = m_rel.predict(g["text"].fillna(""))
gr = g[g["relevant"] == "yes"]
OUT["reddit_gold"] = {"N": int(len(g)), "N_relevant": int(len(gr)), "doc_overlap_with_training": overlap,
                      "relevant_macro_f1": float(f1_score(g["relevant"], g["p_rel"], average="macro")),
                      "tone_macro_f1": float(f1_score(gr["tone"], m_tone.predict(gr["text"].fillna("")), average="macro"))}
# Opus on the same relevant Reddit gold items (like for like with Tier C's tone score above)
Cg = C.set_index("item_id")
OUT["reddit_gold"]["opus_tone_macro_f1_reddit_relevant"] = float(f1_score(gr["tone"], Cg.loc[gr["item_id"], "tone"].astype(str), average="macro"))
V = pd.read_csv(TABLES / "val_tools_vs_gold.csv")
OUT["reddit_gold"]["opus_tone_macro_f1_reddit"] = float(V[(V["tool"] == "opus") & (V["field"] == "tone") &
                                                          (V["subset"] == "source:reddit")]["macro_f1"].iloc[0])

# ---------------- 3. score every kept post; monthly series
red["clean"] = red["clean"].fillna("")
red["tc_relevant"] = m_rel.predict(red["clean"])
R = red[red["tc_relevant"] == "yes"].copy()
R["tone"] = m_tone.predict(R["clean"])
R["neg"] = (R["tone"] == "negative").astype(float)
R["pos"] = (R["tone"] == "positive").astype(float)
R["NEGNET"] = R["neg"] - R["pos"]
by_sub = R.groupby(["survey_month", "sub"])["NEGNET"].mean().unstack()
# Subreddits differ in level and r/personalfinance is missing in some months, so a plain average over the subreddits
# present would move with the mix. Each subreddit's own mean is taken out before averaging, then the mean of the
# subreddit means is added back (fixed effects, as Shapiro et al. 2022 do for newspapers).
sub_mean = by_sub.mean()
red_m = (by_sub - sub_mean).mean(axis=1).add(sub_mean.mean()).reindex(MONTHS).rename("RED_TC_NEGNET")
OUT["subreddit_months_present"] = {k: int(v) for k, v in by_sub.notna().sum().items()}
n_m = R.groupby("survey_month").size().reindex(MONTHS).fillna(0).astype(int).rename("n_relevant")
Mo = pd.read_parquet(PROCESSED / "media_monthly.parquet")
series = pd.concat([red_m, n_m, by_sub.reindex(MONTHS).add_prefix("sub_"), Mo["TC_NEGNET"]], axis=1)
series.to_csv(TABLES / "e3_reddit_monthly.csv")
# split-half reliability: random halves of each month's posts, Spearman-Brown (as src.media.split_half)
rng = np.random.default_rng(7871)
rs = []
for _ in range(200):
    h = rng.integers(0, 2, len(R))
    j = pd.concat([R[h == 0].groupby("survey_month")["NEGNET"].mean(), R[h == 1].groupby("survey_month")["NEGNET"].mean()],
                  axis=1).dropna()
    rs.append(j.corr().iloc[0, 1])
r_half = float(np.mean(rs))
OUT["corpus"] = {"posts_scored": int(len(red)), "posts_relevant": int(len(R)), "relevance_rate": float(len(R) / len(red)),
                 "median_relevant_per_month": float(n_m.loc[MONTHS].median()), "min_relevant_per_month": int(n_m.min()),
                 "months_with_20plus": int((n_m >= 20).sum()), "months": len(MONTHS),
                 "split_half": {"r_half": r_half, "spearman_brown": 2 * r_half / (1 + r_half), "reps": 200},
                 "corr_with_news_tierC": {"r_levels": float(series[["RED_TC_NEGNET", "TC_NEGNET"]].loc[keep].corr().iloc[0, 1]),
                                          "r_changes": float(series[["RED_TC_NEGNET", "TC_NEGNET"]].loc[keep].diff().corr().iloc[0, 1])}}

# ---------------- 4. the RQ2 tests with Reddit tone
S = pd.read_parquet(PROCESSED / "umich_indices.parquet")["ICS"].reindex(MONTHS)
P = pd.read_parquet(PROCESSED / "panel_realtime_mid.parquet")
D = pd.DataFrame({"S": S}).join(P[BASE + H1]).join(series[["RED_TC_NEGNET", "TC_NEGNET"]]).reindex(keep)
med = "RED_TC_NEGNET"
d19 = series[med].loc["2019-01-01":"2019-12-01"].mean()
d26 = series[med].loc["2026-01-01":END].mean()
dm = float(d26 - d19)


def level(cols, label):
    d = D[["S"] + cols].dropna()
    f = fit(d["S"], d[cols])
    b, se = float(f.params[med]), float(f.bse[list(f.params.index).index(med)])
    tc = stats.t.ppf(0.95, f.nu)
    lo, hi = sorted([dm * (b - tc * se), dm * (b + tc * se)])
    return {"model": label, "N": int(f.nobs), "nu": f.nu, "coef": b, "se": se,
            "p_expected_sign": float(stats.t.cdf(b / se, f.nu)),     # expected: negative
            "implied_contribution_if_causal": b * dm, "implied_ci90": [lo, hi],
            "robustness_value": robustness_value(float(f.ols.tvalues[med]), f.df_resid), "_fit": (d, cols)}


lv = [level(BASE + [med], "economy + Reddit"), level(BASE + H1 + [med], "economy + household costs + Reddit"),
      level(BASE + H1 + ["TC_NEGNET", med], "economy + household costs + news + Reddit")]
d_, cols_ = lv[1].pop("_fit")
loyo = leave_one_year_out(d_["S"], d_[cols_], med)
d2 = d_.loc[~d_.index.year.isin([2021, 2022])]
f2 = fit(d2["S"], d2[cols_])
lv[1].update({"loyo_max_p": loyo["max_p"], "loyo_coef_range": [loyo["min_coef"], loyo["max_coef"]],
              "drop_2021_22": {"coef": float(f2.params[med]), "p_two_sided": float(f2.pvalues[med])}})
for x in lv:
    x.pop("_fit", None)
OUT["reddit_change_2019_2026"] = {"mean_2019": float(d19), "mean_2026": float(d26), "change": dm}
OUT["level_models"] = lv
# month-to-month changes (both months outside the COVID window)
dd = pd.DataFrame({"S": S}).join(P[BASE]).join(series[[med]]).reindex(MONTHS).diff()
dd = dd[dd.index.isin(keep) & (dd.index - pd.DateOffset(months=1)).isin(keep)].dropna()
fc = fit(dd["S"], dd[BASE + [med]])
OUT["changes"] = {"N": int(fc.nobs), "coef": float(fc.params[med]), "p_two_sided": float(fc.pvalues[med])}
# which moves first
x = series[med].where(MONTHS.isin(keep))
y = S.where(MONTHS.isin(keep))
exog = P[BASE].reindex(MONTHS)
OUT["toda_yamamoto"] = {"reddit_to_sentiment": toda_yamamoto(y, x, exog=exog),
                        "sentiment_to_reddit": toda_yamamoto(x, y, exog=exog)}
pd.DataFrame([{k: v for k, v in r.items() if k != "implied_ci90"} | {"ci_lo": r["implied_ci90"][0], "ci_hi": r["implied_ci90"][1]}
              for r in lv]).to_csv(TABLES / "e3_reddit_level_models.csv", index=False)
(OUTPUTS / "results_reddit.json").write_text(json.dumps(OUT, indent=1, default=float))
print(json.dumps(OUT, indent=1, default=float))
