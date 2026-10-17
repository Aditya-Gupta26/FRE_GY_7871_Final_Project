"""E7, EXPLORATORY (added after the main results; recorded as note 18): a fair split of the unexplained part of the
2026 gap among the suspects. One rule for every suspect:
  - out of sample: the suspect is added to an economy model that never sees 2026, and the drop in the Jan-Oct 2026
    gap is read off (index points closed);
  - order-free: Shapley values, i.e. each suspect's drop averaged over every order of adding the suspects, so no
    suspect gets credit for what another one carries;
  - uncertainty: 90% ranges from a moving-block bootstrap of the training months (12-month blocks, 500 draws).
Two bases, matching the slides:
  - strict (slide 10): trained on 1978-2019 (latest-vintage data, the ablation panel of scripts/10c), which includes
    the 1980s price and rate spikes, so the suspects can be learned. Suspects: price level (P5, the 5-year price rise
    above a 2%-a-year path), borrowing (B, 30-year mortgage rate), partisan mood (R, Republican president), inflation
    memory (R60, 5-year peak of inflation minus today's rate).
  - trained to 2025 (slide 11): the E6 model (2010-2025, COVID skipped; web-adjusted sentiment on the economy, six
    household costs and news). Suspects: price level (P5), partisan mood (R), inflation memory (R60); borrowing is
    already inside the household costs.
Plus one model-free check on partisan mood: a Republican was president in Feb 2017-2019 and in 2026, so the in-party's
own fall cannot be partisan; the equal-weight party average falling more than the in-party bounds the partisan part.
    python scripts/10f_suspects.py
Needs scripts 01, 10, 10c and 10d. Writes outputs/results_suspects.json.
"""
import _bootstrap  # noqa: F401
import itertools
import json
import math

import numpy as np
import pandas as pd

from src.config import END, OUTPUTS, PREREG, PROCESSED, TABLES

RNG = np.random.default_rng(7871)
REPS, BLOCK = 500, 12
Y26 = pd.date_range("2026-01-01", END, freq="MS")
COVID = pd.date_range("2020-03-01", "2021-01-01", freq="MS")
NAMES = {"P5": "price level", "B": "borrowing costs", "R": "partisan mood", "R60": "inflation memory"}


def gap_closed(y, X, train_idx, base, suspects, rows=None):
    """2026 gap of the base model and the points each subset of suspects closes (fit on the given training rows)."""
    tr = X.loc[train_idx] if rows is None else X.loc[train_idx].iloc[rows]
    yt = y.loc[train_idx] if rows is None else y.loc[train_idx].iloc[rows]
    out = {}
    for k in range(len(suspects) + 1):
        for sub in itertools.combinations(suspects, k):
            cols = base + list(sub)
            A = np.column_stack([np.ones(len(tr)), tr[cols].to_numpy()])
            b = np.linalg.lstsq(A, yt.to_numpy(), rcond=None)[0]
            pred = np.column_stack([np.ones(len(Y26)), X.loc[Y26, cols].to_numpy()]) @ b
            out[frozenset(sub)] = float((y.loc[Y26].to_numpy() - pred).mean())
    return out


def shapley(g, suspects):
    """Points of the gap closed by each suspect, averaged over every order (gaps are negative; closing raises them)."""
    n, val = len(suspects), {}
    for i in suspects:
        others = [s for s in suspects if s != i]
        tot = 0.0
        for k in range(n):
            for sub in itertools.combinations(others, k):
                w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
                tot += w * (g[frozenset(sub) | {i}] - g[frozenset(sub)])
        val[i] = tot
    return val


def blocks(n):
    starts = RNG.integers(0, n - BLOCK + 1, size=math.ceil(n / BLOCK))
    return np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]


