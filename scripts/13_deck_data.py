"""Numbers and series for the presentation, read from the saved outputs (nothing is recomputed here).
    python scripts/13_deck_data.py && node presentation/build_deck.js
Writes presentation/deck_data.json.
"""
import _bootstrap  # noqa: F401
import json

import numpy as np
import pandas as pd

from src.config import OUTPUTS, PROCESSED, ROOT, TABLES

E = json.loads((OUTPUTS / "results_econ.json").read_text())
R = json.loads((OUTPUTS / "results.json").read_text())
V = pd.read_csv(TABLES / "val_tools_vs_gold.csv")
s = pd.read_csv(TABLES / "rq3_series_ICS.csv", index_col=0, parse_dates=True)
pred = s["fitted"].combine_first(s["pred"]).where(~s["covid_window"].astype(bool))
mech = pd.read_csv(TABLES / "rq4_mechanism_series.csv", index_col=0, parse_dates=True)
T = pd.read_parquet(PROCESSED / "umich_tables.parquet")
A = pd.read_csv(TABLES / "rq5_accuracy.csv")
acc = A[~A["dynamic"] & (A["subperiod"] == "all")].set_index("model")["rmse"]


def r(x, k=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), k)


v = V[V["subset"] == "all"].pivot_table(index="field", columns="tool", values="macro_f1")
wp = mech["worse_prices"].groupby(mech.index.year).mean()
party = T.loc["2024-08-01":"2025-03-01", ["ICS_DEM", "ICS_REP"]]
fam = {x["media"]: x for x in R["rq2"]["family"][::-1] if x["test"].startswith("level")}   # the level models
D = {
    "ics": {"labels": [d.strftime("%b %Y") for d in s.index], "actual": [r(x) for x in s["actual"]],
            "pred": [r(x) for x in pred]},
    "gap2026": r(E["E_ICS"]["mean_gap_2026"]), "ics2026": r(s.loc["2026-01-01":, "actual"].mean()),
    "pred2026": r(s.loc["2026-01-01":, "pred"].mean()), "ics_min": r(s["actual"].min()),
    "share_explained": r(100 * E["E_ICS"]["decomposition_2019_to_2026"]["share_explained"], 0),
    "share_lo": r(100 * E["E_ICS"]["decomposition_2019_to_2026"]["share_lo"], 0),
    "share_hi": r(100 * E["E_ICS"]["decomposition_2019_to_2026"]["share_hi"], 0),
    "null_lo": r(E["E_ICS"]["mean_gap_2026_test"]["null_lo"]), "null_hi": r(E["E_ICS"]["mean_gap_2026_test"]["null_hi"]),
    "f1": {k: {t: r(v.loc[k, t], 2) for t in ["opus", "tfidf_opus_trained", "tfidf_goldcv", "dictionary"]} for k in ["relevant", "tone"]},
    "selection": {k: r(R["rq1"]["selection"][k]["share_up"], 2) for k in ["falling", "rising"]},
    "selection_n": {k: [R["rq1"]["selection"][k]["inflation_up_items"], R["rq1"]["selection"][k]["inflation_down_items"]]
                    for k in ["falling", "rising"]},
    "asym_pi_p": r(R["rq1"]["asymmetry"]["TC_NEGNET|all"]["pi"]["p_one_sided"], 3),
    "asym_u_p": r(R["rq1"]["asymmetry"]["TC_NEGNET|all"]["U"]["p_one_sided"], 2),
    # conventional half-up rounding, as in the report (Python round() is half-to-even: 52.5 -> 52)
    "calib": int(100 * R["rq1"]["calibration"]["match_rate"] + 0.5),
    "calib_infl": int(100 * R["rq1"]["calibration"]["by_indicator"]["inflation"]["mean"] + 0.5),
    "media_contrib": r(fam["TC_NEGNET"]["implied_contribution_if_causal"]),
    "media_ci": [r(x) for x in fam["TC_NEGNET"]["implied_ci90"]],
    "media_q": r(fam["TC_NEGNET"]["bh_q"], 2),
    "mode_effect": -6.6,
    "ty_s_to_sf_q": r(R["rq2"]["toda_yamamoto"][3]["bh_q"], 3),
    "worse_prices": {"years": [int(y) for y in wp.index], "values": [r(x) for x in wp]},
    "anchor_r2": {k: r(R["rq4"]["anchoring_price_level"]["worse_prices"][f"R2_{k}"], 2) for k in ["pi", "pi36", "price_level_gap"]},
    "party": {"labels": [d.strftime("%b %y") for d in party.index], "dem": [r(x) for x in party["ICS_DEM"]],
              "rep": [r(x) for x in party["ICS_REP"]]},
    "rmse": {k: r(acc[k], 1) for k in ["m1", "m2", "m1b", "m3"]},
    "cw_m1_m2": r(R["rq5"]["clark_west"][0]["p_one_sided"], 3), "cw_m1b_m3": r(R["rq5"]["clark_west"][1]["p_one_sided"], 2),
    "cw_m1_m1b": r(R["rq5_exploratory_m1_vs_m1b"]["all"]["p_one_sided"], 4),
    "e1_p": [r(R["extras"][k]["p"], 2) for k in ["E1_h1_ICS", "E1_h1_gap", "E1_h3_ICS", "E1_h3_gap"]],
    "mode_share": r(100 * R["rq6"]["F6_ratio"], 0),
}
(ROOT / "presentation").mkdir(exist_ok=True)
(ROOT / "presentation" / "deck_data.json").write_text(json.dumps(D, indent=1))
print({k: v for k, v in D.items() if k not in ("ics", "worse_prices", "party")})
