"""RQ1, RQ2, RQ4, RQ5, RQ6, the three-explanation scorecard, the extra questions and the monitoring
numbers. Everything follows config.PREREG and its recorded notes.
    python scripts/10_analysis.py
Needs scripts 01, 04, 05, 07, 09 to have run. Writes outputs/results.json and outputs/tables/rq*_*.csv.
"""
import _bootstrap  # noqa: F401
import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multitest import multipletests

from src.coded import load_codes
from src.config import END, CODED, INTERIM, OUTPUTS, PREREG, PROCESSED, TABLES
from src.econ_model import fit, mean_gap_band, predict
from src.forecast import clark_west, diebold_mariano, expanding_nowcast, metrics
from src.fred import asof, latest, release_dates, vintages
from src.media import item_measures
from src.tests import (ar1, asymmetry, leave_one_year_out, mde_r, robustness_value, shapley2,
                       toda_yamamoto)

warnings.filterwarnings("ignore")
RES = {}
MONTHS = pd.date_range("2010-01-01", END, freq="MS")
COVID = pd.date_range("2020-03-01", "2021-01-01", freq="MS")
TR = slice("2010-01-01", "2019-12-01")
BASE = ["U", "pi", "g_qoq"]
H1 = PREREG["h1_controls"]

P = pd.read_parquet(PROCESSED / "panel_realtime_mid.parquet")
I = pd.read_parquet(PROCESSED / "umich_indices.parquet")
T = pd.read_parquet(PROCESSED / "umich_tables.parquet")
M = pd.read_parquet(PROCESSED / "media_monthly.parquet")
W = pd.read_parquet(PROCESSED / "media_weekly.parquet")
gm = pd.read_parquet(PROCESSED / "gap_main.parquet")
CODES = load_codes()   # not "C": patsy formulas use C(...)
K = pd.read_csv(CODED / "sample_key.csv", parse_dates=["date", "survey_month"])
X = CODES.merge(K, on="item_id")
S = I["ICS"].reindex(MONTHS)
keep = MONTHS.difference(COVID)
# Monthly media measures (the recorded deviation, PREREG_NOTES note 8): the primary monthly measure is the
# Opus-distilled TF-IDF series on the full corpus (Tier C); SF Fed is the pre-registered secondary.
# The own-Opus series is monthly only where covered (2026) and quarterly for history.
own = M["TC_NEGNET"]
own_bal = M["TC_INFL_BAL"]
own_opus_m = M["own_NEGNET"].where(M["own_covered"].fillna(False).astype(bool))
MQ = pd.read_parquet(PROCESSED / "media_quarterly.parquet")
sf = M["SFFED"]


def pres_party(d):
    d = pd.Timestamp(d)
    if d < pd.Timestamp("2017-01-20") or pd.Timestamp("2021-01-20") <= d < pd.Timestamp("2025-01-20"):
        return "D"
    return "R"


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        o = o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    if isinstance(o, (pd.Timestamp,)):
        return str(o.date())
    return o


# ===================================================================== RQ1
rq1 = {}
# (1) negativity asymmetry: coverage (own, SF Fed) and the public (ICS)
dX = {"U": P["dU3"].reindex(MONTHS), "pi": P["dpi12"].reindex(MONTHS)}
excl2021 = pd.date_range("2020-03-01", "2021-12-01", freq="MS")
asy = {}
for name, s in [("TC_NEGNET", own), ("SFFED_neg", -sf), ("ICS_pessimism", -S)]:
    for tag, drop in [("all", COVID), ("ex_2020_21", excl2021)]:
        idx = MONTHS.difference(drop)
        asy[f"{name}|{tag}"] = asymmetry(s.reindex(idx), {k: v.reindex(idx) for k, v in dX.items()})
rq1["asymmetry"] = asy

# (2) selection vs benchmarks
news = X[X["tier"].isin(["B_news", "A_news2026"]) & (X["relevant"] == "yes")].copy()
im = item_measures(news).join(news[["survey_month", "group", "date"]])
dpi1 = P["pi"].diff().reindex(MONTHS)
im["regime"] = im["survey_month"].map(lambda t: "falling" if dpi1.get(t, 0) < 0 else ("rising" if dpi1.get(t, 0) > 0 else "flat"))
sel = {}
for reg in ["falling", "rising"]:
    g = im[im["regime"] == reg]
    up, dn = g["infl_up"].sum(), g["infl_dn"].sum()
    sel[reg] = {"months": int(g["survey_month"].nunique()), "items": int(len(g)), "inflation_up_items": int(up),
                "inflation_down_items": int(dn), "ratio_up_to_down": float(up / dn) if dn else None,
                "share_up": float(up / (up + dn)) if up + dn else None}
# bootstrap over months for the falling-regime share
rng = np.random.default_rng(7871)
gm_ = im[im["regime"] == "falling"].groupby("survey_month")[["infl_up", "infl_dn"]].sum()
bs = []
for _ in range(2000):
    s_ = gm_.iloc[rng.integers(0, len(gm_), len(gm_))].sum()
    bs.append(s_["infl_up"] / (s_["infl_up"] + s_["infl_dn"]))
sel["falling"]["share_up_ci"] = [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]
jh, jl = latest("JTSHIL"), latest("JTSLDL")
jolts = (jl / (jl + jh)).rename("jolts_layoff_share")
TCI0 = pd.read_parquet(PROCESSED / "tierC_items.parquet")
TCI0 = TCI0[TCI0["tc_relevant"] == "yes"]
lay_m = TCI0.groupby(["survey_month", "group"])[["tc_layoffs", "tc_hiring"]].sum()
jbal = (lay_m["tc_layoffs"] / (lay_m["tc_layoffs"] + lay_m["tc_hiring"])).groupby(level=0).mean().rename("TC_JOB_BAL")
jb = jbal.to_frame().join(jolts.shift(2))     # JOLTS for month t-2 is out by the prediction date
jb = jb.reindex(keep).dropna()
sel["jobs"] = {"coverage_layoff_share_mean": float(jb["TC_JOB_BAL"].mean()), "jolts_layoff_share_mean": float(jb["jolts_layoff_share"].mean()),
               "corr_levels": float(jb.corr().iloc[0, 1]), "N": int(len(jb)),
               "pooled_layoff_items": int(im["lay"].sum()), "pooled_hiring_items": int(im["hire"].sum())}
pce = latest("PCEPI")
lp = np.log(pce)
tt = np.arange(len(lp))
mask = (lp.index >= "2010-01-01") & (lp.index <= "2019-12-01")
b = np.polyfit(tt[mask], lp.to_numpy()[mask], 1)
level_gap = pd.Series(100 * (lp.to_numpy() - (b[0] * tt + b[1])), index=lp.index).rename("price_level_gap")
ph = M["TC_SAL_prices_high"].to_frame().join(P[["pi", "pi36"]]).join(level_gap.shift(2)).reindex(keep).dropna()
sel["prices_high_salience_fit"] = {k: float(smf.ols(f"TC_SAL_prices_high ~ {k}", ph).fit().rsquared) for k in ["pi", "pi36", "price_level_gap"]}
sel["price_level_gap_2026_mean"] = float(level_gap.loc["2026-01-01":"2026-08-01"].mean())
rq1["selection"] = sel

# (3) release days: tone by released change; calibration
rel = X[(X["tier"] == "A_release") & (X["relevant"] == "yes")].copy()
cal = pd.read_csv(PROCESSED / "release_calendar.csv", parse_dates=["ref_period", "release_date"])
VU, VC = vintages("UNRATE"), vintages("CPIAUCSL")


