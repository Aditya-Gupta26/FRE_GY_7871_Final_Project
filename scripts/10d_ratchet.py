"""E5, EXPLORATORY (added after the main results; recorded as note 16): the inflation "ratchet". RQ4 found that in
months when inflation rose 1 pp, ICS was about 6 points lower, while in months when it fell 1 pp, ICS was no higher.
If that lasts, people judge the economy by the recent PEAK of inflation rather than by today's rate, and a model that
treats rises and falls alike expects a recovery that never comes. This script measures how much of the 2026 gap that
accounts for.

Main specification (one extra term in the economy-only model):
  ICS_t = a + b_U U_t + b_pi pi_t + b_R (peak_t - pi_t) + b_g g_t + e_t,  peak_t = highest pi over the past N months
  - No ratchet (falls help as much as rises hurt): b_R = 0.
  - Full ratchet (falls since the peak give no relief): b_R = b_pi, i.e. sentiment follows the peak, not the rate.
  - b_R with the opposite sign to b_pi: falls help MORE than the current rate implies (relief after a peak).
Literal "rises and falls" check: the same with (peak_t - pi_t) replaced by the sum of all monthly falls in pi over the
past N months (F_t). Since pi_t = pi_{t-N} + rises - falls, b_F = b_pi again means falls give no relief.
Main: N = 60 months, trained on 1978-2019 (it contains the 1979-80 peak and the 1981-86 fall, so the model has a
ratchet to learn from), latest-vintage data with publication lags (the ablation panel of scripts/10c). Checks: N = 36;
training from 1985; the cost of borrowing (30-year mortgage rate) added, since rates fell with inflation in the 1980s;
the cumulative-falls form; the 2010-19 real-time Model E window. Each fit is scored on the 2026 gap and on accuracy in
normal years (train to 2009, predict 2010-19; for the 2010-19 window, train 2010-16, predict 2017-19) and after COVID
(Feb 2021 to Dec 2025).
    python scripts/10d_ratchet.py
Needs scripts 01 and 10c. Writes outputs/results_ratchet.json and outputs/tables/ratchet_panel.csv.
"""
import _bootstrap  # noqa: F401
import json

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.config import OUTPUTS, PROCESSED, TABLES
from src.econ_model import fit
from src.fred import latest

Y26 = pd.date_range("2026-01-01", "2026-10-01", freq="MS")
Y19 = pd.date_range("2019-01-01", "2019-12-01", freq="MS")
POST = pd.date_range("2021-02-01", "2025-12-01", freq="MS")
NORMAL = pd.date_range("2010-01-01", "2019-12-01", freq="MS")

# inflation as known on day 14 of month t: 12-month change of PCE to month t-2 (same rule as the ablation panel)
pce = latest("PCEPI").dropna()
allm = pd.date_range("1962-01-01", "2026-10-01", freq="MS")
pi_all = pd.Series({t: 100 * (pce[t - pd.DateOffset(months=2)] / pce[t - pd.DateOffset(months=14)] - 1) for t in allm})
L = pd.read_csv(TABLES / "ablation_panel.csv", index_col=0, parse_dates=True)
assert np.allclose(L["pi"], pi_all.reindex(L.index)), "inflation differs from the ablation panel"


def add_terms(data, pi, ns):
    for n in ns:
        pk = pi.rolling(n, min_periods=n).max()
        data[f"peak{n}"] = pk.reindex(data.index)
        data[f"R{n}"] = (pk - pi).reindex(data.index)
        data[f"F{n}"] = (-pi.diff()).clip(lower=0).rolling(n, min_periods=n).sum().reindex(data.index)


add_terms(L, pi_all, (60, 36))
assert L[["R60", "R36", "F60"]].notna().all().all()


def run(cols, data, train, val_train, val_test):
    d = data.loc[train[0]:train[1]]
    f = fit(d["ICS"], d[cols])
    pred = sm.add_constant(data[cols], has_constant="add") @ f.params
    gap = data["ICS"] - pred
    fv = fit(data.loc[val_train[0]:val_train[1], "ICS"], data.loc[val_train[0]:val_train[1], cols])
    gv = data["ICS"] - sm.add_constant(data[cols], has_constant="add") @ fv.params
    rm = lambda e: float(np.sqrt((e.dropna() ** 2).mean()))
    return f, {"gap2026": float(gap.loc[Y26].mean()), "pred2026": float(pred.loc[Y26].mean()),
               "rmse_post_2021_25": rm(gap.loc[POST]), "bias_post_2021_25": float(gap.loc[POST].mean()),
               "rmse_normal_oos": rm(gv.loc[val_test]), "oos_window": [str(val_test[0].date()), str(val_test[-1].date())],
               "N": int(f.nobs), "R2": float(f.rsquared)}


