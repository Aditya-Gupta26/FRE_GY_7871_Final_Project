"""Monitoring dashboard (brief section 5): one self-contained HTML page (Plotly embedded, works offline),
rebuilt from outputs/ by this script, so `python scripts/update.py` refreshes it after new data.
    python scripts/12_build_dashboard.py
Writes dashboard/index.html.
"""
import _bootstrap  # noqa: F401
import html
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from src.config import (DASHBOARD, DATA_CUTOFF, EVENTS_2026, OUTPUTS, PROCESSED, TABLES, UMICH_MODE, UPCOMING_RELEASES)

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, VIOLET, INK, INK2, MUTED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#0b0b0b", "#52514e", "#898781")
LAYOUT = dict(template="plotly_white", font=dict(family="Helvetica Neue, Helvetica, Arial, sans-serif", size=12, color=INK2),
              margin=dict(l=50, r=20, t=40, b=40), hovermode="x unified", legend=dict(orientation="h", y=-0.15))
COVID = ("2020-03-01", "2021-01-31")
DASHBOARD.mkdir(parents=True, exist_ok=True)
E = json.loads((OUTPUTS / "results_econ.json").read_text())
R = json.loads((OUTPUTS / "results.json").read_text()) if (OUTPUTS / "results.json").exists() else {}
V = json.loads((OUTPUTS / "results_validation.json").read_text()) if (OUTPUTS / "results_validation.json").exists() else {}
MED = json.loads((OUTPUTS / "results_media.json").read_text()) if (OUTPUTS / "results_media.json").exists() else {}
SU = json.loads((OUTPUTS / "results_suspects.json").read_text()) if (OUTPUTS / "results_suspects.json").exists() else {}
figs = []   # (section, figure, note)
SECTION = "gap"


def add(fig, title, note, height=380):
    fig.update_layout(**LAYOUT, height=height, title=dict(text=title, x=0.01, font=dict(size=15, color=INK)))
    figs.append((SECTION, fig, note))


# 1. sentiment vs the economic-only model, by index
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4], vertical_spacing=0.06)
for k, (name, vis) in enumerate([("ICS", True), ("ICC", False), ("ICE", False)]):
    s = pd.read_csv(TABLES / f"rq3_series_{name}.csv", index_col=0, parse_dates=True)
    oos = s.loc["2020-01-01":].copy()
    oos.loc[oos["covid_window"].astype(bool), ["pred", "bb_lo", "bb_hi"]] = np.nan
    fig.add_trace(go.Scatter(x=oos.index, y=oos["bb_hi"], line=dict(width=0), showlegend=False, hoverinfo="skip", visible=vis), 1, 1)
    fig.add_trace(go.Scatter(x=oos.index, y=oos["bb_lo"], fill="tonexty", fillcolor="rgba(42,120,214,0.16)", line=dict(width=0),
                             name="95% bootstrap band", visible=vis), 1, 1)
    fig.add_trace(go.Scatter(x=s.index, y=s["fitted"].combine_first(oos["pred"]), name="Model E prediction",
                             line=dict(color=BLUE, width=2), visible=vis), 1, 1)
    fig.add_trace(go.Scatter(x=s.index, y=s["actual"], name=f"Michigan {name}", line=dict(color=INK, width=2), visible=vis), 1, 1)
    g = s["gap"].where(~s["covid_window"].astype(bool))
    fig.add_trace(go.Bar(x=g.index, y=g, name="gap (out of sample)", marker_color=ORANGE, visible=vis), 2, 1)
