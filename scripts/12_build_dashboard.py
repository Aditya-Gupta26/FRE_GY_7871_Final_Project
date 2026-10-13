"""Monitoring dashboard (brief section 5): one self-contained HTML page (Plotly embedded, works offline),
rebuilt from outputs/ by this script, so `python scripts/update.py` refreshes it after new data.
    python scripts/12_build_dashboard.py
Writes dashboard/index.html.
"""
import _bootstrap  # noqa: F401
import html
import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from src.config import (DASHBOARD, DATA_CUTOFF, EVENTS_2026, OUTPUTS, PROCESSED, TABLES, UPCOMING_RELEASES)

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
fig.update_yaxes(title_text="index", row=1, col=1)
fig.update_yaxes(title_text="gap (points)", row=2, col=1)
add(fig, "Consumer sentiment vs the economic-only model (unemployment, PCE inflation, real GDP; fit 2010-2019 in real time)",
    "Out-of-sample from Jan 2020; the COVID window (Mar 2020 to Jan 2021, grey) is excluded by design. The last month is the "
    "preliminary reading when Michigan has not yet posted the final (see the top of the page).",
    height=520)

# 2. the five index questions
names = [("ICS", "ICS"), ("ICC", "ICC current"), ("ICE", "ICE expected"), ("X1_fin_now", "X1 finances now"),
         ("X2_fin_exp", "X2 finances 1y"), ("X3_bus_1y", "X3 business 1y"), ("X4_bus_5y", "X4 business 5y"),
         ("X5_durables", "X5 buying durables")]
vals = [E[f"E_{k}"]["mean_gap_2026"] for k, _ in names]
fig = go.Figure(go.Bar(y=[n for _, n in names][::-1], x=vals[::-1], orientation="h",
                       marker_color=[BLUE] * 5 + [INK2] * 3,   # bars are listed bottom-up (reversed)
                       text=[f"{v:.1f}" for v in vals[::-1]], textposition="outside"))
fig.update_xaxes(title_text="2026 mean gap (points; X1-X5 relative scores)")
add(fig, "Where the gap sits: the 2026 mean gap by index and by question",
    "Each series has its own Model E fit (2010-2019). X1-X5 are Michigan's five questions; their tables end in Aug 2026.", height=360)

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
    "Survey-aligned windows (15th of the previous month to the 14th), equal weights over left, center, right and local outlet groups. "
    "Tier C = TF-IDF classifier trained on Opus codes, applied to every economic headline; Opus quarterly dots only where a quarter "
    "has 20+ relevant items from 3+ groups.", 520)
fig = go.Figure()
fig.add_trace(go.Scatter(x=M.index, y=M["TC_SAL_prices_high"], name="prices high (Tier C)", line=dict(color=ORANGE, width=1.8)))
fig.add_trace(go.Scatter(x=M.index, y=M["TC_INFL_BAL"], name="inflation-up share of up/down stories (Tier C)", line=dict(color=VIOLET, width=1.5)))
fig.add_trace(go.Scatter(x=Qc.index + pd.DateOffset(months=1), y=Qc["SAL_prices_high"], mode="markers", marker=dict(color=ORANGE, size=6,
                         symbol="diamond"), name="prices high (Opus, quarterly)"))
fig.update_yaxes(title_text="share")
add(fig, "Salience and selection: price stories", "Shares of relevant headlines. The inflation-up share is the selection benchmark "
    "used in the report (Section 5): compare it with whether published inflation was rising or falling.")
fig = go.Figure()
for c, col, nm in [("LEVEL", ORANGE, "price-level frame (of price items)"), ("HH", BLUE, "household frame"), ("FC", AQUA, "forecast frame"),
                   ("EMO", MAGENTA, "emotional wording")]:
    fig.add_trace(go.Scatter(x=Qc.index + pd.DateOffset(months=1), y=Qc[c], name=nm, mode="lines+markers", line=dict(color=col, width=1.8)))
