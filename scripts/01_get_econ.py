"""Economic and survey baseline: vintages, the real-time panel, Michigan data, the SF Fed news
index, the release calendar, and checks of the course file and the official sources.
    python scripts/01_get_econ.py            (cached; add --refresh to re-pull FRED)
Writes data/processed/*.parquet|csv and outputs/tables/data_*.csv|json.
"""
import _bootstrap  # noqa: F401
import json
import sys

import numpy as np
import pandas as pd

from src.config import ALFRED_SERIES, FRED_LATEST_SERIES, PROCESSED, TABLES
from src.fred import latest, release_dates, vintages
from src.realtime import build_panel
from src.sources import bls_u3, course_file, sffed_daily
from src.umich import all_tables, indices

refresh = "--refresh" in sys.argv
PROCESSED.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)

# 1. vintages and latest values
V = {s: vintages(s, refresh=refresh) for s in ALFRED_SERIES}
L = {s: latest(s, refresh=refresh) for s in list(ALFRED_SERIES) + list(FRED_LATEST_SERIES)}

# 2. real-time panels (main: published before day 15 of the survey month; robustness: before day 1)
for rule in ("mid", "start"):
    P = build_panel(rule)
    P.to_parquet(PROCESSED / f"panel_realtime_{rule}.parquet")
    print(rule, "panel", P.shape)
P = pd.read_parquet(PROCESSED / "panel_realtime_mid.parquet")

# 3. Michigan
I = indices()
I.to_parquet(PROCESSED / "umich_indices.parquet")
T = all_tables()
T.to_parquet(PROCESSED / "umich_tables.parquet")
print("umich", I.shape, T.shape, "last table month", T.index.max().date())

# 4. SF Fed daily news sentiment
S = sffed_daily()
S.to_frame().to_parquet(PROCESSED / "sffed_daily.parquet")
print("sffed", S.index.min().date(), S.index.max().date())

# 5. release calendar: first publication of every reference period (from ALFRED)
cal = []
for s in ["UNRATE", "CPIAUCSL", "PCEPI", "GDPC1", "PAYEMS"]:
    r = release_dates(V[s]).reset_index().rename(columns={"date": "ref_period"})
    r = r[r["ref_period"] >= "2009-01-01"]
    r["series"] = s
    cal.append(r.rename(columns={"first_release": "release_date"}))
cal = pd.concat(cal)[["series", "ref_period", "release_date", "first_value"]]
cal.to_csv(PROCESSED / "release_calendar.csv", index=False)
print("release calendar rows", len(cal))

# 6. revisions: real-time value vs latest vintage, same reference period
rev = {}
for name, rt, lt in [("U-3 (pp)", "U", "U_latest"), ("PCE inflation YoY (pp)", "pi", "pi_latest"),
                     ("GDP QoQ SAAR (pp)", "g_qoq", "g_qoq_latest"), ("GDP YoY (pp)", "g_yoy", "g_yoy_latest"),
                     ("PCE 3-yr cumulative (pp)", "pi36", "pi36_latest")]:
    d = (P[lt] - P[rt]).dropna()
    rev[name] = {"N": int(len(d)), "mean_abs_revision": float(d.abs().mean()), "max_abs": float(d.abs().max()),
                 "share_nonzero_at_0.05": float((d.abs() > 0.05).mean())}
pd.DataFrame(rev).T.to_csv(TABLES / "data_revisions.csv")

# 7. timing: median lag of the reference period behind the survey month
lag = {k: P.index.to_period("M").astype(int) - pd.to_datetime(P[f"{k}_ref"]).dt.to_period("M").astype(int)
       for k in ["U", "pi", "rdpi"]}
lag["g (months from quarter start)"] = (P.index.to_period("M").astype(int)
                                        - pd.to_datetime(P["g_ref"]).dt.to_period("M").astype(int))
pd.DataFrame({k: pd.Series(v).value_counts().sort_index() for k, v in lag.items()}).to_csv(TABLES / "data_ref_lags.csv")

# 8. course file vs official latest vintage
C = course_file()
checks = {}
comp = {"unemployment": L["UNRATE"],
        "sentiment": I["ICS"],
        "pce_yoy": 100 * (L["PCEPI"] / L["PCEPI"].shift(12) - 1),
        "pce_yoy_vs_core": 100 * (L["PCEPILFE"] / L["PCEPILFE"].shift(12) - 1),
        "gdp_qoq": L["A191RL1Q225SBEA"]}
for k, ref in comp.items():
    c = C["pce_yoy" if k.startswith("pce") else k]
    j = pd.concat([c.rename("file"), ref.rename("official")], axis=1).dropna()
    d = j["file"] - j["official"]
    extra = sorted(set(c.index) - set(ref.dropna().index))
    checks[k] = {"N_overlap": int(len(j)), "max_abs_diff": float(d.abs().max()),
                 "n_diff_gt_0.05": int((d.abs() > 0.05).sum()),
                 "file_dates_not_in_official": [str(x.date()) for x in extra][-5:],
                 "file_last": str(c.index.max().date()), "official_last": str(ref.dropna().index.max().date())}
# missing months inside the file's own range
u = C["unemployment"]
full = pd.date_range(u.index.min(), u.index.max(), freq="MS")
checks["unemployment"]["missing_months_in_file"] = [str(x.date()) for x in full.difference(u.index)]
checks["gdp_qoq"]["gdpnow_latest_q3_2026"] = float(L["GDPNOW"].get(pd.Timestamp("2026-07-01"), np.nan))
(TABLES / "data_course_file_check.json").write_text(json.dumps(checks, indent=1))
print(json.dumps(checks, indent=1))

# 9. BLS API vs ALFRED UNRATE (latest)
b = bls_u3()
j = pd.concat([b, L["UNRATE"].rename("fred")], axis=1).dropna()
xc = {"N": int(len(j)), "max_abs_diff": float((j["bls_u3"] - j["fred"]).abs().max()),
      "bls_last": str(b.index.max().date())}
(TABLES / "data_bls_crosscheck.json").write_text(json.dumps(xc, indent=1))
print("BLS vs FRED UNRATE:", xc)
