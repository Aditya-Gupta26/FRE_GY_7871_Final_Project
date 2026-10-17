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
VJ = json.loads((OUTPUTS / "results_validation.json").read_text())
s = pd.read_csv(TABLES / "rq3_series_ICS.csv", index_col=0, parse_dates=True)
pred = s["fitted"].combine_first(s["pred"]).where(~s["covid_window"].astype(bool))
mech = pd.read_csv(TABLES / "rq4_mechanism_series.csv", index_col=0, parse_dates=True)
T = pd.read_parquet(PROCESSED / "umich_tables.parquet")
A = pd.read_csv(TABLES / "rq5_accuracy.csv")
acc = A[~A["dynamic"] & (A["subperiod"] == "all")].set_index("model")["rmse"]
TCK = json.loads((OUTPUTS / "results_tierc.json").read_text())
BYG = pd.read_csv(TABLES / "rq1_by_source_group.csv", index_col=0)
RD = json.loads((OUTPUTS / "results_reddit.json").read_text())
e3 = pd.read_csv(TABLES / "e3_reddit_monthly.csv", index_col=0, parse_dates=True)
e3q = e3[["RED_TC_NEGNET", "TC_NEGNET"]].groupby(e3.index.to_period("Q").start_time).mean()   # quarterly means for the chart
preds = R["rq5_main_preds"]
MAR = "2026-03-01 00:00:00"


def r(x, k=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), k)


def _h1(rows, key):   # mean 2026 gap of the H1 model whose controls are "base" or the all-costs model (contains "+")
    return [x for x in rows if (("+" in x["controls"]) if key == "+" else x["controls"] == key)][-1]["mean_gap_2026"]