# The change "as then published" (fix after the final review): U-3 as published (one decimal) minus the previous
# month as then published, rounded; CPI: BLS's headline 12-month change is from the NOT seasonally adjusted index,
# rounded to one decimal (NSA CPI is not revised, so the latest file gives the published values); the released
# month is the latest month in the SA vintage of the release date.
NSA = latest("CPIAUCNS")
NSA = NSA.reindex(pd.date_range(NSA.index.min(), NSA.index.max(), freq="MS"))
YOY_PUB = (100 * (NSA / NSA.shift(12) - 1)).round(1)
NSA_CORE = latest("CPILFENS")
NSA_CORE = NSA_CORE.reindex(pd.date_range(NSA_CORE.index.min(), NSA_CORE.index.max(), freq="MS"))
YOY_CORE_PUB = (100 * (NSA_CORE / NSA_CORE.shift(12) - 1)).round(1)


def released_change(kind, d):
    d = pd.Timestamp(d)
    if kind == "jobs":
        s = asof(VU, d).dropna()
        m = s.index.max()
        prev = s.loc[:m - pd.DateOffset(months=1)]
        return round(float(s[m] - prev.iloc[-1]), 1) if len(prev) else np.nan
    m = asof(VC, d).dropna().index.max()
    prev = YOY_PUB.loc[:m - pd.DateOffset(months=1)].dropna()
    return round(float(YOY_PUB[m] - prev.iloc[-1]), 1) if len(prev) and pd.notna(YOY_PUB.get(m)) else np.nan


rel["chg"] = [released_change(k, d) for k, d in zip(rel["release"], rel["release_date"])]
rel["neg"] = (rel["tone"] == "negative").astype(float)
rel["pos"] = (rel["tone"] == "positive").astype(float)
rel["bin"] = pd.cut(rel["chg"].round(2), [-10, -0.15, -0.05, 0.05, 0.15, 10], labels=["<=-0.2", "-0.1", "0", "+0.1", ">=+0.2"])
rd = rel.groupby(["release", "bin"], observed=True).agg(items=("neg", "size"), releases=("release_date", "nunique"),
                                                         neg=("neg", "mean"), pos=("pos", "mean"),
                                                         emo=("emotional", "mean")).reset_index()
rd.to_csv(TABLES / "rq1_release_bins.csv", index=False)
release_asym = {}
for kind in ["jobs", "cpi"]:
    r = rel[(rel["release"] == kind) & rel["bin"].notna()].copy()
    r["bin"] = r["bin"].astype(str)
    lpm = smf.ols("neg ~ C(bin, Treatment('0'))", r).fit(cov_type="cluster", cov_kwds={"groups": r["release_date"].astype("category").cat.codes})
    pr = {k: float(v) for k, v in lpm.params.items()}
    bad, good = "C(bin, Treatment('0'))[T.+0.1]", "C(bin, Treatment('0'))[T.-0.1]"
    if bad in lpm.params and good in lpm.params:
        L = np.zeros(len(lpm.params))
        L[list(lpm.params.index).index(bad)] = 1
        L[list(lpm.params.index).index(good)] = 1
        tt_ = lpm.t_test(L)
        release_asym[kind] = {"neg_shift_bad_0.1": pr[bad], "neg_shift_good_0.1": pr[good],
                              "asym_sum": float(tt_.effect[0]), "p_two_sided": float(tt_.pvalue),
                              "N_items": int(lpm.nobs), "releases": int(r["release_date"].nunique())}
    # noise band: emotional wording on changes inside sampling error (|dU| <= 0.1) vs larger
    if kind == "jobs":
        small = r["chg"].abs() <= 0.1 + 1e-9   # changes are rounded to 0.1 above
        release_asym["jobs_noise_band"] = {"emotional_small_changes": float(r.loc[small, "emotional"].mean()),
                                           "emotional_large_changes": float(r.loc[~small, "emotional"].mean()),
                                           "n_small": int(small.sum()), "n_large": int((~small).sum())}
rq1["release_days"] = release_asym

# calibration of numerical claims (all coded news items with non-forecast claims)
VP, VPC, VCC, VPAY, VG = (vintages("PCEPI"), vintages("PCEPILFE"), vintages("CPILFESL"), vintages("PAYEMS"), vintages("GDPC1"))


def candidates(ind, measure, d):
    d = pd.Timestamp(d)
    out = []
    if ind == "unemployment_rate":
        s = asof(VU, d).dropna()
        out = list(s.iloc[-2:].to_numpy())
    elif ind == "inflation":
        pools = {"CPI": [VC], "core CPI": [VCC], "PCE": [VP], "core PCE": [VPC]}.get(measure, [VC, VCC, VP, VPC])
        for V in pools:
            s = asof(V, d).dropna()
            yoy = (100 * (s / s.shift(12) - 1)).dropna()
            mom = (100 * (s / s.shift(1) - 1)).dropna()
            out += list(yoy.iloc[-2:].to_numpy()) + list(mom.iloc[-2:].to_numpy())
            out += [round(x, 1) for x in list(yoy.iloc[-2:]) + list(mom.iloc[-2:])]   # as published, one decimal
        # BLS's headline 12-month CPI changes come from the unadjusted indexes, rounded to one decimal (fix after
        # the second review: the SA-based candidates alone scored 5 exactly-published figures as wrong)
        m = asof(VC, d).dropna().index.max()
        for pub, ok in [(YOY_PUB, measure in ("CPI", "unspecified", "na")), (YOY_CORE_PUB, measure in ("core CPI", "unspecified", "na"))]:
            if ok:
                out += list(pub.loc[:m].dropna().iloc[-2:].to_numpy())
    elif ind == "payrolls":
        s = asof(VPAY, d).dropna()
        out = list(s.diff().dropna().iloc[-2:].to_numpy())
    elif ind == "gdp_growth":
        s = asof(VG, d).dropna()
        out = list((100 * ((s / s.shift(1)) ** 4 - 1)).dropna().iloc[-2:].to_numpy())
    return out


def tol(ind, v):
    """Pre-registered tolerance: +-0.1 pp for rates, +-1k for payrolls (values are in thousands)."""
    return (1.0 if ind == "payrolls" else 0.1) + 1e-9


def tol_rounding(ind, v):
    """Sensitivity: a claim stated as a round number matches within its rounding (e.g. "3%" for 3.2%,
    "200,000 jobs" for 187k). This looser rule was the one first coded; the pre-registered rule above is primary."""
    if ind == "payrolls":
        iv = int(round(abs(v)))
        z = len(str(iv)) - len(str(iv).rstrip("0")) if iv else 0
        return max(1.0, 0.5 * 10 ** z)
    return 0.1 if abs(v - round(v)) > 1e-9 else 0.5


calrows = []
allc = X[X["tier"].isin(["B_news", "A_news2026", "A_release"]) & (X["relevant"] == "yes") & (X["n_claims"] > 0)]
for _, r in allc.iterrows():
    for c in r["claims"]:
        if c.get("forecast") == 1:
            continue
        cand = candidates(c["indicator"], c.get("measure", "unspecified"), r["date"])
        v = float(c["value"])
        ok = any(abs(v - x) <= tol(c["indicator"], v) for x in cand)
        ok_r = any(abs(v - x) <= tol_rounding(c["indicator"], v) for x in cand)
        calrows.append({"item_id": r["item_id"], "date": r["date"], "group": r["group"], "tier": r["tier"],
                        "indicator": c["indicator"], "measure": c.get("measure"), "value": v, "match": ok,
                        "match_rounding": ok_r,
                        "nearest": float(min(cand, key=lambda x: abs(v - x))) if cand else np.nan})
CAL = pd.DataFrame(calrows)
CAL.to_csv(TABLES / "rq1_calibration_claims.csv", index=False)
rq1["calibration"] = {"claims": int(len(CAL)), "match_rate": float(CAL["match"].mean()) if len(CAL) else None,
                      "match_rate_rounding_rule": float(CAL["match_rounding"].mean()) if len(CAL) else None,
                      "by_indicator_rounding_rule": CAL.groupby("indicator")["match_rounding"].agg(["mean", "size"]).round(4).to_dict("index") if len(CAL) else {},
                      "by_indicator": CAL.groupby("indicator")["match"].agg(["mean", "size"]).round(4).to_dict("index") if len(CAL) else {},
                      "by_group": CAL.groupby("group")["match"].agg(["mean", "size"]).round(4).to_dict("index") if len(CAL) else {},
                      "measure_stated_share": float((CAL["measure"].isin(["CPI", "PCE", "core CPI", "core PCE"])).mean())
                      if len(CAL) else None}

