"""RQ3 and the economic baseline: Model E, out-of-sample predictions with intervals, the sentiment
gap, how much is explained, the H1 controls (2010-19 and the 1992-2019 long real-time sample),
the H3 variants, seasonality, stability and group gaps. Pre-registered in config.PREREG.
    python scripts/04_econ_baseline.py
Writes outputs/results_econ.json, outputs/tables/rq3_*.csv, data/processed/gap_main.parquet.
"""
import _bootstrap  # noqa: F401
import json
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint

from src.config import END, UMICH_OCT2026_PRELIM, PROCESSED, TABLES, OUTPUTS, PREREG
from src.econ_model import Boot, decompose, fit, mean_gap_band, mean_gap_null_ar1, predict
from src.forecast import expanding_nowcast
from src.fred import latest
from src.realtime import affordability, build_long_panel
from src.umich import components

warnings.filterwarnings("ignore")
TR = slice("2010-01-01", "2019-12-01")
OOS = slice("2020-01-01", END)
COVID = pd.date_range("2020-03-01", "2021-01-01", freq="MS")
POST = slice("2021-02-01", END)
Y26 = slice("2026-01-01", END)
Y19 = slice("2019-01-01", "2019-12-01")
BASE = ["U", "pi", "g_qoq"]
H1 = PREREG["h1_controls"]

P = pd.read_parquet(PROCESSED / "panel_realtime_mid.parquet")
PS = pd.read_parquet(PROCESSED / "panel_realtime_start.parquet")
I = pd.read_parquet(PROCESSED / "umich_indices.parquet")
T = pd.read_parquet(PROCESSED / "umich_tables.parquet")
C = components()
C.to_parquet(PROCESSED / "umich_components.parquet")
S = I[["ICS", "ICC", "ICE"]].join(C[["X1_fin_now", "X2_fin_exp", "X3_bus_1y", "X4_bus_5y", "X5_durables"]]).join(T)
S = S.loc["2010-01-01":END]
assert I.loc[END, "ICS"] == UMICH_OCT2026_PRELIM["ICS"] or not I.loc[END, "preliminary"], "preliminary value not applied"
R = {"prereg_time": "2026-10-12 23:58 ET"}


def keep(idx):
    return idx.difference(COVID)


def run(target: pd.Series, X: pd.DataFrame, name: str, boot_reps: int = 2000, full: bool = True) -> dict:
    y = target.reindex(X.index)
    f = fit(y.loc[TR], X.loc[TR])
    out = {"N_train": int(f.nobs), "R2_train": float(f.rsquared), "nu_ewc": f.nu,
           "coef": f.table().round(6).to_dict(orient="index")}
    pr = predict(f, X.loc[OOS])
    gap = (y.loc[OOS] - pr["pred"]).rename("gap")
    avail = gap.dropna().index                       # months with an observed target
    w26 = avail[(avail >= "2026-01-01") & (avail <= END)]
    wpost = keep(avail[(avail >= "2021-02-01") & (avail <= END)])
    m26, mpost = gap.loc[w26].mean(), gap.loc[wpost].mean()
    out.update(mean_gap_2026=float(m26), n_2026=int(len(w26)), last_month=str(avail.max().date()),
               mean_gap_post=float(mpost), n_post=int(len(wpost)),
               mean_gap_2026_finals_only=float(gap.loc[w26[w26 <= "2026-09-01"]].mean()))
    if full:
        bt = Boot(y.loc[TR], X.loc[TR], reps=boot_reps)
        pi = bt.pi(X.loc[OOS])
        out["mean_gap_2026_test"] = bt.mean_gap_null(X.loc[w26], float(m26))
        out["mean_gap_post_test"] = bt.mean_gap_null(X.loc[wpost], float(mpost))
        out["mean_gap_2026_test_ar1"] = mean_gap_null_ar1(f, X.loc[w26], float(m26))
        out["mean_gap_post_test_ar1"] = mean_gap_null_ar1(f, X.loc[wpost], float(mpost))
        out["mean_gap_2026_analytic"] = mean_gap_band(f, X.loc[w26], gap.loc[w26])
        d = decompose(f, X, y, Y19, w26)
        d["share_ci_boot"] = bt.decomp_ci(pd.Series(d["dx"]), d["actual_change"])
        out["decomposition_2019_to_2026"] = d
        e = y.loc[wpost] - pr["pred"].loc[wpost]
        out["oos_rmse_post"] = float(np.sqrt((e ** 2).mean()))
        out["oos_rmse_post_trainmean"] = float(np.sqrt(((y.loc[wpost] - y.loc[TR].mean()) ** 2).mean()))
        eg = coint(y.loc[TR], X.loc[TR])
        out["engle_granger_t"], out["engle_granger_p"] = float(eg[0]), float(eg[1])
        out["resid_adf_p"] = float(adfuller(f.resid, autolag="AIC")[1])
        series = pd.concat([y.rename("actual"), pr, pi[["bb_lo", "bb_hi"]], gap], axis=1)
        series.loc[TR, "fitted"] = f.ols.fittedvalues
        series["covid_window"] = series.index.isin(COVID)
        series.to_csv(TABLES / f"rq3_series_{name}.csv")
        sp = series.loc[wpost]
        out["share_actual_outside_bb_post"] = float(((sp["actual"] < sp["bb_lo"]) | (sp["actual"] > sp["bb_hi"])).mean())
        out["share_actual_outside_analytic_post"] = float(((sp["actual"] < sp["lo"]) | (sp["actual"] > sp["hi"])).mean())
    return out


