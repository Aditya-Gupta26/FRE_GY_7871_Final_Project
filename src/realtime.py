"""Real-time monthly panel: for each survey month t, the economic data a forecaster had on the
prediction date (published strictly before day PREDICTION_DAY of month t, i.e. by day 14).

- U-3 and U-6: the latest month published by then, from that day's vintage.
- PCE inflation: 100 x (P_m / P_{m-12} - 1), both from the same vintage (the brief's formula);
  pi36 = 100 x (P_m / P_{m-36} - 1) is the cumulative 3-year price increase.
- Real GDP: the latest quarter published by then, QoQ SAAR (A191RL1Q225SBEA) and YoY from GDPC1
  (100 x (Y_q / Y_{q-4} - 1)), same vintage. GDP is a step function of releases: each month
  carries the latest published quarter, never an interpolated monthly value.
- Controls: real disposable income per capita YoY, debt-service ratio (latest quarter), the
  30-year mortgage rate (latest weekly reading), EPU (month t-1), the gas price (latest weekly).
Every value carries its reference period and its publication date, and the code asserts that
each publication date is on or before the prediction date. A latest-vintage twin of every
real-time value (same reference period) gives the revisions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import PREDICTION_DAY, SAMPLE_END, SAMPLE_START
from src.fred import asof, latest, vintages


def survey_months() -> pd.DatetimeIndex:
    return pd.date_range(f"{SAMPLE_START}-01", f"{SAMPLE_END}-01", freq="MS")


def info_date(t: pd.Timestamp, rule: str = "mid") -> pd.Timestamp:
    """mid: end of day 14 of month t (main). start: last day of month t-1 (robustness)."""
    if rule == "mid":
        return t + pd.Timedelta(days=PREDICTION_DAY - 2)
    return t - pd.Timedelta(days=1)


def _row_used(v: pd.DataFrame, obs: pd.Timestamp, when: pd.Timestamp) -> pd.Series:
    m = (v["date"] == obs) & (v["rt_start"] <= when) & (v["rt_end"] >= when)
    r = v.loc[m]
    assert len(r) == 1, (obs, when, len(r))
    return r.iloc[0]


def _ratio(s: pd.Series, m: pd.Timestamp, back: int, months: bool = True) -> float:
    prev = m - pd.DateOffset(months=back) if months else m - pd.DateOffset(months=3 * back)
    if prev not in s.index or pd.isna(s.get(prev)) or pd.isna(s.get(m)):
        return np.nan
    return 100 * (s[m] / s[prev] - 1)


def build_panel(rule: str = "mid") -> pd.DataFrame:
    V = {k: vintages(k) for k in ["UNRATE", "U6RATE", "PCEPI", "PCEPILFE", "CPIAUCSL",
                                  "A191RL1Q225SBEA", "GDPC1", "A229RX0", "TDSP", "PAYEMS"]}
    L = {k: latest(k) for k in V}
    mort, epu, gas = latest("MORTGAGE30US"), latest("USEPUINDXM"), latest("GASREGW")
    rows = []
    for t in survey_months():
        d = info_date(t, rule)
        r = {"month": t, "info_date": d}

        def last_obs(key):
            s = asof(V[key], d).dropna()
            return s, s.index.max()

        # unemployment (U-3), and U-6 for the same reference month
        s, m = last_obs("UNRATE")
        row = _row_used(V["UNRATE"], m, d)
        r.update(U=s[m], U_ref=m, U_pub=row.rt_start, U_latest=L["UNRATE"].get(m))
        s6 = asof(V["U6RATE"], d).dropna()
        if len(s6):
            m6 = m if m in s6.index else s6.index.max()
            r.update(U6=s6[m6], U6_ref=m6, U6_pub=_row_used(V["U6RATE"], m6, d).rt_start, U6_rt=True)
        else:   # ALFRED U6RATE vintages start Mar 4, 2011: latest vintage, flagged
            r.update(U6=L["U6RATE"].get(m), U6_ref=m, U6_pub=pd.NaT, U6_rt=False)
        u3m = 3   # 3-month change in U, same vintage (4 months if month m-3 is missing, e.g. Oct 2025)
        prev = m - pd.DateOffset(months=u3m)
        prev_avail = s.loc[:prev].dropna()
        r["dU3"] = s[m] - prev_avail.iloc[-1] if len(prev_avail) else np.nan

        # PCE inflation (headline, core), pi36; CPI YoY (robustness)
        for key, name in (("PCEPI", "pi"), ("PCEPILFE", "pi_core"), ("CPIAUCSL", "cpi")):
            s, m = last_obs(key)
            r[name] = _ratio(s, m, 12)
            r[f"{name}_ref"] = m
            r[f"{name}_pub"] = _row_used(V[key], m, d).rt_start
            r[f"{name}_latest"] = _ratio(L[key], m, 12)
            if key == "PCEPI":
                r["pi36"] = _ratio(s, m, 36)
                r["pi36_latest"] = _ratio(L[key], m, 36)
                prev = s.loc[: m - pd.DateOffset(months=12)].index
                r["dpi12"] = r["pi"] - (_ratio(s, prev[-1], 12) if len(prev) else np.nan)

        # real GDP growth, latest quarter published: QoQ SAAR = 100 x ((Y_q / Y_{q-1})^4 - 1) and
        # YoY = 100 x (Y_q / Y_{q-4} - 1), both from the same GDPC1 vintage. (ALFRED's own QoQ series,
        # A191RL1Q225SBEA, has vintages only from Sep 26, 2014; it is used to check this formula.)
        sy, q = last_obs("GDPC1")
        prev_q = q - pd.DateOffset(months=3)
        r.update(g_qoq=100 * ((sy[q] / sy[prev_q]) ** 4 - 1), g_ref=q,
                 g_pub=_row_used(V["GDPC1"], q, d).rt_start,
                 g_qoq_latest=100 * ((L["GDPC1"][q] / L["GDPC1"][prev_q]) ** 4 - 1))
        r["g_yoy"] = _ratio(sy, q, 4, months=False)
        r["g_yoy_latest"] = _ratio(L["GDPC1"], q, 4, months=False)
        sa = asof(V["A191RL1Q225SBEA"], d).dropna()
        r["g_qoq_bea"] = sa.get(q, np.nan)          # BEA's published rate, where ALFRED has it

        # controls
        s = asof(V["A229RX0"], d).dropna()
        if len(s):
            m = s.index.max()
            r.update(rdpi_yoy=_ratio(s, m, 12), rdpi_ref=m, rdpi_pub=_row_used(V["A229RX0"], m, d).rt_start,
                     rdpi_rt=True)
        else:   # ALFRED A229RX0 vintages start May 28, 2010: latest vintage, same lag as PCE, flagged
            m = r["pi_ref"]
            r.update(rdpi_yoy=_ratio(L["A229RX0"], m, 12), rdpi_ref=m, rdpi_pub=pd.NaT, rdpi_rt=False)
        s, q2 = last_obs("TDSP")
        r.update(dsr=s[q2], dsr_ref=q2, dsr_pub=_row_used(V["TDSP"], q2, d).rt_start)
        mo = mort.loc[:d].dropna()
        r.update(mort30=mo.iloc[-1], mort30_ref=mo.index[-1])
        ep = epu.loc[: t - pd.DateOffset(months=1)].dropna()
        r.update(epu=ep.iloc[-1], epu_ref=ep.index[-1])
        ga = gas.loc[:d].dropna()
        r.update(gas=ga.iloc[-1], gas_ref=ga.index[-1])
        ga12 = gas.loc[: d - pd.DateOffset(years=1)].dropna()
        r["gas_yoy"] = 100 * (ga.iloc[-1] / ga12.iloc[-1] - 1)
        rows.append(r)
    P = pd.DataFrame(rows).set_index("month")
    P["U6_gap"] = P["U6"] - P["U"]
    P["afford"] = affordability(P.index, P["mort30"], P["pi_ref"])
    # no look-ahead: every publication date on or before the prediction date
    for c in [c for c in P.columns if c.endswith("_pub")]:
        ok = P[c].isna() | (P[c] <= P["info_date"])   # NaT = latest-vintage fill, flagged (no vintage)
        assert ok.all(), f"look-ahead in {c}"
    for c in ["mort30_ref", "gas_ref"]:
        assert (P[c] <= P["info_date"]).all(), f"look-ahead in {c}"
    assert (P["epu_ref"] < P.index).all()
    return P


def affordability(months: pd.DatetimeIndex, mort30: pd.Series, income_ref: pd.Series) -> pd.Series:
    """Payment-to-income index (2019 mean = 100), latest-vintage inputs (flagged in the report).
    Payment on a constant-quality home: Case-Shiller HPI of month t-3 (published about two months
    after the reference month, so known by day 14 of t) x 0.8 (LTV) x the 30-year annuity factor at
    the mortgage rate known on the prediction date. Income: nominal disposable income per capita
    for the latest month whose PCE data were out (same release)."""
    hpi, inc = latest("CSUSHPINSA"), latest("A229RC0")
    out = {}
    for t, r, m in zip(months, mort30, income_ref):
        h = hpi.get(t - pd.DateOffset(months=3))
        i = r / 1200
        pay = 0.8 * h * i / (1 - (1 + i) ** -360) if h is not None and not np.isnan(h) else np.nan
        out[t] = pay / (inc.get(pd.Timestamp(m)) / 12)
    s = pd.Series(out)
    return 100 * s / s.loc["2019-01-01":"2019-12-01"].mean()


def build_long_panel() -> pd.DataFrame:
    """Long real-time sample (1992-01 to 2019-12) for identifying the H1 controls: U-3 and GDP from
    ALFRED vintages (GDP vintages start Dec 1991), inflation and pi36 from CPI-U NSA (never revised),
    the mortgage rate (not revised) and the affordability index (latest-vintage, flagged)."""
    from src.config import LONG_SAMPLE, LONG_VINTAGE_START
    VU = vintages("UNRATE", obs_start="1985-01-01", rt_start=LONG_VINTAGE_START)
    VG = vintages("GDPC1", obs_start="1985-01-01", rt_start=LONG_VINTAGE_START)
    cpi, mort = latest("CPIAUCNS"), latest("MORTGAGE30US")
    rows = []
    for t in pd.date_range(f"{LONG_SAMPLE[0]}-01", f"{LONG_SAMPLE[1]}-01", freq="MS"):
        d = info_date(t, "mid")
        su = asof(VU, d).dropna()
        m = su.index.max()
        sg = asof(VG, d).dropna()
        q = sg.index.max()
        # CPI for month m is released mid-month m+1: known by day 14 of t only if released by then;
        # conservatively use month t-2
        mc = t - pd.DateOffset(months=2)
        mo = mort.loc[:d].dropna()
        rows.append({"month": t, "U": su[m], "U_ref": m, "U_pub": _row_used(VU, m, d).rt_start,
                     "g_qoq": 100 * ((sg[q] / sg[q - pd.DateOffset(months=3)]) ** 4 - 1), "g_ref": q,
                     "g_pub": _row_used(VG, q, d).rt_start,
                     "g_yoy": 100 * (sg[q] / sg[q - pd.DateOffset(months=12)] - 1),
                     "pi_cpi": 100 * (cpi[mc] / cpi[mc - pd.DateOffset(months=12)] - 1),
                     "pi36_cpi": 100 * (cpi[mc] / cpi[mc - pd.DateOffset(months=36)] - 1),
                     "mort30": mo.iloc[-1], "info_date": d, "pi_ref": mc})
    P = pd.DataFrame(rows).set_index("month")
    for c in ("U_pub", "g_pub"):
        assert (P[c] <= P["info_date"]).all(), f"look-ahead in {c}"
    P["afford"] = affordability(P.index, P["mort30"], P["pi_ref"])
    return P