# (4) attribution by lean x president's party (descriptive DiD)
im["pres"] = im["date"].map(pres_party)
att = im.groupby(["pres", "group"])[["BLAME_PRES", "CREDIT_PRES", "ATTR_ANY"]].mean().unstack()
att.to_csv(TABLES / "rq1_attribution.csv")
did = {}
for v in ["BLAME_PRES", "CREDIT_PRES"]:
    try:
        did[v] = float((att.loc["D", (v, "right")] - att.loc["D", (v, "left")]) - (att.loc["R", (v, "right")] - att.loc["R", (v, "left")]))
    except KeyError:
        did[v] = None
# bootstrap over survey months for the blame DiD
mm = im.groupby(["survey_month", "pres", "group"])["BLAME_PRES"].mean().unstack("group")
bs = []
months_ = mm.index.get_level_values(0).unique()
for _ in range(1000):
    pick = rng.choice(months_, len(months_))
    smp = pd.concat([mm.loc[m] for m in pick])
    g = smp.groupby(level=0).mean()
    try:
        bs.append((g.loc["D", "right"] - g.loc["D", "left"]) - (g.loc["R", "right"] - g.loc["R", "left"]))
    except KeyError:
        pass
did["BLAME_PRES_ci"] = [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]
did["n_items"] = att.shape
rq1["attribution"] = {"table": json.loads(att.round(4).to_json()), "did": did}

# descriptive: framing and narratives by year and source; Sacerdote-style LPM with month fixed effects
red = X[X["tier"].isin(["B_reddit", "A_reddit2026"]) & (X["relevant"] == "yes")]
ir = item_measures(red).join(red[["survey_month", "date"]]).assign(group="reddit")
both = pd.concat([im.assign(src="news"), ir.assign(src="reddit")])
both["year"] = pd.to_datetime(both["date"]).dt.year
fr = both.groupby(["src", "year"])[["NEGNET", "EMO", "LEVEL", "HH", "FC", "N1", "N2", "N3", "N4", "SAL_prices_high"]].mean()
fr.to_csv(TABLES / "rq1_framing_by_year.csv")
byg = both.groupby("group")[["neg", "pos", "NEGNET", "EMO", "LEVEL", "HH", "FC", "N1", "N2", "N3", "N4"]].mean()
byg.to_csv(TABLES / "rq1_by_source_group.csv")
lpm = smf.ols("neg ~ C(group, Treatment('center')) + C(survey_month)", both.assign(survey_month=both["survey_month"].astype(str))).fit(cov_type="HC1")
rq1["lpm_negative_by_group"] = {k.split("[T.")[1].rstrip("]"): {"coef": float(v), "p": float(lpm.pvalues[k])}
                                for k, v in lpm.params.items() if k.startswith("C(group")}
rq1["by_group"] = json.loads(byg.round(4).to_json(orient="index"))
# the same comparison split by the president's party (descriptive, added after the main results): month fixed effects
# within each regime, errors clustered by survey month; plus the regime difference of each source's gap (interaction)
bp = both.assign(survey_month=both["survey_month"].astype(str), pres=both["date"].map(pres_party))
bp["R"] = (bp["pres"] == "R").astype(int)
by_pres = {}
for prt in ["D", "R"]:
    d_ = bp[bp["pres"] == prt]
    f_ = smf.ols("neg ~ C(group, Treatment('center')) + C(survey_month)", d_).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d_["survey_month"])[0]})
    by_pres[prt] = {"items": int(len(d_)), "months": int(d_["survey_month"].nunique()),
                    "items_by_group": d_.groupby("group").size().astype(int).to_dict(),
                    "vs_center": {k.split("[T.")[1].rstrip("]"): {"coef": float(v), "se": float(f_.bse[k]), "p": float(f_.pvalues[k])}
                                  for k, v in f_.params.items() if k.startswith("C(group")}}
fi = smf.ols("neg ~ C(group, Treatment('center')) * R + C(survey_month)", bp).fit(
    cov_type="cluster", cov_kwds={"groups": pd.factorize(bp["survey_month"])[0]})
by_pres["R_minus_D"] = {k.split("[T.")[1].split("]")[0]: {"coef": float(v), "p": float(fi.pvalues[k])}
                        for k, v in fi.params.items() if k.startswith("C(group") and k.endswith(":R")}
rq1["lpm_negative_by_group_by_president"] = by_pres
# negativity by outlet lean under each president's party (descriptive; is "right is more negative" just
# "the opposition party's outlets are more negative"?), pooled coded news items
nb = im.assign(pres=im["date"].map(pres_party)).groupby(["pres", "group"])["neg"].agg(["mean", "size"])
rq1["neg_by_lean_and_president"] = {f"{a}|{b}": {"neg_share": float(v["mean"]), "n": int(v["size"])} for (a, b), v in nb.iterrows()}
RES["rq1"] = rq1

# ===================================================================== RQ2
rq2 = {}
D = pd.DataFrame({"S": S}).join(P[BASE + H1]).join(M[["TC_NEGNET", "TC_INFL_BAL", "SFFED", "EPU_news_lag1"]])
D = D.reindex(keep)
fam = []
for med, sign in [("TC_NEGNET", -1), ("SFFED", +1)]:
    d = D[["S"] + BASE + H1 + [med]].dropna()
    f = fit(d["S"], d[BASE + H1 + [med]])
    b, se, p2 = float(f.params[med]), float(f.bse[list(f.params.index).index(med)]), float(f.pvalues[med])
    t_ = b / se
    p1 = float(1 - stats.t.cdf(sign * t_, f.nu))
    d19 = M[med].loc["2019-01-01":"2019-12-01"].mean()
    d26 = M[med].loc["2026-01-01":END].mean()
    dm = float(d26 - d19)
    tc = stats.t.ppf(0.95, f.nu)
    lo_, hi_ = sorted([dm * (b - tc * se), dm * (b + tc * se)])
    loyo = leave_one_year_out(d["S"], d[BASE + H1 + [med]], med)
    d2 = d.loc[~d.index.year.isin([2021, 2022])]
    f2 = fit(d2["S"], d2[BASE + H1 + [med]])
    fam.append({"test": f"level: S on econ + H1 + {med}", "media": med, "N": int(f.nobs), "nu": f.nu, "coef": b, "se": se,
                "p_two_sided": p2, "p_expected_sign": p1, "expected_sign": sign,
                "implied_contribution_if_causal": b * dm, "implied_ci90": [lo_, hi_], "media_change_2019_2026": dm,
                # Cinelli-Hazlett RV is defined on the plain OLS t (fix after the final review), not the EWC t
                "robustness_value": robustness_value(float(f.ols.tvalues[med]), f.df_resid), "loyo_min_coef": loyo["min_coef"],
                "loyo_max_coef": loyo["max_coef"], "loyo_max_p": loyo["max_p"],
                "drop_2021_22_coef": float(f2.params[med]), "drop_2021_22_p": float(f2.pvalues[med])})
    # changes version: difference on the full monthly index, then drop COVID-window months (fix after the final
    # review: differencing after dropping them made 2021-02 a 12-month change)
    dd = pd.DataFrame({"S": S}).join(P[BASE]).join(M[[med]]).reindex(MONTHS).diff()
    dd = dd[dd.index.isin(keep) & (dd.index - pd.DateOffset(months=1)).isin(keep)].dropna()   # both months outside COVID
    fc = fit(dd["S"], dd[BASE + [med]])
    fam.append({"test": f"changes: dS on dU, dpi, dg, d{med}", "media": med, "N": int(fc.nobs), "coef": float(fc.params[med]),
                "p_two_sided": float(fc.pvalues[med]),
                "p_expected_sign": float(1 - stats.t.cdf(sign * fc.tvalues[med], fc.nu)), "expected_sign": sign})