fig.update_yaxes(title_text="share")
add(fig, "Framing (Opus codes, quarterly)", "Level vs rate framing among price items; household vs national aggregate; forecast vs "
    "current; emotional wording. The household frame is fragile under a null wording change (20% flips), so read it as descriptive.")
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
add(fig, "Factual calibration of numerical claims (Opus-extracted, all coded news)",
    "A claim matches if it equals the official value in the data vintage of the publication date (latest or previous release; "
    "+-0.1 pp, payrolls +-1k). Inflation claims fail most often because outlets mix CPI and PCE or months and years "
    "without saying which: only 10% of claims name the measure.", 400)
W = pd.read_parquet(PROCESSED / "media_weekly.parquet")
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=["Weekly net negativity, 2026 (Opus codes)", "Weekly 'prices high' share, 2026"])
fig.add_trace(go.Scatter(x=W.index, y=W["NEGNET"], line=dict(color=ORANGE, width=2), name="net negativity",
                         customdata=W["n_items"], hovertemplate="%{y:.2f} (n=%{customdata})"), 1, 1)
fig.add_trace(go.Scatter(x=W.index, y=W["SAL_prices_high"], line=dict(color=BLUE, width=2), name="prices high"), 2, 1)
for d, lab in EVENTS_2026:
    fig.add_vline(x=pd.Timestamp(d).timestamp() * 1000, line=dict(color=MUTED, width=1, dash="dot"))
add(fig, "Pre-election monitoring window: weekly media (display only; tests are monthly)",
    "11 to 32 relevant items a week, so single weeks are noisy. Dotted lines: events in the table below.", 480)

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
    columns={"own_n_items": "Opus relevant items", "own_n_groups": "outlet groups", "own_covered": "meets 20/3 rule", "TC_n": "Tier C relevant"})
cov26.index = cov26.index.strftime("%b %Y")
cov = cov26.to_html(classes="tbl", float_format=lambda x: f"{x:.0f}")
miss = (f"Opus quarterly series: {int(Q['covered'].sum())} of {len(Q)} quarters meet the coverage rule (20+ relevant items from 3+ groups); "
        f"2026 monthly: {int(M.loc['2026-01-01':, 'own_covered'].sum())} of {len(M.loc['2026-01-01':])} months. "
        f"Google News returns at most ~100 items per query (65% of outlet windows hit the cap), so counts are samples, not volume.")
perf_rows = []
if V:
    for r in V.get("tools_vs_gold", []):
        if r["subset"] == "all" and r["tool"] in ("opus", "dictionary", "tfidf_opus_trained", "tfidf_goldcv") and not str(r["field"]).startswith("topic"):
            perf_rows.append(r)
perf = pd.DataFrame(perf_rows).pivot_table(index="field", columns="tool", values="macro_f1").round(2).rename(
    columns={"opus": "Opus coder", "dictionary": "LM dictionary", "tfidf_opus_trained": "Tier C", "tfidf_goldcv": "TF-IDF (gold CV)"}).to_html(classes="tbl") if perf_rows else "<p>pending</p>"
ics_last = pd.read_csv(TABLES / "rq3_series_ICS.csv", index_col=0, parse_dates=True)["actual"].dropna()
UI = pd.read_parquet(PROCESSED / "umich_indices.parquet")
prelim = bool(UI.loc[ics_last.index[-1], "preliminary"]) if ics_last.index[-1] in UI.index else False
kpi = {f"ICS ({ics_last.index[-1]:%b %Y}{', preliminary' if prelim else ''})": f"{ics_last.iloc[-1]:.1f}",
       "Model E prediction (Oct 2026)": f"{pd.read_csv(TABLES / 'rq3_series_ICS.csv', index_col=0).iloc[-1]['pred']:.1f}",
       "Mean gap, Jan-Oct 2026": f"{E['E_ICS']['mean_gap_2026']:.1f}",
       "Share of 2019-2026 fall explained": f"{100 * E['E_ICS']['decomposition_2019_to_2026']['share_explained']:.0f}%",
       "Interval coverage check (2017-19)": f"{100 * E['coverage_check_2017_19']['boot_coverage']:.0f}%"}