# ---------------- 1. Model E for ICS, ICC, ICE and the five components
X = P[BASE]
for tgt in ["ICS", "ICC", "ICE", "X1_fin_now", "X2_fin_exp", "X3_bus_1y", "X4_bus_5y", "X5_durables"]:
    R[f"E_{tgt}"] = run(S[tgt], X, tgt)
    print(tgt, "R2", round(R[f"E_{tgt}"]["R2_train"], 3), "mean gap 2026", round(R[f"E_{tgt}"]["mean_gap_2026"], 2),
          "p", R[f"E_{tgt}"]["mean_gap_2026_test"]["p_two_sided"])
gm = pd.read_csv(TABLES / "rq3_series_ICS.csv", index_col=0, parse_dates=True)
gm.to_parquet(PROCESSED / "gap_main.parquet")

# ---------------- 2. interval coverage check: train 2010-16, test 2017-19
bt = Boot(S["ICS"].loc["2010-01-01":"2016-12-01"], X.loc["2010-01-01":"2016-12-01"])
pi = bt.pi(X.loc["2017-01-01":"2019-12-01"])
a = S["ICS"].loc["2017-01-01":"2019-12-01"]
f16 = fit(S["ICS"].loc["2010-01-01":"2016-12-01"], X.loc["2010-01-01":"2016-12-01"])
pa = predict(f16, X.loc["2017-01-01":"2019-12-01"])
R["coverage_check_2017_19"] = {"N": int(len(a)), "boot_coverage": float(((a >= pi.bb_lo) & (a <= pi.bb_hi)).mean()),
                                "analytic_coverage": float(((a >= pa.lo) & (a <= pa.hi)).mean()),
                                "mean_error": float((a - pi.pred).mean())}

# ---------------- 3. H1 controls, 2010-19 sample: each alone and jointly
base26 = R["E_ICS"]["mean_gap_2026"]
rows = []
for ctrl in [[c] for c in H1] + [H1]:
    Xc = P[BASE + ctrl]
    o = run(S["ICS"], Xc, "h1_" + "_".join(ctrl) if len(ctrl) == 1 else "h1_all", full=False)
    f = fit(S["ICS"].loc[TR], Xc.loc[TR])
    w = f.wald(ctrl)
    rows.append({"controls": "+".join(ctrl), "R2_train": o["R2_train"], "mean_gap_2026": o["mean_gap_2026"],
                 "share_2026_gap_closed": 1 - o["mean_gap_2026"] / base26, "mean_gap_post": o["mean_gap_post"],
                 "wald_F_ewc": w["F_ewc"], "wald_p_ewc": w["p_ewc"], "wald_p_nw": w["p_nw"],
                 "coef": {c: round(float(f.params[c]), 4) for c in ctrl}})
h1 = pd.DataFrame(rows)
from statsmodels.stats.multitest import multipletests  # noqa: E402
single = h1.iloc[:-1]
h1.loc[single.index, "bh_q_ewc"] = multipletests(single["wald_p_ewc"].fillna(1), method="fdr_bh")[1]
h1.to_csv(TABLES / "rq3_h1_controls_2010_19.csv", index=False)
R["h1_2010_19"] = h1.to_dict(orient="records")

# ---------------- 4. H1 in the long real-time sample 1992-2019
LP = build_long_panel()
LP.to_parquet(PROCESSED / "panel_long.parquet")
cpi = latest("CPIAUCNS")