# Toda-Yamamoto both directions with econ controls as exogenous terms
ty = []
exog = P[BASE].reindex(MONTHS)
for med in ["TC_NEGNET", "SFFED"]:
    x = (own if med == "TC_NEGNET" else sf).reindex(MONTHS).where(MONTHS.isin(keep))
    y = S.where(MONTHS.isin(keep))
    a = toda_yamamoto(y, x, exog=exog)
    b_ = toda_yamamoto(x, y, exog=exog)
    ty.append({"test": f"TY: {med} -> S", **a})
    ty.append({"test": f"TY: S -> {med}", **b_})
TY = pd.DataFrame(ty)
famdf = pd.DataFrame(fam)
# BH over the distinct hypotheses: the two level tests (expected-sign p) and the four TY tests
pv = list(famdf.loc[famdf["test"].str.startswith("level"), "p_expected_sign"]) + list(TY["p"])
q = multipletests(pv, alpha=0.10, method="fdr_bh")[1]
famdf.loc[famdf["test"].str.startswith("level"), "bh_q"] = q[:2]
TY["bh_q"] = q[2:]
famdf.to_csv(TABLES / "rq2_family.csv", index=False)
# the same level model WITHOUT the household costs (added after the main results, for the presentation): news then also
# gets credit for the price and rate pressures it reports, so this is the media-friendly upper case, not a test
d_nh = D[["S"] + BASE + ["TC_NEGNET"]].dropna()
f_nh = fit(d_nh["S"], d_nh[BASE + ["TC_NEGNET"]])
b_nh, se_nh = float(f_nh.params["TC_NEGNET"]), float(f_nh.bse[list(f_nh.params.index).index("TC_NEGNET")])
dm_nh = float(M["TC_NEGNET"].loc["2026-01-01":END].mean() - M["TC_NEGNET"].loc["2019-01-01":"2019-12-01"].mean())
tc_nh = stats.t.ppf(0.95, f_nh.nu)
rq2["level_without_household_TC_NEGNET"] = {
    "N": int(f_nh.nobs), "nu": f_nh.nu, "coef": b_nh, "se": se_nh, "p_expected_sign": float(stats.t.cdf(b_nh / se_nh, f_nh.nu)),
    "implied_contribution_if_causal": b_nh * dm_nh, "implied_ci90": sorted([dm_nh * (b_nh - tc_nh * se_nh), dm_nh * (b_nh + tc_nh * se_nh)]),
    "media_change_2019_2026": dm_nh}
# household costs in the same level model (added after the main results, for the presentation): coefficient x change in
# the 2019 and 2026 averages, as for the news; then news and household costs in the out-of-sample Model E (2010-19)
# that the 39.9-point gap comes from. Descriptive accounting, not a test.
d_lv = D[["S"] + BASE + H1 + ["TC_NEGNET"]].dropna()
f_lv = fit(d_lv["S"], d_lv[BASE + H1 + ["TC_NEGNET"]])
tc_lv = stats.t.ppf(0.95, f_lv.nu)
X_hh = pd.DataFrame({"S": S}).join(P[BASE + H1]).join(M[["TC_NEGNET"]])
dX_hh = X_hh.loc["2026-01-01":END].mean() - X_hh.loc["2019-01-01":"2019-12-01"].mean()


def _pts(f, cols, tc):   # coefficient x change summed over cols, with a 90% band from the EWC covariance
    g = dX_hh[cols].to_numpy()
    t = float(f.params[cols] @ g)
    se = float(np.sqrt(g @ f.V.loc[cols, cols].to_numpy() @ g))
    return {"points": t, "ci90": [t - tc * se, t + tc * se]}


rq2["level_household_contribution"] = {
    "household_all6": _pts(f_lv, H1, tc_lv), "housing_mort30_afford": _pts(f_lv, ["mort30", "afford"], tc_lv),
    "economy": _pts(f_lv, BASE, tc_lv), "news": _pts(f_lv, ["TC_NEGNET"], tc_lv),
    "by_cost": {c: {"coef": float(f_lv.params[c]), "change": float(dX_hh[c]), "points": float(f_lv.params[c] * dX_hh[c])} for c in H1},
    "fall_2019_2026": float(dX_hh["S"]), "N": int(f_lv.nobs)}
TR_E = slice("2010-01-01", "2019-12-01")
oos = {}
for k, cols in [("economy", BASE), ("plus_household", BASE + H1), ("plus_news", BASE + ["TC_NEGNET"]),
                ("plus_household_and_news", BASE + H1 + ["TC_NEGNET"])]:
    fe = fit(S.loc[TR_E], X_hh[cols].loc[TR_E])
    pe = sm.add_constant(X_hh[cols], has_constant="add") @ fe.params
    te = stats.t.ppf(0.95, fe.nu)
    oos[k] = {"gap_2026": float((S - pe).loc["2026-01-01":END].mean()),
              "household": _pts(fe, H1, te) if set(H1) <= set(cols) else None,
              "news": _pts(fe, ["TC_NEGNET"], te) if "TC_NEGNET" in cols else None}
rq2["model_e_2010_19_household_news"] = oos
# E6, EXPLORATORY (on request, after the main results): the same accounting with the model trained on 2010-2025 (COVID
# window skipped), still predicting Jan-Oct 2026 out of sample. Pieces are added in order, each the fall in the 2026 gap:
# the web switch (Michigan's 6.6 added back to sentiment in every web month, then refit), household costs, then news.
# The party mix stays the model-free comparison of averages. This model has seen 2021-2025, so part of the disconnect is
# already inside its coefficients.
web_sh = pd.Series(0.0, index=MONTHS)
web_sh.loc["2024-04-01"], web_sh.loc["2024-05-01"], web_sh.loc["2024-06-01"] = 0.25, 0.5, 0.75
web_sh.loc["2024-07-01":] = 1.0
TR25 = pd.date_range("2010-01-01", "2025-12-01", freq="MS").difference(COVID)
Y26m = pd.date_range("2026-01-01", END, freq="MS")
e6 = {}
for k, cols, web_adj in [("economy", BASE, False), ("web", BASE, True), ("web_household", BASE + H1, True),
                         ("web_household_news", BASE + H1 + ["TC_NEGNET"], True), ("household", BASE + H1, False),
                         ("news", BASE + ["TC_NEGNET"], False), ("household_news", BASE + H1 + ["TC_NEGNET"], False)]:
    y = (S + 6.6 * web_sh) if web_adj else S
    d6 = X_hh[cols].assign(y=y).reindex(TR25).dropna()
    f6 = fit(d6["y"], d6[cols])
    p6 = sm.add_constant(X_hh[cols], has_constant="add") @ f6.params
    t6 = stats.t.ppf(0.95, f6.nu)
    b6 = mean_gap_band(f6, X_hh[cols].reindex(Y26m), (y - p6).reindex(Y26m))   # 95% band of the 10-month mean gap
    e6[k] = {"N": int(f6.nobs), "gap_2026": float((y - p6).reindex(Y26m).mean()), "pred_2026": float(p6.reindex(Y26m).mean()),
             "gap_band95": [float(b6["lo"]), float(b6["hi"])], "coef": {c: float(f6.params[c]) for c in BASE},
             "economy": _pts(f6, BASE, t6), "household": _pts(f6, H1, t6) if set(H1) <= set(cols) else None,
             "news": _pts(f6, ["TC_NEGNET"], t6) if "TC_NEGNET" in cols else None}