v = V[V["subset"] == "all"].pivot_table(index="field", columns="tool", values="macro_f1")
MAIN = ["relevant", "tone", "emotional", "frame_price", "frame_unit", "frame_time", "attr_target", "attr_dir"]
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
    "kappa_models": [r(min(a["kappa"] for a in VJ["agreement_models_prereview"]), 2),
                     r(max(a["kappa"] for a in VJ["agreement_models_prereview"]), 2)],
    "n_disputed": VJ["n_items_any_disagreement"],
    "f1_opus_range": [r(v.loc[MAIN, "opus"].min(), 2), r(v.loc[MAIN, "opus"].max(), 2)],
    "corrections": {k: VJ["review_corrections"][k]["n_items"] for k in ["A", "B"]},
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
    "media_coef": r(fam["TC_NEGNET"]["coef"], 2), "media_change": r(fam["TC_NEGNET"]["media_change_2019_2026"], 3),
    "media_no_h1": {"coef": r(R["rq2"]["level_without_household_TC_NEGNET"]["coef"], 1),
                    "p": r(R["rq2"]["level_without_household_TC_NEGNET"]["p_expected_sign"], 3),
                    "contrib": r(R["rq2"]["level_without_household_TC_NEGNET"]["implied_contribution_if_causal"]),
                    "ci": [r(x) for x in R["rq2"]["level_without_household_TC_NEGNET"]["implied_ci90"]]},
    "mode_effect": -6.6,
    "ty_s_to_sf_q": r(R["rq2"]["toda_yamamoto"][3]["bh_q"], 3),
    "worse_prices": {"years": [int(y) for y in wp.index], "values": [r(x) for x in wp]},
    # what prices actually did, same years: % above the 2010-19 log-linear trend (PCE) and 12-month inflation (%)
    "prices_actual": {"level_gap": [r(x) for x in mech["price_level_gap"].groupby(mech.index.year).mean()],
                      "pi": [r(x) for x in mech["pi"].groupby(mech.index.year).mean()]},
    "anchor_r2": {k: r(R["rq4"]["anchoring_price_level"]["worse_prices"][f"R2_{k}"], 2) for k in ["pi", "pi36", "price_level_gap"]},
    "party": {"labels": [d.strftime("%b %y") for d in party.index], "dem": [r(x) for x in party["ICS_DEM"]],
              "rep": [r(x) for x in party["ICS_REP"]]},
    "rmse": {k: r(acc[k], 1) for k in ["m1", "m2", "m1b", "m3"]},
    "cw_m1_m2": r(R["rq5"]["clark_west"][0]["p_one_sided"], 3), "cw_m1b_m3": r(R["rq5"]["clark_west"][1]["p_one_sided"], 2),
    "cw_m1_m1b": r(R["rq5_exploratory_m1_vs_m1b"]["all"]["p_one_sided"], 4),
    "e1_p": [r(R["extras"][k]["p"], 2) for k in ["E1_h1_ICS", "E1_h1_gap", "E1_h3_ICS", "E1_h3_gap"]],
    "mode_share": r(100 * R["rq6"]["F6_ratio"], 0),
    # RQ4: negativity bias in coverage and in the public (per 1 pp move in published inflation)
    # change in ICS (index points) after a 1 pp rise and after a 1 pp fall; the test is run on pessimism = -ICS,
    # where resp_bad = b_up and resp_good = -b_down, so ICS moves -b_up after a rise and -b_down = resp_good after a fall
    "neg_public": {"rise": r(-R["rq1"]["asymmetry"]["ICS_pessimism|all"]["pi"]["resp_bad"]),
                   "fall": r(R["rq1"]["asymmetry"]["ICS_pessimism|all"]["pi"]["resp_good"]),
                   "p": r(R["rq1"]["asymmetry"]["ICS_pessimism|all"]["pi"]["p_one_sided"], 3)},
    # change in Tier C net negativity after a 1 pp rise (b_up) and after a 1 pp fall (b_down = -resp_good)
    "neg_cover": {"rise": r(R["rq1"]["asymmetry"]["TC_NEGNET|all"]["pi"]["resp_bad"], 3),
                  "fall": r(-R["rq1"]["asymmetry"]["TC_NEGNET|all"]["pi"]["resp_good"], 3)},
    "worse_prices_2019_2026": [int(R["rq4"]["anchoring_price_level"]["worse_prices"]["mean_2019"] + 0.5),
                               int(R["rq4"]["anchoring_price_level"]["worse_prices"]["mean_2026"] + 0.5)],   # half-up, as in the report
    # RQ5: March 2026 forecasts (index points)
    "mar26": {"actual": r(s.loc["2026-03-01", "actual"], 2), "modelE": r(s.loc["2026-03-01", "pred"], 2),
              **{k: r(preds[k][MAR], 2) for k in ["m1", "m2", "m1b", "m3"]}},   # 2 decimals: the slide shows differences
    "rmse_2026": {k: r(A[~A["dynamic"] & (A["subperiod"] == "2026")].set_index("model")["rmse"][k]) for k in ["m1", "m2", "m1b", "m3"]},
    # RQ6
    "f4_shares": [r(100 * x, 0) for x in R["rq6"]["F4_shares"]],
    "f7_r2": [r(R["rq6"]["F7_R2"]["fundamentals"], 2), r(R["rq6"]["F7_R2"]["media"], 2)],
    "mode_gap": r(R["monitoring"]["mode_adjusted_gap_2026"]),
    # E3 Reddit (exploratory)
    "e3": {"posts": RD["corpus"]["posts_scored"], "relevant": RD["corpus"]["posts_relevant"],
           "median_month": r(RD["corpus"]["median_relevant_per_month"], 0),
           "coef_econ": r(RD["level_models"][0]["coef"]), "p_econ": r(RD["level_models"][0]["p_expected_sign"], 2),
           "coef_h1": r(RD["level_models"][1]["coef"]), "p_h1": r(RD["level_models"][1]["p_expected_sign"], 2),
           "contrib_h1": r(RD["level_models"][1]["implied_contribution_if_causal"]),
           "ci_h1": [r(x) for x in RD["level_models"][1]["implied_ci90"]],
           "contrib_econ": r(RD["level_models"][0]["implied_contribution_if_causal"]),
           "ci_econ": [r(x) for x in RD["level_models"][0]["implied_ci90"]],
           "ty": [r(RD["toda_yamamoto"]["reddit_to_sentiment"]["p"], 2), r(RD["toda_yamamoto"]["sentiment_to_reddit"]["p"], 2)],
           "gold_rel": r(RD["reddit_gold"]["relevant_macro_f1"], 2), "gold_tone": r(RD["reddit_gold"]["tone_macro_f1"], 2),
           "opus_tone": r(RD["reddit_gold"]["opus_tone_macro_f1_reddit_relevant"], 2),   # same 59 relevant items as Tier C
           "change": r(RD["reddit_change_2019_2026"]["change"], 2), "split_half": r(RD["corpus"]["split_half"]["spearman_brown"], 2),
           "p_changes": r(RD["changes"]["p_two_sided"], 2),
           "r_news": r(RD["corpus"]["corr_with_news_tierC"]["r_levels"], 2),
           "series": {"labels": [d.strftime("%Y") if d.month == 1 else "" for d in e3q.index],
                      "reddit": [r(x, 3) for x in e3q["RED_TC_NEGNET"]], "news": [r(x, 3) for x in e3q["TC_NEGNET"]]}},
    # Tier C training and validation
    "tierc": {"rows": [{"name": x["classifier"], "train": r(x["train_macro_f1"], 2), "cv": r(x["cv_macro_f1"], 2),
                        "gold": r(x["gold_macro_f1"], 2)} for x in TCK["classifiers"]],
              "n_train": TCK["training_items"], "r_opus_q": r(TCK["agreement_with_opus_quarterly"]["TC_NEGNET"]["r_levels"], 2),
              "r_opus_q_prices": r(TCK["agreement_with_opus_quarterly"]["TC_prices_high"]["r_levels"], 2)},
    # honourable mentions
    "retest_tone": r(VJ["test_retest"]["tone"]["kappa"], 2),
    "variants_range": [r(min(v.get("mean_gap_2026", v.get("mean_gap_2026_Q1_Q3")) for v in E["variants"].values())),
                       r(max(v.get("mean_gap_2026", v.get("mean_gap_2026_Q1_Q3")) for v in E["variants"].values()))],
    "party_eq": [r(R["monitoring"]["party_equal_weight"]["mean_2017feb_2019"]), r(R["monitoring"]["party_equal_weight"]["mean_2026_jan_aug"]),
                 r(R["monitoring"]["party_equal_weight"]["ics_2017feb_2019"]), r(R["monitoring"]["party_equal_weight"]["ics_2026_jan_aug"])],
    "midterm": [r(R["monitoring"]["midterm_years_mean"]), r(R["monitoring"]["other_years_mean"]), r(R["monitoring"]["2026_jun_to_oct"])],
    "placebo_hits": r(R["rq5"]["joint_null_hits"]["mean"], 2),
    # RQ1 by source: share of relevant Opus-labelled items that are negative (2010-2026 pooled), and the same-month
    # difference from center outlets (linear probability model with month fixed effects)
    # RQ1 asymmetry, three panels: change in negativity after bad news and after good news
    # (monthly Tier C net negativity per 1 pp for inflation and unemployment: after a rise = b_up = resp_bad,
    # after a fall = -b_down... = -resp_good; jobs-report days: change in the share of that day's headlines that are
    # negative after a 0.1 pp rise or fall in unemployment, against an unchanged report)
    "asym3": {"inflation": {"bad": r(R["rq1"]["asymmetry"]["TC_NEGNET|all"]["pi"]["resp_bad"], 3),
                            "good": r(-R["rq1"]["asymmetry"]["TC_NEGNET|all"]["pi"]["resp_good"], 3),
                            "p": r(R["rq1"]["asymmetry"]["TC_NEGNET|all"]["pi"]["p_one_sided"], 3)},
              "unemployment": {"bad": r(R["rq1"]["asymmetry"]["TC_NEGNET|all"]["U"]["resp_bad"], 2),
                               "good": r(-R["rq1"]["asymmetry"]["TC_NEGNET|all"]["U"]["resp_good"], 2),
                               "p": r(R["rq1"]["asymmetry"]["TC_NEGNET|all"]["U"]["p_one_sided"], 2)},
              "jobs_days": {"bad": r(R["rq1"]["release_days"]["jobs"]["neg_shift_bad_0.1"], 3),
                            "good": r(R["rq1"]["release_days"]["jobs"]["neg_shift_good_0.1"], 3),
                            "p": r(R["rq1"]["release_days"]["jobs"]["p_two_sided"], 2)}},
    "by_source": {g: int(100 * float(BYG.loc[g, "neg"]) + 0.5) for g in ["left", "center", "local", "right", "reddit"]},
    "by_source_vs_center": {g: {"pts": r(100 * v["coef"]), "p": v["p"]} for g, v in R["rq1"]["lpm_negative_by_group"].items()},
    "by_source_by_president": {prt: {g: {"pts": r(100 * v["coef"]), "p": v["p"]}
                                     for g, v in R["rq1"]["lpm_negative_by_group_by_president"][prt]["vs_center"].items()}
                               for prt in ["D", "R"]},
    "by_source_R_minus_D": {g: {"pts": r(100 * v["coef"]), "p": v["p"]}
                            for g, v in R["rq1"]["lpm_negative_by_group_by_president"]["R_minus_D"].items()},
    # the 2026 gap (index points). The gap must be out of sample (the brief), so only the two survey pieces, which need
    # no model, are subtracted; news and household costs depend on the training years and are listed as explanations
    "drop": {"fall": r(-E["E_ICS"]["decomposition_2019_to_2026"]["actual_change"]),
             "economy": r(-E["E_ICS"]["decomposition_2019_to_2026"]["predicted_change"]),
             "gap": r(-E["E_ICS"]["mean_gap_2026"]),
             "web": 6.6,
             "party_mix": r((R["monitoring"]["party_equal_weight"]["ics_2017feb_2019"] - R["monitoring"]["party_equal_weight"]["ics_2026_jan_aug"])
                            - (R["monitoring"]["party_equal_weight"]["mean_2017feb_2019"] - R["monitoring"]["party_equal_weight"]["mean_2026_jan_aug"])),
             # the 39.9 already uses the data people saw on day 14 (real-time); on final, revised data the gap would be
             # bigger (41.0), so revisions explain none of the 39.9 and are not subtracted from it below
             "revisions": r(-E["E_ICS"]["mean_gap_2026"] * E["h3_revision_effect_share"]),
             "gap_final_data": r(-E["variants"]["revised_data"]["mean_gap_2026"]),
             # household costs (H1): points of the 2026 gap they close when added (negative = they widen it): all six in
             # the 2010-19 model, and the three-cost model in the 1992-2019 long sample against its own base
             "household": [r(_h1(E["h1_2010_19"], "+") - E["E_ICS"]["mean_gap_2026"]),
                           r(_h1(E["h1_long_1992_2019"], "+") - _h1(E["h1_long_1992_2019"], "base"))],
             "news": r(-fam["TC_NEGNET"]["implied_contribution_if_causal"]),
             # coefficient x change, points of the 2019-2026 fall (positive = explains part of the fall): the slide 6 model
             # (2010-2026, in sample) and the out-of-sample Model E (2010-19) the 39.9 comes from
             "in_sample": {k: {"pts": r(-v["points"]), "ci": sorted([r(-x) for x in v["ci90"]])}
                           for k, v in R["rq2"]["level_household_contribution"].items() if isinstance(v, dict) and "points" in v},
             "afford_change": r(R["rq2"]["level_household_contribution"]["by_cost"]["afford"]["change"], 0),
             "oos": {"household": r(-R["rq2"]["model_e_2010_19_household_news"]["plus_household"]["household"]["points"]),
                     "gap_household": r(-R["rq2"]["model_e_2010_19_household_news"]["plus_household"]["gap_2026"]),
                     "news": r(-R["rq2"]["model_e_2010_19_household_news"]["plus_news"]["news"]["points"]),
                     "gap_news": r(-R["rq2"]["model_e_2010_19_household_news"]["plus_news"]["gap_2026"])},
             "overshoot_m1_m1b": [r(-A[~A["dynamic"] & (A["subperiod"] == "2026")].set_index("model")["bias"][k]) for k in ["m1", "m1b"]]},
}
_pe = R["monitoring"]["party_equal_weight"]
D["drop"]["rest"] = r(-E["E_ICS"]["mean_gap_2026"] - 6.6
                      - ((_pe["ics_2017feb_2019"] - _pe["ics_2026_jan_aug"]) - (_pe["mean_2017feb_2019"] - _pe["mean_2026_jan_aug"])), 2)