def cpi_rt(t):  # same lag rule as the long panel: month t-2
    m = t - pd.DateOffset(months=2)
    return (100 * (cpi[m] / cpi[m - pd.DateOffset(months=12)] - 1), 100 * (cpi[m] / cpi[m - pd.DateOffset(months=36)] - 1))


O = P[["U", "g_qoq", "mort30"]].loc[OOS].copy()
O["pi_cpi"], O["pi36_cpi"] = zip(*[cpi_rt(t) for t in O.index])
Lall = pd.concat([LP[["U", "g_qoq", "pi_cpi", "pi36_cpi", "mort30"]], O])
# one affordability definition for the whole 1992-2026 range (income of month t-2), normalised to the
# 2019 mean (computing it on the 2020-26 rows alone would have no 2019 to normalise by)
Lall["afford"] = affordability(Lall.index, Lall["mort30"], pd.Series(Lall.index - pd.DateOffset(months=2), index=Lall.index))
Sl = I["ICS"]
LTR = slice("1992-01-01", "2019-12-01")
rows = []
lbase = ["U", "pi_cpi", "g_qoq"]
lb26 = None
for ctrl in [[], ["pi36_cpi"], ["mort30"], ["afford"], ["pi36_cpi", "mort30", "afford"]]:
    Xl = Lall[lbase + ctrl]
    f = fit(Sl.reindex(Xl.index).loc[LTR], Xl.loc[LTR])
    pr = predict(f, Xl.loc[OOS])
    gap = Sl.reindex(Xl.index).loc[OOS] - pr["pred"]
    m26 = float(gap.loc[Y26].mean())
    lb26 = m26 if not ctrl else lb26
    w = f.wald(ctrl) if ctrl else {"F_ewc": np.nan, "p_ewc": np.nan, "p_nw": np.nan}
    rows.append({"controls": "+".join(ctrl) or "base", "N_train": int(f.nobs), "nu": f.nu, "R2_train": float(f.rsquared),
                 "mean_gap_2026": m26, "share_2026_gap_closed": (1 - m26 / lb26) if ctrl else 0.0,
                 "mean_gap_post": float(gap.loc[keep(gap.loc[POST].dropna().index)].mean()),
                 "n_post": int(len(keep(gap.loc[POST].dropna().index))),
                 "wald_p_ewc": w["p_ewc"], "wald_p_nw": w["p_nw"],
                 "coef": {c: round(float(f.params[c]), 4) for c in lbase + ctrl}})
    if ctrl == ["pi36_cpi", "mort30", "afford"]:
        pd.concat([Sl.reindex(Xl.index).loc[OOS].rename("actual"), pr["pred"], gap.rename("gap")], axis=1).to_csv(
            TABLES / "rq3_series_long_h1.csv")
    if not ctrl:
        pd.concat([Sl.reindex(Xl.index).loc[OOS].rename("actual"), pr["pred"], gap.rename("gap")], axis=1).to_csv(
            TABLES / "rq3_series_long_base.csv")
lh = pd.DataFrame(rows)
lh.to_csv(TABLES / "rq3_h1_controls_long.csv", index=False)
R["h1_long_1992_2019"] = lh.to_dict(orient="records")

# ---------------- 5. variants (H3: measurement, timing, revisions; GDP/inflation definitions)
var = {}
for name, Xv, Sv in [("g_yoy", P[["U", "pi", "g_yoy"]], S["ICS"]),
                     ("core_pce", P[["U", "pi_core", "g_qoq"]], S["ICS"]),
                     ("cpi", P[["U", "cpi", "g_qoq"]], S["ICS"]),
                     ("start_of_month_info", PS[BASE], S["ICS"]),
                     ("revised_data", P[["U_latest", "pi_latest", "g_qoq_latest"]].set_axis(BASE, axis=1), S["ICS"])]:
    o = run(Sv, Xv, "var_" + name, full=False)
    var[name] = {"R2_train": o["R2_train"], "mean_gap_2026": o["mean_gap_2026"], "mean_gap_post": o["mean_gap_post"]}
# quarterly-frequency model: quarter-average sentiment on the real-time data of the quarter's middle month
Q = S["ICS"].resample("QS").mean().to_frame("ICS").join(P[BASE].loc[P.index.month.isin([2, 5, 8, 11])].set_axis(
    P[BASE].loc[P.index.month.isin([2, 5, 8, 11])].index.to_period("Q").start_time))