rq2["e6_model_2010_25"] = e6
TY.to_csv(TABLES / "rq2_toda_yamamoto.csv", index=False)
# claim rule for H2 (Tier C NEGNET, the monthly primary after the deviation)
lev = famdf[famdf["test"].str.startswith("level") & (famdf["media"] == "TC_NEGNET")].iloc[0]
tyrow = TY[TY["test"] == "TY: TC_NEGNET -> S"].iloc[0]
claim = {"expected_sign": bool(lev["coef"] < 0), "bh_q_lt_0.10": bool(lev["bh_q"] < 0.10),
         "permutation_p_lt_0.10": bool(tyrow.get("p_perm", 1) < 0.10),
         "survives_h1_controls": bool(lev["p_expected_sign"] < 0.10),
         "survives_loyo": bool(lev["loyo_max_p"] < 0.10 and lev["loyo_max_coef"] < 0),
         "survives_drop_2021_22": bool(lev["drop_2021_22_p"] < 0.10 and lev["drop_2021_22_coef"] < 0)}
claim["passes"] = all(claim.values())
rq2["claim_rule_TC_NEGNET"] = claim
# the original own-Opus measure under its fallback rule: quarterly direct level test (covered quarters)
Qd = pd.DataFrame({"S": S}).join(P[BASE + H1]).reindex(keep)
Qd = Qd.groupby(Qd.index.to_period("Q").start_time).mean().join(MQ[["ownQ_NEGNET", "ownQ_covered"]])
Qd = Qd[Qd["ownQ_covered"].fillna(False).astype(bool)].dropna()
fq = fit(Qd["S"], Qd[BASE + H1 + ["ownQ_NEGNET"]])
fq0 = fit(Qd["S"], Qd[BASE + ["ownQ_NEGNET"]])
rq2["quarterly_own_opus"] = {"N_quarters": int(fq.nobs), "nu": fq.nu, "coef_with_H1": float(fq.params["ownQ_NEGNET"]),
                             "p_with_H1": float(fq.pvalues["ownQ_NEGNET"]), "coef_econ_only": float(fq0.params["ownQ_NEGNET"]),
                             "p_econ_only": float(fq0.pvalues["ownQ_NEGNET"])}
# out-of-sample gap version: expanding Model 1 errors 2017+ on media
ex1 = expanding_nowcast(S.reindex(keep), P[BASE].reindex(keep), first_origin="2017-01-01", train_start="2010-01-01")
# real-time Tier C: the value for month t from vintage t (classifier trained on codes published before day 15 of t;
# scripts/09b, fix after the final review); "own" is the full-sample Tier C series, kept as the first-run version
VT = pd.read_parquet(PROCESSED / "tierC_realtime.parquet")
VINT = {o: g.set_index("survey_month")[["TC_NEGNET", "TC_INFL_BAL"]].sort_index() for o, g in VT.groupby("origin")}
tc_rt = pd.Series({o: v.loc[o, "TC_NEGNET"] for o, v in VINT.items() if o in v.index}, name="own_rt")
g_oos = ex1["err"].to_frame("gap_oos").join(own.rename("own")).join(sf.rename("sf")).join(tc_rt).dropna()
for med in ["own_rt", "own", "sf"]:
    f = fit(g_oos["gap_oos"], g_oos[[med]])
    rq2[f"oos_gap_on_{med}"] = {"N": int(f.nobs), "coef": float(f.params[med]), "p": float(f.pvalues[med]),
                                "r": float(g_oos[["gap_oos", med]].corr().iloc[0, 1])}
rq2["mde"] = mde_r(len(g_oos), ar1(g_oos["gap_oos"]), ar1(g_oos["own"]))
rq2["family"] = famdf.to_dict("records")
rq2["toda_yamamoto"] = TY.to_dict("records")
# Reddit demand side: engagement on negativity, sub x month fixed effects
rd_ = red.copy()
rd_["neg"] = (rd_["tone"] == "negative").astype(float)
rr = pd.read_parquet(PROCESSED / "reddit_scores.parquet")   # text-free copy written by 09
rd_ = rd_.merge(rr, on="doc_id", suffixes=("", "_r"))
rd_["lscore"] = np.log1p(rd_["score"].astype(float))
rd_["cell"] = rd_["sub"].astype(str) + "_" + rd_["survey_month"].astype(str)
dm_ = smf.ols("lscore ~ neg + C(cell)", rd_).fit(cov_type="HC1")
rq2["reddit_demand"] = {"N": int(dm_.nobs), "coef_neg_log_score": float(dm_.params["neg"]), "p": float(dm_.pvalues["neg"]),
                        "note": "Arctic Shift scores are snapshots taken at different ages in different eras; within sub-month cells only"}
# party timing around the 2020 and 2024 elections: party sentiment (Table 5b) and the tone of left- vs
# right-leaning outlets (Tier C), Aug-Oct before vs Nov-Jan after each election (single months hold too few
# right-leaning items: 1 to 9 relevant a month in late 2020)
party = T[["ICS_DEM", "ICS_IND", "ICS_REP"]]
TCI = pd.read_parquet(PROCESSED / "tierC_items.parquet")
TCI = TCI[TCI["tc_relevant"] == "yes"]
TCI["NEGNET"] = (TCI["tc_tone"] == "negative").astype(float) - (TCI["tc_tone"] == "positive").astype(float)
pt = {}
for ev, (b0, b1, a0, a1) in {"2020": ("2020-08-01", "2020-10-01", "2020-11-01", "2021-01-01"),
                             "2024": ("2024-08-01", "2024-10-01", "2024-11-01", "2025-01-01")}.items():
    pre = TCI[(TCI["survey_month"] >= b0) & (TCI["survey_month"] <= b1)]
    post = TCI[(TCI["survey_month"] >= a0) & (TCI["survey_month"] <= a1)]
    pt[ev] = {"party_change_oct_to_dec": (party.loc[a0.replace("-11-", "-12-")] - party.loc[b1]).round(2).to_dict(),
              "outlet_tone_change": {g: {"pre": float(pre.loc[pre.group == g, "NEGNET"].mean()),
                                         "post": float(post.loc[post.group == g, "NEGNET"].mean()),
                                         "n_pre": int((pre.group == g).sum()), "n_post": int((post.group == g).sum())}
                                     for g in ["left", "right", "center", "local"]},
              "party_path": party.loc[b0:pd.Timestamp(a1) + pd.DateOffset(months=2)].round(1).to_dict(orient="index")}
rq2["party_timing"] = pt
RES["rq2"] = rq2

# ===================================================================== RQ4 mechanisms
rq4 = {}
nh = (T["news_unfav"] - T["news_fav"]).rename("net_unfav_recall")
rq4["recall_asymmetry"] = asymmetry(nh.reindex(keep), {k: v.reindex(keep) for k, v in dX.items()})
rec = M[["TC_SAL_prices_high"]].join(T[["unfav_high_prices", "fav_low_prices", "unfav_unemp", "fav_emp"]])
rec["media_price"] = rec["TC_SAL_prices_high"]
rc = rec.reindex(keep).dropna()
rq4["availability_recall_vs_media"] = {"N": int(len(rc)), "corr_levels": float(rc[["media_price", "unfav_high_prices"]].corr().iloc[0, 1]),
                                       "corr_changes": float(rc[["media_price", "unfav_high_prices"]].diff().corr().iloc[0, 1]),
                                       "ty_media_to_recall": toda_yamamoto(rec["unfav_high_prices"].reindex(MONTHS).where(MONTHS.isin(keep)),
                                                                           rec["media_price"].reindex(MONTHS).where(MONTHS.isin(keep)), perm=False),
                                       "ty_recall_to_media": toda_yamamoto(rec["media_price"].reindex(MONTHS).where(MONTHS.isin(keep)),
                                                                           rec["unfav_high_prices"].reindex(MONTHS).where(MONTHS.isin(keep)), perm=False)}