def run(y, X, train_idx, base, suspects):
    g = gap_closed(y, X, train_idx, base, suspects)
    point = shapley(g, suspects)
    draws = []
    for _ in range(REPS):
        gb = gap_closed(y, X, train_idx, base, suspects, rows=blocks(len(train_idx)))
        draws.append(shapley(gb, suspects))
    D = pd.DataFrame(draws)
    D["all"] = D[suspects].sum(axis=1)
    rng = {c: [float(D[c].quantile(0.05)), float(D[c].quantile(0.95))] for c in D}
    return {"base_gap_2026": g[frozenset()], "gap_with_all": g[frozenset(suspects)],
            "closed": {s: {"name": NAMES[s], "points": point[s], "range90": rng[s]} for s in suspects},
            "closed_all": {"points": sum(point.values()), "range90": rng["all"]}, "N_train": len(train_idx)}


L = pd.read_csv(TABLES / "ablation_panel.csv", index_col=0, parse_dates=True)
L["R60"] = pd.read_csv(TABLES / "ratchet_panel.csv", index_col=0, parse_dates=True)["R60"]
OUT = {"rule": "out of sample (2026 never seen), Shapley over suspects, 90% block-bootstrap ranges"}
# strict basis: 1978-2019
TRs = L.loc["1978-01-01":"2019-12-01"].index
OUT["strict_1978_2019"] = run(L["ICS"], L, TRs, ["U", "pi", "g"], ["P5", "B", "R", "R60"])
# trained to 2025: the E6 model
MONTHS = pd.date_range("2010-01-01", END, freq="MS")
H1 = PREREG["h1_controls"]
P = pd.read_parquet(PROCESSED / "panel_realtime_mid.parquet")
S = pd.read_parquet(PROCESSED / "umich_indices.parquet")["ICS"].reindex(MONTHS)
web = pd.Series(0.0, index=MONTHS)
web.loc["2024-04-01"], web.loc["2024-05-01"], web.loc["2024-06-01"] = 0.25, 0.5, 0.75
web.loc["2024-07-01":] = 1.0
X = P[["U", "pi", "g_qoq"] + H1].join(pd.read_parquet(PROCESSED / "media_monthly.parquet")[["TC_NEGNET"]]).reindex(MONTHS)
X = X.join(L[["P5", "R", "R60"]])
y = S + 6.6 * web
TR25 = pd.date_range("2010-01-01", "2025-12-01", freq="MS").difference(COVID)
TR25 = TR25[X.loc[TR25].notna().all(axis=1).to_numpy() & y.loc[TR25].notna().to_numpy()]
OUT["trained_2010_2025"] = run(y, X, TR25, ["U", "pi", "g_qoq"] + H1 + ["TC_NEGNET"], ["P5", "R", "R60"])
# model-free partisan check (same president's party in Feb 2017-2019 and 2026)
A = json.loads((OUTPUTS / "results_ablation.json").read_text())["party_same_president_party"]
fall = {k: A[k]["2017_19"] - A[k]["2026_jan_aug"] for k in ["ICS_DEM", "ICS_IND", "ICS_REP"]}
OUT["partisan_model_free"] = {"fall_by_party": fall, "equal_weight_fall": float(np.mean(list(fall.values()))),
                              "in_party_fall": fall["ICS_REP"],
                              "upper_bound_partisan": float(np.mean(list(fall.values())) - fall["ICS_REP"]),
                              "note": "if partisan mood drove the fall, the in-party (Republicans in both periods) would not fall"}
(OUTPUTS / "results_suspects.json").write_text(json.dumps(OUT, indent=1))
for k in ["strict_1978_2019", "trained_2010_2025"]:
    o = OUT[k]
    print(f"{k}: base gap {o['base_gap_2026']:+.1f}, with all suspects {o['gap_with_all']:+.1f}, N {o['N_train']}")
    for s, v in o["closed"].items():
        print(f"   {v['name']:17s} closes {v['points']:+5.1f}  (90% range {v['range90'][0]:+.1f} to {v['range90'][1]:+.1f})")
    print(f"   all suspects      closes {o['closed_all']['points']:+5.1f}  (90% range {o['closed_all']['range90'][0]:+.1f} to {o['closed_all']['range90'][1]:+.1f})")
print("partisan, model-free:", {k: round(v, 1) for k, v in OUT["partisan_model_free"]["fall_by_party"].items()},
      "bound", round(OUT["partisan_model_free"]["upper_bound_partisan"], 1))