def spec(data, term, train, val_train, base, val_test=NORMAL):
    f0, m0 = run(base, data, train, val_train, val_test)
    f1, m1 = run(base + [term], data, train, val_train, val_test)
    names = list(f1.params.index)
    b_pi, b_T, se_T = float(f1.params["pi"]), float(f1.params[term]), float(f1.bse[names.index(term)])
    dT = float(data.loc[Y26, term].mean() - data.loc[Y19, term].mean())
    tc = stats.t.ppf(0.95, f1.nu)
    n = int(term[1:])
    return {"term": term, "memory_months": n, "train": train, "controls": base, "base": m0, "ratchet": m1,
            "coef": {c: {"b": float(f1.params[c]), "se": float(f1.bse[names.index(c)]), "p": float(f1.pvalues[c])} for c in base + [term]},
            "coef_base": {c: float(f0.params[c]) for c in base},
            "share_b_term_over_b_pi": b_T / b_pi,   # 1 = full ratchet, 0 = none, < 0 = relief after a peak
            "gap_change_points": m1["gap2026"] - m0["gap2026"],   # > 0 = the term closes part of the 2026 gap
            "term_effect_2019_to_2026": {"points": b_T * dT, "ci90": sorted([(b_T - tc * se_T) * dT, (b_T + tc * se_T) * dT]),
                                         "change_in_term": dT},
            "inputs": {"peak_2019": float(data.loc[Y19, f"peak{n}"].mean()), "peak_2026": float(data.loc[Y26, f"peak{n}"].mean()),
                       "pi_2019": float(data.loc[Y19, "pi"].mean()), "pi_2026": float(data.loc[Y26, "pi"].mean()),
                       "term_2019": float(data.loc[Y19, term].mean()), "term_2026": float(data.loc[Y26, term].mean())}}


LONG = ("1978-01-01", "2019-12-01"), ("1978-01-01", "2009-12-01")
OUT = {"spec": "ICS on U, pi, g and one ratchet term: R = peak of pi over the past N months - pi, or F = sum of monthly "
               "falls in pi over the past N months. Term coefficient = b_pi means falls give no relief (full ratchet), "
               "0 means falls count like rises, opposite sign to b_pi means relief after a peak.",
       "main_peak_60m_1978_2019": spec(L, "R60", *LONG, ["U", "pi", "g"]),
       "peak_36m_1978_2019": spec(L, "R36", *LONG, ["U", "pi", "g"]),
       "peak_60m_from_1985": spec(L, "R60", ("1985-01-01", "2019-12-01"), ("1985-01-01", "2009-12-01"), ["U", "pi", "g"]),
       "peak_60m_with_borrowing": spec(L, "R60", *LONG, ["U", "pi", "g", "B"]),
       "cumulative_falls_60m_1978_2019": spec(L, "F60", *LONG, ["U", "pi", "g"])}
# the project's Model E window (2010-19, real-time U, pi, g); the terms use latest-vintage PCE before 2010
P = pd.read_parquet(PROCESSED / "panel_realtime_mid.parquet")[["U", "pi", "g_qoq"]].copy()
P["ICS"] = pd.read_parquet(PROCESSED / "umich_indices.parquet")["ICS"].reindex(P.index)
add_terms(P, pd.concat([pi_all.loc[:"2009-12-01"], P["pi"]]), (60,))
OUT["model_e_window_2010_2019_realtime_peak_60m"] = spec(P, "R60", ("2010-01-01", "2019-12-01"), ("2010-01-01", "2016-12-01"),
                                                         ["U", "pi", "g_qoq"], val_test=pd.date_range("2017-01-01", "2019-12-01", freq="MS"))
OUT["model_e_window_2010_2019_realtime_peak_60m"]["note"] = "2010-19 has no large peak-and-fall, so the term is barely identified here"
L[["ICS", "U", "pi", "g", "B", "peak60", "R60", "F60", "peak36", "R36"]].to_csv(TABLES / "ratchet_panel.csv")
(OUTPUTS / "results_ratchet.json").write_text(json.dumps(OUT, indent=1, default=float))
for k, v in OUT.items():
    if isinstance(v, dict):
        c, t = v["coef"], v["term"]
        print(f"{k:44s} b_pi {c['pi']['b']:+.2f}  b_{t} {c[t]['b']:+.2f} (p {c[t]['p']:.3f}) share {v['share_b_term_over_b_pi']:+.2f} | "
              f"gap26 {v['base']['gap2026']:+.1f} -> {v['ratchet']['gap2026']:+.1f} | term effect {v['term_effect_2019_to_2026']['points']:+.1f} "
              f"[{v['term_effect_2019_to_2026']['ci90'][0]:+.1f}, {v['term_effect_2019_to_2026']['ci90'][1]:+.1f}] | "
              f"RMSE 21-25 {v['base']['rmse_post_2021_25']:.1f} -> {v['ratchet']['rmse_post_2021_25']:.1f} | "
              f"normal OOS {v['base']['rmse_normal_oos']:.1f} -> {v['ratchet']['rmse_normal_oos']:.1f}")