f_gas = fit(S.reindex(P.index).loc[TR], P[BASE + ["gas_yoy"]].loc[TR])
pr_gas = predict(f_gas, P[BASE + ["gas_yoy"]].loc["2026-01-01":END])
rq4["gas_beyond_pce"] = {"coef_gas_yoy": float(f_gas.params["gas_yoy"]), "p": float(f_gas.pvalues["gas_yoy"]),
                         "mean_gap_2026_with_gas": float((S.loc["2026-01-01":END] - pr_gas["pred"]).mean())}
anch = T[["worse_prices", "dur_bad_prices_high", "house_bad_prices_high"]].join(P[["pi", "pi36"]]).join(level_gap.shift(2))
an = {}
for yv in ["worse_prices", "dur_bad_prices_high"]:
    d = anch[[yv, "pi", "pi36", "price_level_gap"]].reindex(keep).dropna()
    an[yv] = {"N": int(len(d)), **{f"R2_{k}": float(smf.ols(f"{yv} ~ {k}", d).fit().rsquared) for k in ["pi", "pi36", "price_level_gap"]},
              "mean_2019": float(T[yv].loc["2019-01-01":"2019-12-01"].mean()), "mean_2022": float(T[yv].loc["2022-01-01":"2022-12-01"].mean()),
              "mean_2026": float(T[yv].loc["2026-01-01":"2026-08-01"].mean())}
rq4["anchoring_price_level"] = an
# monthly series behind the RQ4 figure (no results computed here)
anch.join(rec[["media_price", "unfav_high_prices"]]).join(nh).reindex(MONTHS).to_csv(TABLES / "rq4_mechanism_series.csv")
el = {}
for ev, (a, b) in {"2016": ("2016-10-01", "2016-12-01"), "2020": ("2020-10-01", "2020-12-01"), "2024": ("2024-10-01", "2024-12-01")}.items():
    try:
        el[ev] = (party.loc[b] - party.loc[a]).round(2).to_dict()
    except KeyError:
        el[ev] = "party data not monthly then"
rq4["partisan_election_jumps"] = el
rq4["fundamentals_change_oct_dec"] = {ev: {"dU": float(P.loc[b, "U"] - P.loc[a, "U"]), "dpi": float(P.loc[b, "pi"] - P.loc[a, "pi"])}
                                      for ev, (a, b) in {"2020": ("2020-10-01", "2020-12-01"), "2024": ("2024-10-01", "2024-12-01")}.items()}
RES["rq4"] = rq4

# ===================================================================== RQ5 prediction
rq5 = {}
Dm = pd.DataFrame({"S": S}).join(P[BASE + H1]).join(M[["TC_NEGNET", "TC_INFL_BAL", "SFFED", "DICT_NEGNET", "EPU_news_lag1"]])
Dm = Dm.reindex(keep)
specs = {"m1": BASE, "m1b": BASE + H1, "m2": BASE + ["TC_NEGNET", "TC_INFL_BAL"], "m3": BASE + H1 + ["TC_NEGNET", "TC_INFL_BAL"]}


TCCOLS = ["TC_NEGNET", "TC_INFL_BAL"]


def _roll(v: pd.Series, k: int) -> pd.Series:
    """Circular shift of the non-missing values by k (placebo for the joint null)."""
    a = v.to_numpy(float).copy()
    ok = ~np.isnan(a)
    a[ok] = np.roll(a[ok], k)
    return pd.Series(a, index=v.index)


def nowcasts(cols, dynamic=False, data=Dm, rolling=None, realtime=True, media_lag=0, shift=0):
    """Nowcasts from 2017-01, each fit only on months before the origin. If the spec uses Tier C and realtime is
    True (the default, fix after the final review), the Tier C columns at origin t are vintage t from 09b: the
    classifier trained on codes published before day 15 of t, applied to every month up to t. media_lag lags the
    Tier C columns one month; shift circularly shifts them (joint placebo). realtime=False reproduces the first run,
    which used the full-sample Tier C series (a look-ahead in the measurement)."""
    d0 = data.copy()
    cols = list(cols)
    if dynamic:
        d0["S_lag"] = S.shift(1).reindex(d0.index)
        cols = cols + ["S_lag"]
    uses_tc = any(c in TCCOLS for c in cols)
    out = []
    for t in d0.loc["2017-01-01":].index:
        d = d0
        if uses_tc:
            d = d0.copy()
            if realtime:
                if t not in VINT:
                    continue
                v = VINT[t].reindex(MONTHS)
            else:
                v = M[TCCOLS].reindex(MONTHS)
            if media_lag:
                v = v.shift(media_lag)
            v = v.reindex(d.index)
            if shift:
                v = v.apply(lambda c: _roll(c.loc[:t], shift).reindex(c.index))
            d[TCCOLS] = v[TCCOLS]
        dd = d[["S"] + cols].dropna()
        if t not in dd.index:
            continue
        lo = t - pd.DateOffset(months=rolling) if rolling else pd.Timestamp("2010-01-01")
        tr = dd.loc[lo:t - pd.DateOffset(months=1)]
        if len(tr) < (48 if rolling else 60):
            continue
        Xc = sm.add_constant(tr[cols], has_constant="add")
        bb = np.linalg.lstsq(Xc.to_numpy(), tr["S"].to_numpy(), rcond=None)[0]
        out.append({"month": t, "y": dd.loc[t, "S"], "pred": float(np.r_[1.0, dd.loc[t, cols].to_numpy(float)] @ bb)})
    r = pd.DataFrame(out).set_index("month")
    r["err"] = r["y"] - r["pred"]
    return r


fc_rows, cw_rows = [], []
for dyn in [False, True]:
    preds = {k: nowcasts(v, dyn) for k, v in specs.items()}
    common = preds["m1"].index
    for k in preds:
        common = common.intersection(preds[k].index)
    for k, r in preds.items():
        for sub, sl in [("all", slice(None)), ("2017-19", slice("2017-01-01", "2019-12-01")),
                        ("2021-26", slice("2021-02-01", END)), ("2026", slice("2026-01-01", END))]:
            fc_rows.append({"model": k, "dynamic": dyn, "subperiod": sub, **metrics(r.loc[common].loc[sl])})
    for a, b in [("m1", "m2"), ("m1b", "m3")]:
        cw = clark_west(preds[a].loc[common, "y"], preds[a].loc[common, "pred"], preds[b].loc[common, "pred"])
        cw_rows.append({"restricted": a, "unrestricted": b, "dynamic": dyn, **cw})
    if not dyn:
        RES["rq5_main_preds"] = {k: v.loc[common, "pred"].round(3).to_dict() for k, v in preds.items()}
        pd.DataFrame({k: v.loc[common, "pred"] for k, v in preds.items()}).join(preds["m1"].loc[common, "y"]).to_csv(TABLES / "rq5_nowcasts.csv")
        # EXPLORATORY (added after the main results; not pre-registered): do the household
        # controls alone improve the economy-only nowcast? m1 vs m1b, all months and 2021-02..2026-10
        c21 = common[(common >= "2021-02-01") & (common <= END)]
        RES["rq5_exploratory_m1_vs_m1b"] = {
            "all": clark_west(preds["m1"].loc[common, "y"], preds["m1"].loc[common, "pred"], preds["m1b"].loc[common, "pred"]),
            "2021_26": clark_west(preds["m1"].loc[c21, "y"], preds["m1"].loc[c21, "pred"], preds["m1b"].loc[c21, "pred"])}
# the first run used the full-sample Tier C series (look-ahead in the measurement); kept for disclosure only
for dyn in [False, True]:
    pf = {k: nowcasts(specs[k], dyn, realtime=False) for k in ["m1", "m2", "m1b", "m3"]}
    cmf = pf["m1"].index.intersection(pf["m2"].index).intersection(pf["m1b"].index).intersection(pf["m3"].index)
    for a, b in [("m1", "m2"), ("m1b", "m3")]:
        cw_rows.append({"restricted": a, "unrestricted": b, "dynamic": f"{dyn} (first run, full-sample Tier C)",
                        **clark_west(pf[a].loc[cmf, "y"], pf[a].loc[cmf, "pred"], pf[b].loc[cmf, "pred"])})