# from unrounded pieces: the gap minus the web switch and the party mix only
# E6: the same accounting with the model trained on 2010-2025, pieces added in order (index points of the 2026 gap closed)
_e6 = R["rq2"]["e6_model_2010_25"]
_g = {k: -v["gap_2026"] for k, v in _e6.items()}
_pm = (_pe["ics_2017feb_2019"] - _pe["ics_2026_jan_aug"]) - (_pe["mean_2017feb_2019"] - _pe["mean_2026_jan_aug"])
D["e6"] = {"gap": r(_g["economy"]), "pred": r(_e6["economy"]["pred_2026"]), "absorbed": r(-E["E_ICS"]["mean_gap_2026"] - _g["economy"]),
           "web": r(_g["economy"] - _g["web"]), "party_mix": r(_pm), "household": r(_g["web"] - _g["web_household"]),
           "news": r(_g["web_household"] - _g["web_household_news"]),
           "rest": r(_g["web_household_news"] - _pm),
           "alone": {"household": r(_g["economy"] - _g["household"]), "news": r(_g["economy"] - _g["news"])},
           "economy_explains": r(-_e6["economy"]["economy"]["points"]), "N": _e6["economy"]["N"],
           # 95% range of the unexplained part (the 10-month mean gap's band, minus the party mix), floored at 0;
           # and the inflation coefficient (index points per 1 pp) in the 2010-19 and the 2010-25 economy models
           "rest_range": [max(0.0, r(-_e6["web_household_news"]["gap_band95"][1] - _pm, 0)), r(-_e6["web_household_news"]["gap_band95"][0] - _pm, 0)],
           "pi_coef": [r(E["E_ICS"]["coef"]["pi"]["coef"]), r(_e6["economy"]["coef"]["pi"])]}