# 6. groups
SECTION = "groups"
T = pd.read_parquet(PROCESSED / "umich_tables.parquet")
fig = go.Figure()
for c, col, nm in [("ICS_DEM", BLUE, "Democrats"), ("ICS_IND", INK2, "Independents"), ("ICS_REP", ORANGE, "Republicans")]:
    s = T[c].loc["2017-02-01":]
    fig.add_trace(go.Scatter(x=s.index, y=s, name=nm, line=dict(color=col, width=2)))
fig.update_yaxes(title_text="ICS within party")
add(fig, "Sentiment by political party (Michigan Table 5b, monthly from Feb 2017)",
    "Party is a moderator and a confounder: levels swing with the party in the White House.")
gg = E["groups"]
lab = {"ICS_bottom": "income: bottom third", "ICS_middle": "income: middle third", "ICS_top": "income: top third",
       "ICS_age18_34": "age 18-34", "ICS_age35_54": "age 35-54", "ICS_age55p": "age 55+", "ICS_NE": "Northeast",
       "ICS_MW": "Midwest", "ICS_S": "South", "ICS_W": "West"}
fig = go.Figure(go.Bar(x=[gg[k]["mean_gap_2026_jan_aug"] for k in lab], y=list(lab.values()), orientation="h", marker_color=BLUE))
fig.update_xaxes(title_text="mean gap Jan-Aug 2026 (points)")
add(fig, "Gap by income, age and region (each group's own Model E)", "Regional gaps use national fundamentals, so they are descriptive.", 400)

parts = {"gap": [], "media": [], "groups": []}
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
<h1>Consumer Sentiment Gap Monitor: Michigan sentiment vs measured conditions and economic news, 2010 to the 2026 midterms</h1>
<p class="sub">FRE-GY 7871 final project (Aditya Gupta). Data cutoff {DATA_CUTOFF:%b %d, %Y}; built {datetime.now():%b %d, %Y %H:%M}. Rebuild with <code>python scripts/update.py</code>.</p>
<div class="kpis">{kpis}</div>
<h2>Sentiment, its economic-model prediction and the gap</h2>{''.join(parts['gap'])}
<h2>Media tone, salience, framing and factual calibration</h2>{''.join(parts['media'])}
<h2>Economic releases and major events, 2026</h2>
<p class="sub">The model inputs for each survey month: the latest value published by day 14 (value, reference period; publication date):</p>
<table class="plain"><tr><th>Survey month</th><th>U-3 %</th><th>PCE inflation, 12-month %</th><th>Real GDP, QoQ annualised %</th></tr>{rel_rows}</table>
<p class="sub">Major events:</p><table class="plain"><tr><th>Date</th><th>Event</th></tr>{ev}</table>
<h2>Groups</h2>{''.join(parts['groups'])}
<h2>Source composition, missingness and model performance</h2>
<p class="sub">Relevant economic headlines per year and outlet group (Tier C relevance; AllSides lean groups; local = 16 big-city dailies):</p>{comp}
<p class="sub">2026 monitoring months: coded items, groups and coverage:</p>{cov}
<p class="sub">{html.escape(miss)}</p>
<p class="sub">Validation against the 450 adjudicated gold labels (macro-F1). Gold labels are from two independent Claude Opus annotators plus an Opus adjudicator, not humans, so these are upper bounds:</p>{perf}
<h2>Cutoff and prospective update plan</h2>
<p class="sub">The analysis stops at the {DATA_CUTOFF:%b %d, %Y} data pull (last survey month: {list(kpi)[0]}). Scheduled releases (config.UPCOMING_RELEASES; update the list with the cutoff):</p>
<table class="plain"><tr><th>Date</th><th>Release</th></tr>{up}</table>
</main></body></html>"""
(DASHBOARD / "index.html").write_text(page)
print("wrote dashboard/index.html", round(len(page) / 1e6, 2), "MB")