# rolling-window robustness (static)
rp = {k: nowcasts(v, rolling=84) for k, v in specs.items()}
cm = rp["m1"].index.intersection(rp["m2"].index).intersection(rp["m1b"].index).intersection(rp["m3"].index)
for a, b in [("m1", "m2"), ("m1b", "m3")]:
    cw_rows.append({"restricted": a, "unrestricted": b, "dynamic": "rolling84",
                    **clark_west(rp[a].loc[cm, "y"], rp[a].loc[cm, "pred"], rp[b].loc[cm, "pred"])})
# sensitivity grid (6 variants of the media block), static, CW vs model 1
grid_specs = {"SF Fed": ["SFFED"], "dictionary": ["DICT_NEGNET"], "tone only": ["TC_NEGNET"], "news EPU": ["EPU_news_lag1"]}


def grid(data, shift=0):
    hits, rows = 0, []
    base = nowcasts(BASE, data=data)
    for name, cols in grid_specs.items():
        r = nowcasts(BASE + cols, data=data, shift=shift)
        cmn = base.index.intersection(r.index)
        cw = clark_west(base.loc[cmn, "y"], base.loc[cmn, "pred"], r.loc[cmn, "pred"])
        rows.append({"variant": name, **cw})
        hits += cw["p_one_sided"] < 0.10
    # start-of-month information set and lag-1 media
    PS = pd.read_parquet(PROCESSED / "panel_realtime_start.parquet")
    d2 = data.copy()
    d2[BASE] = PS[BASE].reindex(d2.index)
    b2, r2 = nowcasts(BASE, data=d2), nowcasts(BASE + TCCOLS, data=d2, shift=shift)
    cmn = b2.index.intersection(r2.index)
    cw = clark_west(b2.loc[cmn, "y"], b2.loc[cmn, "pred"], r2.loc[cmn, "pred"])
    rows.append({"variant": "start-of-month information", **cw})
    hits += cw["p_one_sided"] < 0.10
    # lag-1 media (fix after the final review: the joint null now shifts this variant too)
    r3 = nowcasts(BASE + TCCOLS, data=data, media_lag=1, shift=shift)
    cmn = base.index.intersection(r3.index)
    cw = clark_west(base.loc[cmn, "y"], base.loc[cmn, "pred"], r3.loc[cmn, "pred"])
    rows.append({"variant": "lag-1 media", **cw})
    hits += cw["p_one_sided"] < 0.10
    return hits, rows


hits, grow = grid(Dm)
# joint shifted null: shift every media series by the same k (> 12 months), rebuild the grid
null_hits = []
media_cols = ["TC_NEGNET", "TC_INFL_BAL", "SFFED", "DICT_NEGNET", "EPU_news_lag1"]
for k in range(13, 60, 4):
    d = Dm.copy()
    for c in media_cols:
        v = d[c].to_numpy(float)
        ok = ~np.isnan(v)
        arr = np.full(len(v), np.nan)
        arr[ok] = np.roll(v[ok], k)
        d[c] = arr
    null_hits.append(grid(d, shift=k)[0])
rq5["grid"] = grow
# the pre-registered Reddit variant cannot be estimated: Reddit history coding was cut in the recorded deviation (note 8)
rq5["grid_reddit_variant"] = {"months_with_5plus_coded_relevant_posts": int((M["red_n_items"] >= 5).sum()),
                              "median_items_per_month": float(M["red_n_items"].median()),
                              "note": "not estimable; replaced by tone-only and news-EPU variants (recorded note in PREREG_NOTES)"}
rq5["grid_hits_p_lt_0.10"] = int(hits)
rq5["joint_null_hits"] = {"mean": float(np.mean(null_hits)), "share_ge_observed": float(np.mean(np.array(null_hits) >= hits)),
                          "draws": len(null_hits)}
# non-nested: own tone vs SF Fed, Opus vs dictionary, Opus vs Tier C (DM with HLN correction)
nn = []
base_m2 = nowcasts(BASE + ["TC_NEGNET"])
for name, cols in [("SF Fed", ["SFFED"]), ("dictionary", ["DICT_NEGNET"])]:
    r = nowcasts(BASE + cols)
    cmn = base_m2.index.intersection(r.index)
    dmr = diebold_mariano(base_m2.loc[cmn, "y"], base_m2.loc[cmn, "pred"], r.loc[cmn, "pred"])
    n_ = dmr["N"]
    hln = np.sqrt((n_ + 1 - 2 + 0) / n_)      # Harvey-Leybourne-Newbold factor for h = 1
    dmr["dm_t_hln"] = dmr["dm_t"] * hln
    dmr["p_hln"] = float(2 * (1 - stats.t.cdf(abs(dmr["dm_t_hln"]), n_ - 1)))
    nn.append({"tierC_vs": name, **dmr})
rq5["non_nested"] = nn
rq5["forecasts"] = fc_rows
rq5["clark_west"] = cw_rows
pd.DataFrame(fc_rows).to_csv(TABLES / "rq5_accuracy.csv", index=False)
pd.DataFrame(cw_rows).to_csv(TABLES / "rq5_clark_west.csv", index=False)
RES["rq5"] = rq5

# ===================================================================== Shapley: H1 and media blocks, 2026 mean gap closed
E = json.loads((OUTPUTS / "results_econ.json").read_text())
gap0 = E["E_ICS"]["mean_gap_2026"]
Dsh = pd.DataFrame({"S": S}).join(P[BASE + H1]).join(M[["TC_NEGNET", "TC_INFL_BAL"]])


def gap26(cols):
    d = Dsh[["S"] + cols].dropna()
    f = fit(d.loc[TR, "S"], d.loc[TR, cols])
    w = Dsh.loc["2026-01-01":END, cols].dropna()
    return float((Dsh.loc[w.index, "S"] - predict(f, w)["pred"]).mean())


vals = {"": gap26(BASE), "A": gap26(BASE + H1), "B": gap26(BASE + ["TC_NEGNET", "TC_INFL_BAL"]),
        "AB": gap26(BASE + H1 + ["TC_NEGNET", "TC_INFL_BAL"])}
closed = {k: 1 - v / vals[""] for k, v in vals.items()}
RES["shapley"] = {"gaps": vals, "closed": closed, "shapley_H1_media": shapley2(closed)}

# ===================================================================== RQ6 falsifiers and the scorecard
cwm = pd.DataFrame(cw_rows)
cw_static = cwm[cwm["dynamic"] == False]  # noqa: E712
F1 = (not claim["passes"]) and (cw_static["p_one_sided"] >= 0.10).all()
ty_s_to_m = TY[TY["test"] == "TY: S -> TC_NEGNET"].iloc[0]
F2 = bool(ty_s_to_m["bh_q"] < 0.10 and tyrow["bh_q"] >= 0.10)
a_own = asy["TC_NEGNET|all"]
F3 = {k: bool(a_own[k]["ci90"][0] <= 0) for k in ["U", "pi"]}
h1rows = {r["controls"]: r for r in E["h1_2010_19"]}
h1long = {r["controls"]: r for r in E["h1_long_1992_2019"]}
share_h1 = h1rows["+".join(H1)]["share_2026_gap_closed"]
share_h1_long = h1long["pi36_cpi+mort30+afford"]["share_2026_gap_closed"]
F4 = bool(share_h1 >= 0.5 and share_h1_long >= 0.5)
mode_effect = 6.6
F6 = bool(mode_effect >= abs(gap0))
r2_media = rq4["availability_recall_vs_media"]["corr_levels"] ** 2
r2_fund = float(smf.ols("unfav_high_prices ~ pi + pi36", T[["unfav_high_prices"]].join(P[["pi", "pi36"]]).reindex(keep).dropna()).fit().rsquared)
F7 = bool(r2_fund > r2_media)
RES["rq6"] = {"F1_no_media_effect_or_gain": bool(F1), "F2_sentiment_leads_media": F2, "F3_no_asymmetry": F3,
              "F4_h1_closes_gap": F4, "F4_shares": [share_h1, share_h1_long],
              "F5_party_timing": "see rq2.party_timing", "F6_mode_as_large_as_gap": F6, "F6_ratio": mode_effect / abs(gap0),
              "F7_recall_tracks_fundamentals_better": F7, "F7_R2": {"fundamentals": r2_fund, "media": r2_media}}
