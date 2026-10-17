"""E4, EXPLORATORY (added after the main results; recorded as note 15): an ablation of the ~26 index points
of the 2026 gap that the measured pieces leave over. We postulated three mechanisms the 2010-19 Model E
cannot see: the PRICE LEVEL (P), the COST OF BORROWING (B) and PARTISAN MOOD (R). A model trained on 2010-19
cannot learn a price-level effect (the price level never left its trend then), so the ablation trains on
1978-2019, which includes the 1970s-80s price and interest-rate shocks.

Part A, time-series ablation (latest-vintage data with publication lags, 1978-2019 training):
  ICS_t = a + b_U U_t + b_pi pi_t + b_g g_t  [+ block P] [+ block B] [+ block R] + e_t
  - U_t: unemployment of month t-1 (out on the first Friday of t)
  - pi_t: headline PCE inflation, 12 months to month t-2 (out at the end of t-1)
  - g_t: real GDP growth, quarter on quarter annualised, latest quarter ending by month t-2 (advance estimate
    out about a month after the quarter), held flat; never interpolated
  - P_t: excess 5-year price rise over a 2% path, 100 ln(PCE_{t-2}/PCE_{t-62}) - 500 ln 1.02 (log points)
  - B_t: 30-year mortgage rate, latest weekly value by day 14 of t
  - R_t: 1 if a Republican is president on day 14 of t
  All 8 block combinations are fitted (EWC standard errors). For each: the 2026 mean gap (actual minus
  prediction, Jan-Oct 2026), the points of the baseline gap it closes, normal-times accuracy (train
  1978-2009, predict 2010-19) and post-2021 accuracy (train 1978-2019, predict Feb 2021-Dec 2025). Shapley
  values share the gap closed among the three blocks. Robustness: a 3-year price window; mortgage-payment
  growth instead of the rate level; training from 1985; Michigan's web-interview effect added back to the
  actuals; a real-time 1992-2019 sample with CPI inflation (the project's long panel).

Part B, regional check of the price-level block: BLS CPI for the four Census regions against Michigan
sentiment by region, with region and month fixed effects, so everything national (the economy, national
news, the survey's mode, the party in power) is absorbed and only regional differences in price paths
identify the effect. Driscoll-Kraay standard errors. Regional CPI is bimonthly before 1987 and Oct 2025 is
missing: log-linear interpolation, with a 1992-2026 check that needs none before 1987.

Part C, descriptive: falls by income third, and Michigan's own "why" answers in 2019 and 2026.

    python scripts/10c_ablation.py
Needs scripts 01, 04 and 10 to have run. Writes outputs/results_ablation.json and outputs/tables/ablation_*.csv.
"""
import _bootstrap  # noqa: F401
import itertools
import json
import math
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.config import OUTPUTS, PROCESSED, TABLES
from src.econ_model import fit
from src.fred import latest

warnings.filterwarnings("ignore")
OUT = {}
Y26 = pd.date_range("2026-01-01", "2026-10-01", freq="MS")
Y19 = pd.date_range("2019-01-01", "2019-12-01", freq="MS")
POST = pd.date_range("2021-02-01", "2025-12-01", freq="MS")      # after the COVID window, before the 2026 target
NORMAL = pd.date_range("2010-01-01", "2019-12-01", freq="MS")
COVID = pd.date_range("2020-03-01", "2021-01-01", freq="MS")

# ---------------------------------------------------------------- A. the long monthly panel
ics = pd.read_parquet(PROCESSED / "umich_indices.parquet")["ICS"]
un, pce, gdp, mort = (latest(s).dropna() for s in ["UNRATE", "PCEPI", "GDPC1", "MORTGAGE30US"])
months = pd.date_range("1978-01-01", "2026-10-01", freq="MS")
# presidents (inauguration Jan 20): party in office on day 14 of month t
TERMS = [("1977-01-20", "D"), ("1981-01-20", "R"), ("1993-01-20", "D"), ("2001-01-20", "R"), ("2009-01-20", "D"),
         ("2017-01-20", "R"), ("2021-01-20", "D"), ("2025-01-20", "R")]


def party(t):
    d = t + pd.Timedelta(days=13)
    p = None
    for start, prt in TERMS:
        if d >= pd.Timestamp(start):
            p = prt
    return p


def pay(r):
    i = r / 1200
    return i / (1 - (1 + i) ** -360)