fq = fit(Q["ICS"].loc[TR], Q[BASE].loc[TR])
pq = predict(fq, Q[BASE].loc["2020-01-01":"2026-07-01"])
gq = Q["ICS"].loc["2020-01-01":"2026-07-01"] - pq["pred"]
var["quarterly"] = {"N_train": int(fq.nobs), "R2_train": float(fq.rsquared),
                    "mean_gap_2026_Q1_Q3": float(gq.loc["2026-01-01":"2026-07-01"].mean())}
R["variants"] = var
R["h3_revision_effect_share"] = float(abs(var["revised_data"]["mean_gap_2026"] - base26) / abs(base26))

# ---------------- 6. seasonality (11 month dummies: q > nu, so the Newey-West Wald is used)
D = pd.get_dummies(P.index.month, prefix="m", drop_first=True).astype(float).set_index(P.index)
fs = fit(S["ICS"].loc[TR], pd.concat([X, D], axis=1).loc[TR])
R["seasonality"] = {"p_nw_month_dummies": fs.wald(list(D.columns))["p_nw"], "note": "11 restrictions > nu, EWC F undefined"}

# ---------------- 7. stability: rolling 60-month coefficients; expanding vs fixed errors
roll = []
Sx = S["ICS"].to_frame("y").join(X)
for end in pd.date_range("2015-01-01", END, freq="MS"):
    w = Sx.loc[end - pd.DateOffset(months=59):end]
    w = w.loc[w.index.difference(COVID)]
    if len(w) < 48:
        continue
    f = fit(w["y"], w[BASE])
    roll.append({"end": end, **{c: float(f.params[c]) for c in BASE}, "N": int(f.nobs)})
roll = pd.DataFrame(roll).set_index("end")
roll.to_csv(TABLES / "rq3_rolling_coefs.csv")
R["rolling_sign_changes"] = {c: int((np.sign(roll[c]).diff().abs() > 0).sum()) for c in BASE}
R["rolling_coef_range"] = {c: [float(roll[c].min()), float(roll[c].max())] for c in BASE}
ex = expanding_nowcast(S["ICS"], X.loc[X.index.difference(COVID)], first_origin="2021-02-01", train_start="2010-01-01")
fixed_err = gm.loc[ex.index, "gap"]
R["expanding_vs_fixed_rmse_post"] = {"expanding": float(np.sqrt((ex.err ** 2).mean())),
                                     "fixed": float(np.sqrt((fixed_err ** 2).mean())), "N": int(len(ex))}

# ---------------- 8. group gaps (income terciles, age, region: same model per group; party descriptive)
grp = {}
for g in ["ICS_bottom", "ICS_middle", "ICS_top", "ICS_age18_34", "ICS_age35_54", "ICS_age55p",
          "ICS_NE", "ICS_MW", "ICS_S", "ICS_W"]:
    o = run(S[g], X.loc[:"2026-08-01"], "grp_" + g, full=False)
    grp[g] = {"R2_train": o["R2_train"], "mean_gap_2026_jan_aug": float(
        (S[g].loc["2026-01-01":"2026-08-01"] - predict(fit(S[g].loc[TR], X.loc[TR]), X.loc["2026-01-01":"2026-08-01"])["pred"]).mean())}
party = S[["ICS_DEM", "ICS_IND", "ICS_REP"]]
grp["party_levels"] = {k: {"mean_2017_19": float(party[k].loc["2017-01-01":"2019-12-01"].mean()),
                           "mean_2021feb_2024dec": float(party[k].loc["2021-02-01":"2024-12-01"].mean()),
                           "mean_2026_jan_aug": float(party[k].loc["2026-01-01":"2026-08-01"].mean())}
                       for k in party.columns}
pd.DataFrame({k: v for k, v in grp.items() if k != "party_levels"}).T.to_csv(TABLES / "rq3_group_gaps.csv")
R["groups"] = grp

def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, float) and not np.isfinite(o):
        return None
    if isinstance(o, (np.floating, np.integer)):
        return _clean(o.item())
    return o


(OUTPUTS / "results_econ.json").write_text(json.dumps(_clean(R), indent=1, default=str, allow_nan=False))
print("coverage", R["coverage_check_2017_19"])
print(h1[["controls", "mean_gap_2026", "share_2026_gap_closed", "wald_p_ewc"]].round(3).to_string())
print(lh[["controls", "N_train", "R2_train", "mean_gap_2026", "share_2026_gap_closed", "wald_p_ewc"]].round(3).to_string())
print(json.dumps(var, indent=1))
print("revision effect share", round(R["h3_revision_effect_share"], 3), "| seasonality", R["seasonality"])
print("rolling sign changes", R["rolling_sign_changes"], R["expanding_vs_fixed_rmse_post"])