fig.add_vrect(x0=COVID[0], x1=COVID[1], fillcolor="#ecebe6", line_width=0, layer="below")
btn = [dict(label=n, method="update", args=[{"visible": [i // 5 == j for i in range(15)]}]) for j, n in enumerate(["ICS", "ICC", "ICE"])]
fig.update_layout(updatemenus=[dict(buttons=btn, direction="right", x=0.0, y=1.12, showactive=True)])
fig.update_yaxes(title_text="index points", row=1, col=1)
fig.update_yaxes(title_text="gap: actual minus prediction (index points)", row=2, col=1)
add(fig, "Sentiment vs what the economy predicts (model fitted on 2010-2019 from unemployment, inflation and GDP growth as published then)",
    "Gap = actual sentiment minus the model's prediction for the same month, in index points (negative = gloomier than the economy predicts). "
    "Predictions from Jan 2020 are out of sample. The COVID months (Mar 2020 to Jan 2021, grey) are left out on purpose. "
    "The last month is Michigan's preliminary reading until the final is posted (see the top of the page).",
    height=520)

# 2. the five index questions
names = [("ICS", "ICS"), ("ICC", "ICC current"), ("ICE", "ICE expected"), ("X1_fin_now", "X1 finances now"),
         ("X2_fin_exp", "X2 finances 1y"), ("X3_bus_1y", "X3 business 1y"), ("X4_bus_5y", "X4 business 5y"),
         ("X5_durables", "X5 buying durables")]
vals = [E[f"E_{k}"]["mean_gap_2026"] for k, _ in names]
fig = go.Figure(go.Bar(y=[n for _, n in names][::-1], x=vals[::-1], orientation="h",
                       marker_color=[BLUE] * 5 + [INK2] * 3,   # bars are listed bottom-up (reversed)
                       text=[f"{v:.1f}" for v in vals[::-1]], textposition="outside"))
fig.update_xaxes(title_text="2026 mean gap: actual minus economy-only prediction (index points; X1-X5 in their own score points)")
add(fig, "Where the gap is: the 2026 average gap for each index and question",
    "Each one has its own economy-only model (fitted 2010-2019). X1 to X5 are Michigan's five questions; their tables end in Aug 2026.", height=360)

# 2b. what explains the gap (exploratory checks E6 and E7, added after the main results)
SECTION = "explain"
expl_table = ""
if SU and "e6_model_2010_25" in R.get("rq2", {}):
    pe = R["monitoring"]["party_equal_weight"]
    WEB = -UMICH_MODE["method_effect_ICS"]
    PMIX = (pe["ics_2017feb_2019"] - pe["ics_2026_jan_aug"]) - (pe["mean_2017feb_2019"] - pe["mean_2026_jan_aug"])
    GAP = -E["E_ICS"]["mean_gap_2026"]
    e6 = {k: -v["gap_2026"] for k, v in R["rq2"]["e6_model_2010_25"].items()}
    s_strict, s_25 = SU["strict_1978_2019"], SU["trained_2010_2025"]
    rest = GAP - WEB - PMIX
    left25 = e6["web_household_news"] - PMIX
    rows = {   # index points of the 2026 gap, left to right
        "Model trained 2010-2019 (the brief's out-of-sample gap)": {
            "Learned from 2021-25": 0, "Web-interview switch": WEB, "Party mix of respondents": PMIX, "Household costs": 0, "News tone": 0,
            "Suspects, fair test": max(0.0, s_strict["closed_all"]["points"]), "Unexplained": rest - max(0.0, s_strict["closed_all"]["points"])},
        "Model trained 2010-2025 (2026 still unseen)": {
            "Learned from 2021-25": GAP - e6["economy"], "Web-interview switch": e6["economy"] - e6["web"], "Party mix of respondents": PMIX,
            "Household costs": e6["web"] - e6["web_household"], "News tone": e6["web_household"] - e6["web_household_news"],
            "Suspects, fair test": min(left25, s_25["closed_all"]["points"]), "Unexplained": max(0.0, left25 - s_25["closed_all"]["points"])}}
    cols = {"Learned from 2021-25": "#c9c8c1", "Web-interview switch": INK2, "Party mix of respondents": VIOLET, "Household costs": AQUA,
            "News tone": ORANGE, "Suspects, fair test": YELLOW, "Unexplained": "#e8a3a3"}
    fig = go.Figure()
    for seg, col in cols.items():
        vals = [rows[r][seg] for r in rows]
        fig.add_trace(go.Bar(y=list(rows), x=vals, orientation="h", name=seg, marker_color=col,
                             text=[f"{v:.1f}" if v >= 1.5 else "" for v in vals], textposition="inside",
                             hovertemplate=f"{seg}: %{{x:.1f}} index points<extra></extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="index points of the 39.9-point 2026 gap (Model E, trained 2010-2019)")
    add(fig, "What explains the 2026 gap, by how the model is trained",
        f"Top: the brief's gap ({GAP:.1f} points) is out of sample, so only pieces that need no model are subtracted: Michigan's own "
        f"web-vs-phone estimate ({WEB:.1f}) and the party-mix check ({PMIX:.1f}, the national index against an equal-weight average of the "
        f"three party indexes). The suspects, tested fairly (next chart), add {s_strict['closed_all']['points']:.1f} together, leaving "
        f"{rest - s_strict['closed_all']['points']:.1f} unexplained. Bottom: the same economy model trained on 2010-2025 (COVID months skipped) "
        f"still predicts 2026 out of sample; it expects {R['rq2']['e6_model_2010_25']['economy']['pred_2026']:.1f} (gap {e6['economy']:.1f}), "
        f"because inflation now weighs about three times more. Pieces are added to it in turn; the suspects then explain "
        f"{s_25['closed_all']['points']:.1f} (90% range {s_25['closed_all']['range90'][0]:.0f} to {s_25['closed_all']['range90'][1]:.0f}), roughly the "
        f"{left25:.1f} left. Exploratory (E6, E7).", height=330)
    names = {"P5": "Price level (5-year rise above 2% a year)", "B": "Borrowing costs (30-year mortgage rate)",
             "R": "Partisan mood (Republican president)", "R60": "Inflation memory (5-year peak minus today)"}
    fig = go.Figure()
    for lab, res, col in [("Model trained 1978-2019", s_strict, BLUE), ("Model trained 2010-2025", s_25, ORANGE)]:
        ks = [k for k in names]
        pts = [res["closed"][k]["points"] if k in res["closed"] else None for k in ks]
        lo = [res["closed"][k]["points"] - res["closed"][k]["range90"][0] if k in res["closed"] else None for k in ks]
        hi = [res["closed"][k]["range90"][1] - res["closed"][k]["points"] if k in res["closed"] else None for k in ks]
        fig.add_trace(go.Bar(y=[names[k] for k in ks], x=pts, orientation="h", name=lab, marker_color=col,
                             error_x=dict(type="data", array=hi, arrayminus=lo, color=INK2, thickness=1),
                             text=[f"{v:+.1f}" if v is not None else "in household costs" for v in pts], textposition="outside",
                             hovertemplate="%{y}: %{x:.1f} points<extra>" + lab + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title_text="index points of the 2026 gap closed (minus = widens it); bars show 90% ranges", zeroline=True)
    add(fig, "The suspects, tested fairly: points of the 2026 gap each one explains",
        "One rule for every suspect: it is added to a model that never sees 2026 and the drop in the 2026 gap is read off, averaged over "
        "every order of adding the suspects (Shapley values), with 90% ranges from 500 block-bootstrap refits. In 1978-2019 (that model's "
        f"own 2026 gap is {-s_strict['base_gap_2026']:.1f}) only borrowing costs help ({s_strict['closed']['B']['points']:.1f}; it closes "
        f"{json.loads((OUTPUTS / 'results_ablation.json').read_text())['main']['models']['B']['closed_points']:.1f} on its own); the price level is "
        "about 0 and inflation memory pulls the other way (people forgave the 1980s inflation once it fell). In 2010-2025 inflation memory "
        "and the price level roughly cover the rest. Borrowing is inside the household costs in the 2010-2025 model. "
        f"Model-free partisan check: a Republican was president in both 2017-19 and 2026, and Republicans still fell "
        f"{SU['partisan_model_free']['in_party_fall']:.1f} points, so at most {SU['partisan_model_free']['upper_bound_partisan']:.1f} of the fall "
        "can be partisan. Exploratory (E7).", height=420)
    hh, oo = R["rq2"]["level_household_contribution"], R["rq2"]["model_e_2010_19_household_news"]
    f1 = lambda d: f"{-d['points']:.1f} ({-d['ci90'][1]:.1f} to {-d['ci90'][0]:.1f})"
    expl_table = (
        "<table class='plain'><tr><th>Index points of the 2026 gap explained by</th><th>Model learns 2010-2019 (out of sample)</th>"
        "<th>Model learns 2010-2026 (in sample, coefficient x change)</th><th>Model learns 2010-2025, added in turn</th></tr>"
        f"<tr><td>Household costs (six)</td><td>{-oo['plus_household']['household']['points']:.1f} (the wrong way; gap {-oo['plus_household']['gap_2026']:.1f})</td>"
        f"<td>{f1(hh['household_all6'])}; housing alone {-hh['housing_mort30_afford']['points']:.1f}</td><td>{e6['web'] - e6['web_household']:.1f}</td></tr>"
        f"<tr><td>News tone (Tier C)</td><td>{-oo['plus_news']['news']['points']:.1f} (the wrong way)</td><td>{f1(hh['news'])}</td>"
        f"<td>{e6['web_household'] - e6['web_household_news']:.1f}</td></tr></table>"
        "<p class='note'>The same two variables, three training windows. The 2010s never saw 2026's housing costs (mortgage payment on a typical "
        "home up 49% against income since 2019), so a model trained on them learns almost nothing about them; a model that sees 2026 itself is "
        "generous. News is small in every version: it mostly reports the pressures people already feel.</p>")

# 3. media measures: Tier C monthly (primary), own Opus codes (quarterly history, 2026 monthly and weekly),
# SF Fed (secondary), LM dictionary; calibration of numerical claims
SECTION = "media"
M = pd.read_parquet(PROCESSED / "media_monthly.parquet")
Q = pd.read_parquet(PROCESSED / "media_quarterly_own.parquet")
Qc = Q[Q["covered"].astype(bool)]
own26 = M.loc["2026-01-01":].where(M.loc["2026-01-01":, "own_covered"].astype(bool))
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.6, 0.4],
                    subplot_titles=["News net negativity (share negative - share positive, relevant headlines)",
                                    "SF Fed Daily News Sentiment Index (survey-window mean; higher = more positive)"])
fig.add_trace(go.Scatter(x=M.index, y=M["TC_NEGNET"], line=dict(color=BLUE, width=1.5), name="Tier C monthly (primary)"), 1, 1)
fig.add_trace(go.Scatter(x=M.index, y=M["DICT_NEGNET"], line=dict(color=MUTED, width=1.2), name="LM dictionary monthly"), 1, 1)
fig.add_trace(go.Scatter(x=Qc.index + pd.DateOffset(months=1), y=Qc["NEGNET"], mode="markers", marker=dict(color=ORANGE, size=6),
                         name="Opus codes, quarterly"), 1, 1)
fig.add_trace(go.Scatter(x=own26.index, y=own26["own_NEGNET"], line=dict(color=ORANGE, width=2.5), name="Opus codes, 2026 monthly"), 1, 1)
fig.add_trace(go.Scatter(x=M.index, y=M["SFFED"], line=dict(color=AQUA, width=1.5), name="SF Fed"), 2, 1)
fig.add_vrect(x0=COVID[0], x1=COVID[1], fillcolor="#ecebe6", line_width=0, layer="below")
add(fig, "Media tone",
    "News for each survey month runs from the 15th of the previous month to the 14th; left, center, right and local outlets count "
    "equally. Tier C = a simple classifier trained on Opus's labels that scores every economic headline (Opus could not label them "
    "all). Opus quarterly dots only where a quarter has 20+ relevant items from 3+ outlet groups.", 520)
fig = go.Figure()
fig.add_trace(go.Scatter(x=M.index, y=M["TC_SAL_prices_high"], name="prices high (Tier C)", line=dict(color=ORANGE, width=1.8)))
fig.add_trace(go.Scatter(x=M.index, y=M["TC_INFL_BAL"], name="inflation-up share of up/down stories (Tier C)", line=dict(color=VIOLET, width=1.5)))
fig.add_trace(go.Scatter(x=Qc.index + pd.DateOffset(months=1), y=Qc["SAL_prices_high"], mode="markers", marker=dict(color=ORANGE, size=6,
                         symbol="diamond"), name="prices high (Opus, quarterly)"))
fig.update_yaxes(title_text="share")
add(fig, "What price stories talk about", "Shares of relevant headlines. Compare the 'inflation up' share with whether "
    "published inflation was actually rising or falling (report, Section 5).")
fig = go.Figure()
for c, col, nm in [("LEVEL", ORANGE, "price-level frame (of price items)"), ("HH", BLUE, "household frame"), ("FC", AQUA, "forecast frame"),
                   ("EMO", MAGENTA, "emotional wording")]:
    fig.add_trace(go.Scatter(x=Qc.index + pd.DateOffset(months=1), y=Qc[c], name=nm, mode="lines+markers", line=dict(color=col, width=1.8)))
fig.update_yaxes(title_text="share")
add(fig, "How stories are framed (Opus labels, quarterly)", "Price level vs inflation rate among price stories; households vs the "
    "national economy; future vs present; emotional wording. The household frame changed in 20% of items under a meaningless "
    "wording change, so treat it as descriptive only.")
CAL = pd.read_csv(TABLES / "rq1_calibration_claims.csv", parse_dates=["date"])
cy = CAL.groupby(CAL["date"].dt.year)["match"].agg(["mean", "size"])
ci = CAL.groupby("indicator")["match"].agg(["mean", "size"])
fig = make_subplots(rows=1, cols=2, column_widths=[0.62, 0.38], subplot_titles=["Claims matching official data, by year", "By indicator"])
fig.add_trace(go.Bar(x=cy.index, y=cy["mean"], marker_color=BLUE, text=[f"n={n}" for n in cy["size"]], textposition="outside",
                     name="match rate"), 1, 1)
fig.add_trace(go.Bar(x=ci.index, y=ci["mean"], marker_color=AQUA, text=[f"n={n}" for n in ci["size"]], textposition="outside",
                     showlegend=False), 1, 2)
fig.update_yaxes(range=[0, 1.15], title_text="share matching", row=1, col=1)
fig.update_yaxes(range=[0, 1.15], row=1, col=2)
add(fig, "Are the numbers in headlines right? (claims found by Opus)",
    "A claim matches if it is within 0.1 point (payrolls 1,000) of the official figure published by that day (latest or "
    "previous release). Inflation numbers fail most often because outlets mix up CPI and PCE, or monthly and yearly changes, "
    "without saying which: only 10% of claims name the measure.", 400)
W = pd.read_parquet(PROCESSED / "media_weekly.parquet")
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=["Weekly net negativity, 2026 (Opus codes)", "Weekly 'prices high' share, 2026"])
fig.add_trace(go.Scatter(x=W.index, y=W["NEGNET"], line=dict(color=ORANGE, width=2), name="net negativity",
                         customdata=W["n_items"], hovertemplate="%{y:.2f} (n=%{customdata})"), 1, 1)
fig.add_trace(go.Scatter(x=W.index, y=W["SAL_prices_high"], line=dict(color=BLUE, width=2), name="prices high"), 2, 1)
for d, lab in EVENTS_2026:
    fig.add_vline(x=pd.Timestamp(d).timestamp() * 1000, line=dict(color=MUTED, width=1, dash="dot"))
add(fig, "Weekly news in 2026 (for display; the tests use monthly data)",
    "11 to 32 relevant headlines a week, so single weeks are noisy. Dotted lines mark events in the table below.", 480)

# 4. events and releases: each 2026 survey month's model inputs and when they were published
PNL = pd.read_parquet(PROCESSED / "panel_realtime_mid.parquet").loc["2026-01-01":]
rel_rows = "".join(
    f"<tr><td>{m:%b %Y}</td><td>{r.U:.1f} ({r.U_ref:%b}; {r.U_pub:%b %d})</td>"
    f"<td>{r.pi:.2f} ({r.pi_ref:%b}; {r.pi_pub:%b %d})</td>"
    f"<td>{r.g_qoq:.1f} ({r.g_ref.year}Q{(r.g_ref.month - 1) // 3 + 1}; {r.g_pub:%b %d})</td></tr>"
    for m, r in PNL.iterrows())
ev = "".join(f"<tr><td>{html.escape(d)}</td><td>{html.escape(t)}</td></tr>" for d, t in EVENTS_2026)
up = "".join(f"<tr><td>{html.escape(d)}</td><td>{html.escape(t)}</td></tr>" for d, t in UPCOMING_RELEASES)

# 5. composition, missingness, model performance
TCI = pd.read_parquet(PROCESSED / "tierC_items.parquet")
TCI = TCI[TCI["tc_relevant"] == "yes"]
TCI["year"] = pd.to_datetime(TCI["survey_month"]).dt.year
compo = TCI.groupby(["year", "group"]).size().unstack(fill_value=0)
comp = compo.to_html(classes="tbl")
cov26 = M.loc["2026-01-01":, ["own_n_items", "own_n_groups", "own_covered", "TC_n"]].rename(
    columns={"own_n_items": "Opus relevant items", "own_n_groups": "outlet groups", "own_covered": "enough for a reading (20+ items, 3+ groups)", "TC_n": "Tier C relevant"})
cov26["enough for a reading (20+ items, 3+ groups)"] = cov26["enough for a reading (20+ items, 3+ groups)"].map({True: "yes", False: "no"})
cov26.index = cov26.index.strftime("%b %Y")
cov = cov26.to_html(classes="tbl", float_format=lambda x: f"{x:.0f}")
miss = (f"Opus quarterly series: {int(Q['covered'].sum())} of {len(Q)} quarters have enough headlines (20+ relevant items from 3+ outlet groups); "
        f"2026 monthly: {int(M.loc['2026-01-01':, 'own_covered'].sum())} of {len(M.loc['2026-01-01':])} months. "
        f"Google News returns at most about 100 items per search (65% of outlet windows hit that cap), so counts are samples, not the true volume.")
perf_rows = []
if V:
    for r in V.get("tools_vs_gold", []):
        if r["subset"] == "all" and r["tool"] in ("opus", "dictionary", "tfidf_opus_trained", "tfidf_goldcv") and not str(r["field"]).startswith("topic"):
            perf_rows.append(r)
FIELD_NAMES = {"relevant": "Relevant", "tone": "Tone", "emotional": "Emotional wording", "frame_price": "Price level vs rate",
               "frame_unit": "Household vs national", "frame_time": "Current vs forecast", "attr_target": "Who gets credit or blame",
               "attr_dir": "Credit vs blame"}
perf = pd.DataFrame(perf_rows).pivot_table(index="field", columns="tool", values="macro_f1").round(2).rename(
    index=FIELD_NAMES, columns={"opus": "Opus coder", "dictionary": "Word list (dictionary)", "tfidf_opus_trained": "Tier C",
                                "tfidf_goldcv": "Classifier trained on gold"}).rename_axis(None).fillna("n/a").to_html(classes="tbl") if perf_rows else "<p>pending</p>"
ics_last = pd.read_csv(TABLES / "rq3_series_ICS.csv", index_col=0, parse_dates=True)["actual"].dropna()
UI = pd.read_parquet(PROCESSED / "umich_indices.parquet")
prelim = bool(UI.loc[ics_last.index[-1], "preliminary"]) if ics_last.index[-1] in UI.index else False
kpi = {f"ICS ({ics_last.index[-1]:%b %Y}{', preliminary' if prelim else ''})": f"{ics_last.iloc[-1]:.1f}",
       "Economy-only prediction, Oct 2026 (index points)": f"{pd.read_csv(TABLES / 'rq3_series_ICS.csv', index_col=0).iloc[-1]['pred']:.1f}",
       "Average gap, Jan-Oct 2026 (ICS minus prediction, index points)": f"{E['E_ICS']['mean_gap_2026']:.1f}",
       "Share of the 44.8-point fall in ICS, 2019 to 2026, that the economy explains": f"{100 * E['E_ICS']['decomposition_2019_to_2026']['share_explained']:.0f}%",
       "Dry-run months inside the 95% band (2017-19)": f"{100 * E['coverage_check_2017_19']['boot_coverage']:.0f}%"}
if SU:   # the gap accounting (exploratory): survey pieces need no model; the suspects are tested fairly
    kpi["Gap left after the web switch and party mix (index points)"] = f"{rest:.1f}"
    kpi["Unexplained after the fair suspect test (index points)"] = f"{rest - SU['strict_1978_2019']['closed_all']['points']:.1f}"

# 6. groups
SECTION = "groups"
T = pd.read_parquet(PROCESSED / "umich_tables.parquet")
fig = go.Figure()
for c, col, nm in [("ICS_DEM", BLUE, "Democrats"), ("ICS_IND", INK2, "Independents"), ("ICS_REP", ORANGE, "Republicans")]:
    s = T[c].loc["2017-02-01":]
    fig.add_trace(go.Scatter(x=s.index, y=s, name=nm, line=dict(color=col, width=2)))
fig.update_yaxes(title_text="ICS within party (index points)")
add(fig, "Sentiment by political party (Michigan Table 5b, monthly from Feb 2017)",
    "Party changes both how people answer and who answers: levels swing with the party in the White House.")
gg = E["groups"]
lab = {"ICS_bottom": "income: bottom third", "ICS_middle": "income: middle third", "ICS_top": "income: top third",
       "ICS_age18_34": "age 18-34", "ICS_age35_54": "age 35-54", "ICS_age55p": "age 55+", "ICS_NE": "Northeast",
       "ICS_MW": "Midwest", "ICS_S": "South", "ICS_W": "West"}
fig = go.Figure(go.Bar(x=[gg[k]["mean_gap_2026_jan_aug"] for k in lab], y=list(lab.values()), orientation="h", marker_color=BLUE))
fig.update_xaxes(title_text="mean gap Jan-Aug 2026: group ICS minus its economy-only prediction (index points)")
add(fig, "Gap by income, age and region (each group has its own economy-only model)", "Regional gaps use national economic data, so they are only descriptive.", 400)

parts = {"gap": [], "explain": [], "media": [], "groups": []}
for i, (sec, f, note) in enumerate(figs):
    parts[sec].append(pio.to_html(f, full_html=False, include_plotlyjs="inline" if i == 0 else False,
                                  config={"displaylogo": False, "responsive": True}))
    parts[sec].append(f"<p class='note'>{html.escape(note)}</p>")
kpis = "".join(f"<div class='kpi'><div class='v'>{v}</div><div class='l'>{html.escape(k)}</div></div>" for k, v in kpi.items())
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sentiment Gap Monitor</title>
<style>
:root {{ --bg:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --line:#e1e0d9; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font-family:'Helvetica Neue',Helvetica,Arial,sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:16px; }}
h1 {{ font-size:22px; margin:8px 0 2px; }} h2 {{ font-size:17px; margin:28px 0 6px; border-bottom:1px solid var(--line); }}
.sub {{ color:var(--ink2); font-size:13px; }}
.kpis {{ display:flex; flex-wrap:wrap; gap:10px; margin:14px 0; }}
.kpi {{ border:1px solid var(--line); border-radius:6px; padding:10px 14px; min-width:150px; background:#fff; }}
.kpi .v {{ font-size:22px; font-weight:600; }} .kpi .l {{ font-size:12px; color:var(--ink2); }}
.note {{ color:var(--ink2); font-size:12px; margin:2px 0 18px; }}
table.tbl, table.plain {{ border-collapse:collapse; font-size:12.5px; }}
.tbl td, .tbl th, .plain td, .plain th {{ border-bottom:1px solid var(--line); padding:3px 8px; text-align:left; }}
</style></head><body><main>
<h1>Consumer Sentiment Gap Monitor: Michigan sentiment vs the economy and the news, 2010 to the 2026 midterms</h1>
<p class="sub">FRE-GY 7871 final project (Aditya Gupta). Data cutoff {DATA_CUTOFF:%b %d, %Y}. Rebuild with <code>python scripts/update.py</code>.</p>
<div class="kpis">{kpis}</div>
<h2>Sentiment, what the economy predicts, and the gap</h2>{''.join(parts['gap'])}
<h2>What explains the gap (exploratory checks)</h2>{''.join(parts['explain'])}{expl_table}
<h2>The news: tone, topics, framing and accuracy</h2>{''.join(parts['media'])}
<h2>Economic releases and major events, 2026</h2>
<p class="sub">What the model used each month: the latest figure published by the 14th (value, the period it covers; the date it was published):</p>
<table class="plain"><tr><th>Survey month</th><th>U-3 %</th><th>PCE inflation, 12-month %</th><th>Real GDP, QoQ annualised %</th></tr>{rel_rows}</table>
<p class="sub">Major events:</p><table class="plain"><tr><th>Date</th><th>Event</th></tr>{ev}</table>
<h2>Groups</h2>{''.join(parts['groups'])}
<h2>Where the headlines come from, gaps in the data, and how accurate the AI is</h2>
<p class="sub">Relevant economic headlines per year and outlet group (relevance from Tier C; groups by AllSides political lean; local = 16 big-city dailies):</p>{comp}
<p class="sub">2026 months: headlines labelled by Opus, outlet groups covered, and whether the month counts:</p>{cov}
<p class="sub">{html.escape(miss)}</p>
<p class="sub">How accurate each tool is against the 450 gold labels (macro-F1, 1 = perfect). The gold labels are two passes (Claude Sonnet 5.5 and Claude Haiku 5.5, with my corrections), with Claude Fable 5.1 settling disagreements; none of them is the Opus coder being scored:</p>{perf}
<h2>Cutoff and update plan</h2>
<p class="sub">The analysis stops at the {DATA_CUTOFF:%b %d, %Y} data pull (last survey month: {list(kpi)[0]}). Upcoming releases (listed in config.UPCOMING_RELEASES):</p>
<table class="plain"><tr><th>Date</th><th>Release</th></tr>{up}</table>
</main></body></html>"""
(DASHBOARD / "index.html").write_text(page)
print("wrote dashboard/index.html", round(len(page) / 1e6, 2), "MB")