rows = []
for t in months:
    day14 = t + pd.Timedelta(days=13)
    u = un.loc[:t - pd.DateOffset(months=1)].iloc[-1]                    # month t-1, or the last one published
    m2 = t - pd.DateOffset(months=2)
    q = gdp.loc[:t - pd.DateOffset(months=4)].index[-1]                  # quarter start <= t-4: quarter ended by t-2
    g = 100 * ((gdp[q] / gdp[q - pd.DateOffset(months=3)]) ** 4 - 1)
    r_now = mort.loc[:day14].iloc[-1]
    r_ago = mort.loc[:day14 - pd.DateOffset(months=12)].iloc[-1]
    rows.append({"month": t, "U": u, "pi": 100 * (pce[m2] / pce[m2 - pd.DateOffset(months=12)] - 1),
                 "g": g, "g_ref": q,
                 "P5": 100 * (math.log(pce[m2]) - math.log(pce[m2 - pd.DateOffset(months=60)])) - 500 * math.log(1.02),
                 "P3": 100 * (math.log(pce[m2]) - math.log(pce[m2 - pd.DateOffset(months=36)])) - 300 * math.log(1.02),
                 "B": r_now, "B_pay": 100 * math.log(pay(r_now) / pay(r_ago)), "R": float(party(t) == "R")})
L = pd.DataFrame(rows).set_index("month")
L["ICS"] = ics.reindex(L.index)
web = pd.Series(0.0, index=L.index)
web.loc["2024-04-01"], web.loc["2024-05-01"], web.loc["2024-06-01"] = 0.25, 0.5, 0.75
web.loc["2024-07-01":] = 1.0
L["ICS_mode_adj"] = L["ICS"] + 6.6 * web                                  # Michigan's own web-vs-phone estimate
L.drop(columns=["g_ref"]).to_csv(TABLES / "ablation_panel.csv")
assert L[["U", "pi", "g", "P5", "B", "R", "ICS"]].notna().all().all(), "gap in the long panel"

BASE = ["U", "pi", "g"]
BLOCKS = {"P": ["P5"], "B": ["B"], "R": ["R"]}


def run(cols, y="ICS", train=("1978-01-01", "2019-12-01"), data=L):
    d = data.loc[train[0]:train[1]]
    f = fit(d[y], d[cols])
    pred = sm.add_constant(data[cols], has_constant="add") @ f.params
    gap = data[y] - pred
    return f, pred, gap


def rmse(e):
    e = e.dropna()
    return float(np.sqrt((e ** 2).mean()))


def contrib(f, cols, data):
    """Shift of the 2026 prediction relative to 2019 caused by `cols` (index points), with a 90% CI."""
    dx = (data.loc[Y26, cols].mean() - data.loc[Y19, cols].mean()).values
    b = f.params[cols].values
    V = f.V.loc[cols, cols].values
    est, se = float(b @ dx), float(np.sqrt(dx @ V @ dx))
    tc = stats.t.ppf(0.95, f.nu)
    return {"points": est, "ci90": [est - tc * se, est + tc * se], "change_in_inputs": dict(zip(cols, map(float, dx)))}


def ablation(blocks=BLOCKS, y="ICS", train=("1978-01-01", "2019-12-01"), val_train=("1978-01-01", "2009-12-01"), data=L,
             base=BASE):
    res = {}
    for k in range(4):
        for combo in itertools.combinations(sorted(blocks), k):
            cols = base + sum((blocks[b] for b in combo), [])
            f, pred, gap = run(cols, y, train, data)
            fv, _, gv = run(cols, y, val_train, data)
            name = "".join(combo) or "base"
            res[name] = {"blocks": list(combo), "cols": cols, "N": int(f.nobs), "nu": f.nu, "R2": float(f.rsquared),
                         "coef": {c: {"b": float(f.params[c]), "se": float(f.bse[list(f.params.index).index(c)]),
                                      "p": float(f.pvalues[c])} for c in cols},
                         "gap2026": float(gap.loc[Y26].mean()), "pred2026": float(pred.loc[Y26].mean()),
                         "rmse_post_2021_25": rmse(gap.loc[POST]), "bias_post_2021_25": float(gap.loc[POST].mean()),
                         "rmse_normal_2010_19_oos": rmse(gv.loc[NORMAL]),
                         "block_contrib": {b: contrib(f, blocks[b], data) for b in combo}}
    b0 = res["base"]["gap2026"]
    for v in res.values():
        v["closed_points"] = v["gap2026"] - b0          # positive = the block closes the (negative) gap
        v["closed_share_of_base_gap"] = (v["gap2026"] - b0) / -b0
    # Shapley values of the three blocks for the gap closed and for the post-2021 RMSE reduction
    names = sorted(blocks)

    def val(S, key):
        nm = "".join(sorted(S)) or "base"
        return res[nm][key] - res["base"][key] if key == "gap2026" else res["base"][key] - res[nm][key]
    shap = {}
    for key in ["gap2026", "rmse_post_2021_25"]:
        phi = {}
        for i in names:
            others = [j for j in names if j != i]
            s = 0.0
            for k in range(len(others) + 1):
                for S in itertools.combinations(others, k):
                    w = math.factorial(len(S)) * math.factorial(len(names) - len(S) - 1) / math.factorial(len(names))
                    s += w * (val(set(S) | {i}, key) - val(set(S), key))
            phi[i] = s
        shap[key] = phi
    return res, shap