# E7: the fair split of the unexplained part among the suspects (points closed, Shapley, 90% bootstrap ranges)
_SU = json.loads((OUTPUTS / "results_suspects.json").read_text())
D["suspects"] = {k: {"closed": {s: {"pts": r(v["points"]), "lo": r(v["range90"][0], 0), "hi": r(v["range90"][1], 0)}
                                for s, v in _SU[k]["closed"].items()},
                     "all": {"pts": r(_SU[k]["closed_all"]["points"]), "lo": r(_SU[k]["closed_all"]["range90"][0], 0),
                             "hi": r(_SU[k]["closed_all"]["range90"][1], 0)}}
                 for k in ["strict_1978_2019", "trained_2010_2025"]}
D["suspects"]["partisan_bound"] = r(_SU["partisan_model_free"]["upper_bound_partisan"])
D["suspects"]["in_party_fall"] = r(_SU["partisan_model_free"]["in_party_fall"])
D["suspects"]["strict_base_gap"] = r(_SU["strict_1978_2019"]["base_gap_2026"])   # the 1978-2019 model's own 2026 gap
D["suspects"]["borrowing_alone"] = r(json.loads((OUTPUTS / "results_ablation.json").read_text())["main"]["models"]["B"]["closed_points"])
_b = E["E_ICS"]["mean_gap_2026_analytic"]
D["drop"]["rest_range"] = [r(-_b["hi"] - 6.6 - _pm, 0), r(-_b["lo"] - 6.6 - _pm, 0)]   # 95% range of the 28.6
(ROOT / "presentation").mkdir(exist_ok=True)
(ROOT / "presentation" / "deck_data.json").write_text(json.dumps(D, indent=1))
print({k: v for k, v in D.items() if k not in ("ics", "worse_prices", "party", "e3", "tierc")})