# scorecard
sh = RES["shapley"]["shapley_H1_media"]
h1_verdict = ("supported" if share_h1 >= 0.5 and share_h1_long >= 0.5 and h1rows["+".join(H1)]["wald_p_ewc"] < 0.05
              else "partly" if (0.25 <= share_h1 or 0.25 <= share_h1_long) else "not supported")
cw_main = cw_static[(cw_static["restricted"] == "m1") & (cw_static["unrestricted"] == "m2")].iloc[0]
media_share = sh["B"] / sh["total"] if sh["total"] > 0 else np.nan
h2_verdict = ("supported" if claim["passes"] and cw_main["p_one_sided"] < 0.10 and (media_share >= 0.25)
              else "partly" if (claim["passes"] or cw_main["p_one_sided"] < 0.10) else "not supported")
rev_share = E["h3_revision_effect_share"]
fixed, expd = E["expanding_vs_fixed_rmse_post"]["fixed"], E["expanding_vs_fixed_rmse_post"]["expanding"]
inst_intended = bool(min(E["rolling_sign_changes"].values()) > 0 and fixed > 1.25 * expd)
inst_literal = bool(min(E["rolling_sign_changes"].values()) > 0 and expd > 1.25 * fixed)
h3_hits = [mode_effect / abs(gap0) >= 0.25, rev_share >= 0.25, inst_intended]
h3_verdict = "supported" if sum(h3_hits) >= 2 else "partly" if sum(h3_hits) == 1 else "not supported"
RES["scorecard"] = {"H1": {"verdict": h1_verdict, "share_closed_2010_19": share_h1, "share_closed_long": share_h1_long},
                    "H2": {"verdict": h2_verdict, "claim_rule": claim["passes"], "cw_p_m1_vs_m2": float(cw_main["p_one_sided"]),
                           "media_shapley_share": media_share},
                    "H3": {"verdict": h3_verdict, "mode_share": mode_effect / abs(gap0), "revision_share": rev_share,
                           "instability_intended_rule": inst_intended, "instability_literal_rule": inst_literal,
                           "verdict_under_literal_rule": ("supported" if sum([h3_hits[0], h3_hits[1], inst_literal]) >= 2 else
                                                          "partly" if sum([h3_hits[0], h3_hits[1], inst_literal]) == 1 else "not supported")}}

# ===================================================================== extras
ex = {}
pc = latest("PCEC96")
g1 = 100 * (np.log(pc).diff()).rename("dc")
inc = P["rdpi_yoy"]
for h in [1, 3]:
    fut = (100 * (np.log(pc).shift(-h) - np.log(pc)) / h).rename("dc_fwd")
    d = pd.DataFrame({"dc_fwd": fut, "ICS": S, "gap": gm["gap"]}).join(P[BASE + ["rdpi_yoy"]]).join(g1.shift(1).rename("dc_lag"))
    d = d.reindex(keep).dropna(subset=["dc_fwd", "ICS", "dc_lag"] + BASE)
    for var in ["ICS", "gap"]:
        dd = d.dropna(subset=[var])
        f = fit(dd["dc_fwd"], dd[BASE + ["rdpi_yoy", "dc_lag", var]])
        ex[f"E1_h{h}_{var}"] = {"N": int(f.nobs), "coef": float(f.params[var]), "p": float(f.pvalues[var]),
                                "sample": [str(dd.index.min().date()), str(dd.index.max().date())]}
tcm = TCI.groupby(["survey_month", "group"])[["tc_prices_high", "tc_layoffs", "tc_hiring", "tc_inflation_down"]].mean().groupby(level=0).mean()
tab = tcm.join(T[["unfav_high_prices", "unfav_unemp", "fav_emp", "fav_low_prices"]]).reindex(keep)
e2 = []
for a, b in [("tc_prices_high", "unfav_high_prices"), ("tc_layoffs", "unfav_unemp"),
             ("tc_hiring", "fav_emp"), ("tc_inflation_down", "fav_low_prices")]:
    d = tab[[a, b]].dropna()
    e2.append({"media": a, "recall": b, "N": len(d), "r_levels": float(d.corr().iloc[0, 1]),
               "r_changes": float(d.diff().corr().iloc[0, 1])})
ex["E2_recall_vs_coverage"] = e2
RES["extras"] = ex

# ===================================================================== monitoring
mon = {}
web = pd.Series(0.0, index=MONTHS)
web.loc["2024-04-01"], web.loc["2024-05-01"], web.loc["2024-06-01"] = 0.25, 0.5, 0.75
web.loc["2024-07-01":] = 1.0
adj = S + 6.6 * web
mon["mode_adjusted_gap_2026"] = float((adj - gm["pred"].reindex(MONTHS)).loc["2026-01-01":END].mean())
yrs = {}
for y in range(2010, 2027):
    try:
        yrs[y] = float(gm.loc[f"{y}-10-01", "gap"] - gm.loc[f"{y}-06-01", "gap"]) if f"{y}-10-01" in gm.index.strftime("%Y-%m-%d") else None
    except KeyError:
        yrs[y] = None
fitted = gm["actual"] - gm["fitted"]
for y in range(2010, 2020):
    yrs[y] = float(fitted.loc[f"{y}-10-01"] - fitted.loc[f"{y}-06-01"])
mon["jun_to_oct_gap_change"] = yrs
mon["midterm_years_mean"] = float(np.mean([yrs[y] for y in [2010, 2014, 2018, 2022] if yrs.get(y) is not None]))
mon["other_years_mean"] = float(np.mean([v for y, v in yrs.items() if y not in [2010, 2014, 2018, 2022, 2026, 2020] and v is not None]))
mon["2026_jun_to_oct"] = yrs.get(2026)
# composition check: an equal-weighted mean of the three party indexes does not move with the partisan mix of
# respondents (Michigan notes the Republican share fell from Mar 2025)
pe = T[["ICS_DEM", "ICS_IND", "ICS_REP"]].mean(axis=1)
mon["party_equal_weight"] = {"mean_2017feb_2019": float(pe.loc["2017-02-01":"2019-12-01"].mean()),
                             "mean_2026_jan_aug": float(pe.loc["2026-01-01":"2026-08-01"].mean()),
                             "ics_2017feb_2019": float(S.loc["2017-02-01":"2019-12-01"].mean()),
                             "ics_2026_jan_aug": float(S.loc["2026-01-01":"2026-08-01"].mean())}
mon["party_2026"] = T.loc["2026-01-01":, ["ICS_DEM", "ICS_IND", "ICS_REP"]].round(1).to_dict(orient="index")
mon["weekly_last"] = W.tail(6)[["NEGNET", "SAL_prices_high", "n_items"]].round(3).to_dict(orient="index")
mon["media_2026"] = M.loc["2026-01-01":, ["own_NEGNET", "own_SAL_prices_high", "own_INFL_BAL", "TC_NEGNET", "SFFED", "own_n_items"]].round(3).to_dict(orient="index")
RES["monitoring"] = mon

(OUTPUTS / "results.json").write_text(json.dumps(clean(RES), indent=1, default=str, allow_nan=False))
print(json.dumps(clean({k: RES[k] for k in ["scorecard", "rq6", "shapley"]}), indent=1, default=str))