main, shap = ablation()
OUT["main"] = {"spec": "train 1978-01..2019-12 (latest-vintage data, publication lags), predict Jan-Oct 2026",
               "models": main, "shapley": shap}
# leave-one-out from the full model
OUT["main"]["leave_one_out"] = {b: main["BPR"]["gap2026"] - main["".join(sorted(set("BPR") - {b}))]["gap2026"] for b in "BPR"}

# sanity check: the same specification on 2010-19 gives a 2026 gap close to the real-time Model E (-39.9)
f10, _, g10 = run(BASE, train=("2010-01-01", "2019-12-01"))
OUT["check_2010_19_same_spec"] = {"gap2026": float(g10.loc[Y26].mean()), "coef": {c: float(f10.params[c]) for c in BASE},
                                  "note": "the project's Model E (real-time data) gives -39.9; this uses latest-vintage data"}
# can a 2010-19 model learn the price-level block at all?
fP10, _, gP10 = run(BASE + ["P5"], train=("2010-01-01", "2019-12-01"))
OUT["check_P_in_2010_19"] = {"P5_sd_2010_19": float(L.loc[NORMAL, "P5"].std()), "P5_sd_1978_2019": float(L.loc["1978":"2019", "P5"].std()),
                             "coef_P5": float(fP10.params["P5"]), "se_P5": float(fP10.bse[list(fP10.params.index).index("P5")]),
                             "gap2026": float(gP10.loc[Y26].mean())}
OUT["inputs_2019_vs_2026"] = {c: {"2019": float(L.loc[Y19, c].mean()), "2026": float(L.loc[Y26, c].mean())}
                              for c in ["U", "pi", "g", "P5", "P3", "B", "B_pay", "R"]}

# ---------------------------------------------------------------- A2. robustness
rob = {}
for label, kw in {
    "price window 3 years": {"blocks": {"P": ["P3"], "B": ["B"], "R": ["R"]}},
    "borrowing as payment growth": {"blocks": {"P": ["P5"], "B": ["B_pay"], "R": ["R"]}},
    "training from 1985": {"train": ("1985-01-01", "2019-12-01"), "val_train": ("1985-01-01", "2009-12-01")},
    "web-interview effect added back": {"y": "ICS_mode_adj"},
}.items():
    r, s = ablation(**kw)
    rob[label] = {"gap2026": {k: v["gap2026"] for k, v in r.items()}, "closed_points": {k: v["closed_points"] for k, v in r.items()},
                  "rmse_post_2021_25": {k: v["rmse_post_2021_25"] for k, v in r.items()},
                  "rmse_normal_2010_19_oos": {k: v["rmse_normal_2010_19_oos"] for k, v in r.items()},
                  "shapley_gap": s["gap2026"],
                  "coef_blocks": {k: {c: r[k]["coef"][c]["b"] for c in r[k]["cols"] if c not in BASE} for k in ["P", "B", "R", "BPR"]}}

# real-time 1992-2019 sample (the project's long panel: ALFRED U and GDP, CPI-U NSA inflation, as of day 14)
LP = pd.read_parquet(PROCESSED / "panel_long.parquet")[["U", "g_qoq", "pi_cpi", "mort30"]]
P = pd.read_parquet(PROCESSED / "panel_realtime_mid.parquet")
cpi = latest("CPIAUCNS")     # Oct 2025 was never published (shutdown): months that need it are left missing


def cpi_block(t, n):
    m = t - pd.DateOffset(months=2)
    a, b = cpi.get(m, np.nan), cpi.get(m - pd.DateOffset(months=12 * n), np.nan)
    return 100 * (np.log(a) - np.log(b)) - 100 * n * math.log(1.02)


O = P[["U", "g_qoq", "mort30"]].loc["2010-01-01":"2026-10-01"].copy()
O["pi_cpi"] = [100 * (cpi.get(t - pd.DateOffset(months=2), np.nan) / cpi.get(t - pd.DateOffset(months=14), np.nan) - 1) for t in O.index]
RT = pd.concat([LP.loc[:"2009-12-01"], O])
RT["P5"] = [cpi_block(t, 5) for t in RT.index]
RT["B"] = RT["mort30"]
RT["R"] = [float(party(t) == "R") for t in RT.index]
RT["U"], RT["pi"], RT["g"] = RT["U"], RT["pi_cpi"], RT["g_qoq"]
RT["ICS"] = ics.reindex(RT.index)
r_rt, s_rt = ablation(train=("1992-01-01", "2019-12-01"), val_train=("1992-01-01", "2009-12-01"), data=RT)
rob["real-time 1992-2019, CPI"] = {"gap2026": {k: v["gap2026"] for k, v in r_rt.items()},
                                    "closed_points": {k: v["closed_points"] for k, v in r_rt.items()},
                                    "rmse_post_2021_25": {k: v["rmse_post_2021_25"] for k, v in r_rt.items()},
                                    "rmse_normal_2010_19_oos": {k: v["rmse_normal_2010_19_oos"] for k, v in r_rt.items()},
                                    "shapley_gap": s_rt["gap2026"],
                                    "coef_blocks": {k: {c: r_rt[k]["coef"][c]["b"] for c in r_rt[k]["cols"] if c not in BASE}
                                                    for k in ["P", "B", "R", "BPR"]}}
OUT["robustness"] = rob

# ---------------------------------------------------------------- B. regional check of the price-level block
T = pd.read_parquet(PROCESSED / "umich_tables.parquet")
REG = {"NE": "CUUR0100SA0", "MW": "CUUR0200SA0", "S": "CUUR0300SA0", "W": "CUUR0400SA0"}
allm = pd.date_range("1966-12-01", "2026-09-01", freq="MS")
panel = []
reg_info = {}
for r, sid in REG.items():
    c = latest(sid, obs_start="1966-01-01").dropna()
    n_missing = int(allm.difference(c.index).size)
    lc = np.log(c.reindex(allm)).interpolate(method="time", limit_area="inside")   # bimonthly before 1987; Oct 2025
    reg_info[r] = {"months_interpolated": n_missing}
    for t in pd.date_range("1978-01-01", "2026-08-01", freq="MS"):
        m = t - pd.DateOffset(months=2)
        panel.append({"region": r, "month": t, "ICS": T.loc[t, f"ICS_{r}"] if t in T.index else np.nan,
                      "P5": 100 * (lc[m] - lc[m - pd.DateOffset(months=60)]) - 500 * math.log(1.02),
                      "cum_since_2019": np.nan})
RP = pd.DataFrame(panel).dropna(subset=["ICS", "P5"])
RP = RP[~RP["month"].isin(COVID)]
RP = RP[RP.groupby("month")["region"].transform("count") == 4]      # balanced: the within transformation needs it


def twoway(df, start, end=pd.Timestamp("2026-12-01"), drop_region=None):
    d = df[(df["month"] >= start) & (df["month"] <= end)].copy()
    if drop_region:
        d = d[d["region"] != drop_region]
    for v in ["ICS", "P5"]:   # two-way within transformation (balanced panel)
        d[v + "_w"] = d[v] - d.groupby("region")[v].transform("mean") - d.groupby("month")[v].transform("mean") + d[v].mean()
    x, y = d["P5_w"].values, d["ICS_w"].values
    b = float((x @ y) / (x @ x))
    e = y - b * x
    s = pd.Series(x * e, index=d["month"].values).groupby(level=0).sum().sort_index()   # score per month
    Tn = len(s)
    lag = int(math.floor(4 * (Tn / 100) ** (2 / 9)))
    S = float((s ** 2).sum())
    for l in range(1, lag + 1):
        S += 2 * (1 - l / (lag + 1)) * float((s.values[l:] * s.values[:-l]).sum())
    se = math.sqrt(S) / float(x @ x)
    return {"start": start, "N": int(len(d)), "months": Tn, "beta": b, "se_driscoll_kraay": se, "lag": lag,
            "p_two_sided": float(2 * (1 - stats.norm.cdf(abs(b / se))))}


reg = {"interpolation": reg_info, "fe_1983_2026": twoway(RP, pd.Timestamp("1983-01-01")),
       "fe_1992_2026": twoway(RP, pd.Timestamp("1992-01-01")),
       "fe_1983_2019_before_covid": twoway(RP, pd.Timestamp("1983-01-01"), pd.Timestamp("2019-12-01")),
       "fe_2021_2026_after_covid": twoway(RP, pd.Timestamp("2021-02-01")),
       "leave_one_region_out_1983_2026": {r: twoway(RP, pd.Timestamp("1983-01-01"), drop_region=r) for r in REG}}
# translate the regional slope into points for the national change in the price-level block, 2019 -> 2026
dP_nat = float(L.loc[Y26, "P5"].mean() - L.loc[Y19, "P5"].mean())
for k in ["fe_1983_2026", "fe_1992_2026"]:
    b, se = reg[k]["beta"], reg[k]["se_driscoll_kraay"]
    reg[k]["implied_points_for_national_2019_2026_change"] = {"points": b * dP_nat, "ci90": [(b - 1.645 * se) * dP_nat, (b + 1.645 * se) * dP_nat]}
# simple cross-section: change 2019 -> Jan-Aug 2026 by region
cs = []
for r in REG:
    d = RP[RP["region"] == r].set_index("month")
    cs.append({"region": r, "ICS_2019": float(d.loc["2019", "ICS"].mean()), "ICS_2026": float(d.loc["2026-01-01":"2026-08-01", "ICS"].mean()),
               "P5_2019": float(d.loc["2019", "P5"].mean()), "P5_2026": float(d.loc["2026-01-01":"2026-08-01", "P5"].mean())})
cs = pd.DataFrame(cs)
cs["dICS"], cs["dP5"] = cs["ICS_2026"] - cs["ICS_2019"], cs["P5_2026"] - cs["P5_2019"]
cs.to_csv(TABLES / "ablation_regions.csv", index=False)
reg["cross_section"] = cs.round(3).to_dict("records")
reg["cross_section_corr_dICS_dP5"] = float(cs[["dICS", "dP5"]].corr().iloc[0, 1])
reg["national_dP5_2019_2026"] = dP_nat
OUT["regional"] = reg

# ---------------------------------------------------------------- C. descriptive
inc = []
for k, lab in [("ICS_bottom", "bottom third"), ("ICS_middle", "middle third"), ("ICS_top", "top third")]:
    a, b = float(T.loc["2019", k].mean()), float(T.loc["2026-01-01":"2026-08-01", k].mean())
    inc.append({"group": lab, "2019": a, "2026_jan_aug": b, "change": b - a, "change_pct": 100 * (b / a - 1)})
OUT["income"] = inc
why = ["worse_prices", "worse_income", "dur_bad_prices_high", "dur_bad_rates_high", "dur_bad_cant_afford",
       "house_bad_prices_high", "house_bad_rates_high", "house_bad_cant_afford", "px_median"]
OUT["why_answers"] = {c: {"2019": float(T.loc["2019", c].mean()), "2026_jan_aug": float(T.loc["2026-01-01":"2026-08-01", c].mean())} for c in why}
pt = T[["ICS_DEM", "ICS_IND", "ICS_REP"]]
OUT["party_same_president_party"] = {"note": "a Republican was president in Feb 2017-2019 and in 2026",
                                     **{c: {"2017_19": float(pt.loc["2017-02-01":"2019-12-01", c].mean()),
                                            "2026_jan_aug": float(pt.loc["2026-01-01":"2026-08-01", c].mean())} for c in pt}}

# ---------------------------------------------------------------- write
tab = pd.DataFrame([{"model": k, "blocks": "+".join(v["blocks"]) or "economy only", "R2": v["R2"], "gap2026": v["gap2026"],
                     "closed_points": v["closed_points"], "closed_share": v["closed_share_of_base_gap"],
                     "rmse_post_2021_25": v["rmse_post_2021_25"], "bias_post_2021_25": v["bias_post_2021_25"],
                     "rmse_normal_2010_19_oos": v["rmse_normal_2010_19_oos"],
                     **{f"b_{c}": v["coef"][c]["b"] for c in v["cols"]}, **{f"p_{c}": v["coef"][c]["p"] for c in v["cols"]}}
                    for k, v in main.items()])
tab.to_csv(TABLES / "ablation_main.csv", index=False)
def _js(o):
    return float(o) if isinstance(o, (np.floating, np.integer)) else str(o)


(OUTPUTS / "results_ablation.json").write_text(json.dumps(OUT, indent=1, default=_js))
print(tab.round(3).to_string())
print(json.dumps({"shapley": shap, "leave_one_out": OUT["main"]["leave_one_out"], "check_2010_19": OUT["check_2010_19_same_spec"],
                  "check_P_2010_19": OUT["check_P_in_2010_19"], "inputs": OUT["inputs_2019_vs_2026"]}, indent=1, default=_js))
