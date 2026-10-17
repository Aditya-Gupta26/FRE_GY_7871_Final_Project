"""All report figures from the saved outputs (no recomputation of results here).
    python scripts/11_make_figures.py [fig1 fig2 ...]     (default: all that have their inputs)
Writes outputs/figures/fig*.png.
"""
import _bootstrap  # noqa: F401
import json
import sys

import numpy as np
import pandas as pd

from src.config import FIGURES, OUTPUTS, PROCESSED, TABLES
from src.plots import (AQUA, BLUE, GRID, INK, INK2, MAGENTA, MUTED, ORANGE, RED, VIOLET, YELLOW, plt, shade,
                       year_axis)

FIGURES.mkdir(parents=True, exist_ok=True)
COVID = (pd.Timestamp("2020-03-01"), pd.Timestamp("2021-01-31"))


def fig1():
    """Sentiment vs the economic-only model (Model E), the bootstrap interval and the gap; and the
    2026 gap by index and component question."""
    s = pd.read_csv(TABLES / "rq3_series_ICS.csv", index_col=0, parse_dates=True)
    E = json.loads((OUTPUTS / "results_econ.json").read_text())
    fig = plt.figure(figsize=(7.4, 3.25))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.35, 1], height_ratios=[1.35, 1], hspace=0.35, wspace=0.62)
    a = fig.add_subplot(gs[0, 0])
    b = fig.add_subplot(gs[1, 0], sharex=a)
    c = fig.add_subplot(gs[:, 1])
    for ax in (a, b):
        shade(ax, *COVID)
        ax.axvline(pd.Timestamp("2020-01-01"), color=MUTED, lw=0.8, ls=":")
    oos = s.loc["2020-01-01":].copy()
    oos.loc[oos["covid_window"].astype(bool), ["pred", "bb_lo", "bb_hi"]] = np.nan   # excluded by design
    a.fill_between(oos.index, oos["bb_lo"], oos["bb_hi"], color=BLUE, alpha=0.16, lw=0)
    a.plot(s.index[s["fitted"].notna()], s["fitted"].dropna(), color=BLUE, lw=1.4)
    a.plot(oos.index, oos["pred"], color=BLUE, lw=1.4, ls="--")
    a.plot(s.index, s["actual"], color=INK, lw=1.5)
    a.text(pd.Timestamp("2010-03-01"), 108, "Model E fit, 2010-2019 (real time)", color=BLUE, fontsize=7.5)
    a.text(pd.Timestamp("2020-12-01"), 113, "out-of-sample prediction and 95% band", color=BLUE, fontsize=7.5)
    a.text(pd.Timestamp("2015-06-01"), 80, "Michigan ICS", color=INK, fontsize=7.5)
    a.set_ylabel("index (1966 = 100)")
    a.set_ylim(40, 120)
    a.set_title("(a) Sentiment vs the economic-only model")
    gap = s["gap"]
    res = s["actual"] - s["fitted"]
    b.bar(res.dropna().index, res.dropna(), width=25, color=MUTED, lw=0)
    g_oos = gap.loc["2020-01-01":][~s.loc["2020-01-01":, "covid_window"].astype(bool)]
    b.bar(g_oos.index, g_oos, width=25, color=ORANGE, lw=0)
    b.axhline(0, color=INK2, lw=0.7)
    m26 = E["E_ICS"]["mean_gap_2026"]
    b.annotate(f"Jan-Oct 2026 mean {m26:.1f}", xy=(pd.Timestamp("2026-05-01"), m26), xytext=(pd.Timestamp("2013-01-01"), -45),
               fontsize=7.5, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7))
    b.set_ylabel("points")
    b.set_ylim(-60, 22)
    b.set_title("(b) Gap = sentiment - prediction (grey: in-sample residual)")
    year_axis(b, 2)
    plt.setp(a.get_xticklabels(), visible=False)
    names = [("ICS", "ICS sentiment"), ("ICC", "ICC current"), ("ICE", "ICE expected"),
             ("X1_fin_now", "X1 finances now"), ("X2_fin_exp", "X2 finances 1y"),
             ("X3_bus_1y", "X3 business 1y"), ("X4_bus_5y", "X4 business 5y"),
             ("X5_durables", "X5 durables")]
    vals = [E[f"E_{k}"]["mean_gap_2026"] for k, _ in names]
    cols = [INK2] * 3 + [BLUE] * 5
    y = np.arange(len(names))[::-1]
    c.barh(y, vals, color=cols, height=0.62)
    for yy, v in zip(y, vals):
        c.text(v - 1.5, yy, f"{v:.0f}", va="center", ha="right", fontsize=7.3, color=INK2)
    c.set_yticks(y, [n for _, n in names], fontsize=7.4)
    c.set_xlim(-100, 0)
    c.axvline(0, color=INK2, lw=0.7)
    c.set_title("(c) 2026 mean gap by index")
    c.set_xlabel("points (X1-X5: relative score)")
    c.grid(axis="y", visible=False)
    fig.savefig(FIGURES / "fig3_baseline_gap.png")
    plt.close(fig)


def _t90(nu):
    from scipy import stats
    return float(stats.t.ppf(0.95, nu))


def fig2():
    """Media measures over time (same units: net negative share among relevant items), the SF Fed index
    (own units, own panel), and how each measurement tool scores against the gold labels."""
    M = pd.read_parquet(PROCESSED / "media_monthly.parquet")
    Q = pd.read_parquet(PROCESSED / "media_quarterly.parquet")
    V = pd.read_csv(TABLES / "val_tools_vs_gold.csv")
    fig = plt.figure(figsize=(7.4, 3.15))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.2, 1], height_ratios=[1.5, 1], hspace=0.38, wspace=0.42)
    a = fig.add_subplot(gs[0, 0])
    b = fig.add_subplot(gs[1, 0], sharex=a)
    c = fig.add_subplot(gs[:, 1])
    for ax in (a, b):
        shade(ax, *COVID)
    a.plot(M.index, M["DICT_NEGNET"], color=MUTED, lw=0.9)
    a.plot(M.index, M["TC_NEGNET"], color=BLUE, lw=1.1)
    q = Q[Q["ownQ_covered"].astype(bool)]
    a.plot(q.index + pd.DateOffset(months=1), q["ownQ_NEGNET"], "o", color=ORANGE, ms=3.2, mec="white", mew=0.5)
    own26 = M.loc["2026-01-01":, "own_NEGNET"].where(M.loc["2026-01-01":, "own_covered"].astype(bool))
    a.plot(own26.index, own26, color=ORANGE, lw=1.4)
    a.axhline(0, color=INK2, lw=0.6)
    a.text(pd.Timestamp("2010-02-01"), 0.98, "Tier C (TF-IDF trained on Opus codes), monthly", color=BLUE, fontsize=7.3)
    a.text(pd.Timestamp("2010-02-01"), 0.87, "own Opus codes: quarterly dots; 2026 monthly line", color=ORANGE, fontsize=7.3)
    a.text(pd.Timestamp("2010-02-01"), 0.76, "LM dictionary, monthly", color=MUTED, fontsize=7.3)
    a.set_ylim(-0.4, 1.05)
    a.set_ylabel("share neg. - share pos.")
    a.set_title("(a) Net negativity of economic news")
    b.plot(M.index, M["SFFED"], color=AQUA, lw=1.1)
    b.axhline(0, color=INK2, lw=0.6)
    b.set_ylabel("index")
    b.set_title("(b) SF Fed daily news sentiment, survey-month mean")
    year_axis(b, 2)
    plt.setp(a.get_xticklabels(), visible=False)
    fields = [("relevant", "relevance"), ("tone", "tone"), ("emotional", "emotional"), ("frame_price", "price frame"),
              ("frame_time", "time frame"), ("attr_dir", "attribution")]
    tools = [("opus", "Opus coder", ORANGE, "o"), ("tfidf_opus_trained", "Tier C", BLUE, "s"),
             ("tfidf_goldcv", "TF-IDF on gold (CV)", AQUA, "D"), ("dictionary", "dictionary", MUTED, "^")]
    v = V[V["subset"] == "all"].pivot_table(index="field", columns="tool", values="macro_f1")
    y = np.arange(len(fields))[::-1]
    for tk, lab, col, mk in tools:
        c.plot(v.loc[[f for f, _ in fields], tk], y, mk, color=col, ms=4.5, mec="white", mew=0.5, label=lab, ls="none")
    c.set_yticks(y, [n for _, n in fields])
    c.set_xlim(0.2, 1.02)
    c.set_xlabel("macro-F1 vs gold (450 items)")
    c.set_title("(c) Tools vs gold labels")
    c.legend(loc="upper left", bbox_to_anchor=(-0.1, -0.17), ncol=2, fontsize=7, handletextpad=0.2, columnspacing=0.8)
    c.grid(axis="y", visible=False)
    fig.savefig(FIGURES / "fig1_media.png")
    plt.close(fig)


def fig3():
    """RQ1 bias tests: asymmetric response, release-day tone by the released change, selection of
    inflation stories, and negativity by outlet lean and the president's party."""
    R = json.loads((OUTPUTS / "results.json").read_text())["rq1"]
    bins = pd.read_csv(TABLES / "rq1_release_bins.csv")
    fig, ((a, b), (c, d)) = plt.subplots(2, 2, figsize=(7.4, 3.75), gridspec_kw={"hspace": 0.85, "wspace": 0.3})
    asy = R["asymmetry"]["TC_NEGNET|all"]
    t = _t90(asy["nu"])
    xs = {"U": 0, "pi": 1}
    for k, x0 in xs.items():
        r = asy[k]
        for dx, key, col in [(-0.12, "bad", ORANGE), (0.12, "good", BLUE)]:
            m, se = r[f"resp_{key}"], r[f"se_{key}"]
            a.errorbar(x0 + dx, m, yerr=t * se, fmt="o", color=col, ms=4.5, capsize=0, elinewidth=1.2)
        a.text(x0, max(r["resp_bad"] + t * r["se_bad"], r["resp_good"] + t * r["se_good"]) + 0.03,
               f"one-sided p = {r['p_one_sided']:.3f}", ha="center", fontsize=7, color=INK2)
    a.axhline(0, color=INK2, lw=0.6)
    a.set_xticks([0, 1], ["unemployment\n(per pp change)", "inflation\n(per pp change)"])
    a.set_xlim(-0.6, 1.6)
    a.set_ylabel("response per pp change")
    a.text(-0.5, -0.33, "bad news", color=ORANGE, fontsize=7.3)
    a.text(0.2, -0.33, "good news", color=BLUE, fontsize=7.3)
    a.set_ylim(-0.4, 0.95)
    a.set_title("(a) Response to bad vs good news (Tier C, 90% CI)")
    a.grid(axis="x", visible=False)
    order = ["<=-0.2", "-0.1", "0", "+0.1", ">=+0.2"]
    for rel, col, lab in [("jobs", ORANGE, "jobs day (x: change in U-3)"), ("cpi", VIOLET, "CPI day (x: change in CPI y/y)")]:
        g = bins[bins["release"] == rel].set_index("bin").reindex(order)
        b.plot(range(5), g["neg"], "-o", color=col, ms=3.8, lw=1.3, mec="white", mew=0.5, label=lab)
    nj = bins[bins["release"] == "jobs"].set_index("bin").reindex(order)["items"]
    nc = bins[bins["release"] == "cpi"].set_index("bin").reindex(order)["items"]
    b.set_xticks(range(5), [f"{lab}\n{j} / {c_}" for lab, j, c_ in zip(["<= -0.2", "-0.1", "0", "+0.1", ">= +0.2"], nj, nc)],
                 fontsize=7.2)
    b.set_xlabel("released change, pp (right = worse); items: jobs / CPI")
    b.set_ylabel("share of items negative")
    b.set_ylim(0.1, 0.7)
    b.legend(loc="upper left", fontsize=7)
    b.set_title("(b) Release-day tone")
    sel = R["selection"]
    vals = [sel["falling"]["share_up"], sel["rising"]["share_up"]]
    c.bar([0, 1], vals, color=[BLUE, ORANGE], width=0.55)
    lo, hi = sel["falling"]["share_up_ci"]
    c.errorbar(0, vals[0], yerr=[[vals[0] - lo], [hi - vals[0]]], color=INK2, capsize=0, elinewidth=1.1)
    for i, k in enumerate(["falling", "rising"]):
        s = sel[k]
        c.text(i, 0.04, f"{s['inflation_up_items']} up /\n{s['inflation_down_items']} down", ha="center", fontsize=6.8, color="white")
    c.axhline(0.5, color=MUTED, lw=0.7, ls=":")
    c.set_xticks([0, 1], [f"inflation fell\n({sel['falling']['months']} months)", f"inflation rose\n({sel['rising']['months']} months)"])
    c.set_ylim(0, 0.8)
    c.set_ylabel("'inflation up' share")
    c.set_title("(c) Which inflation stories get told")
    c.grid(axis="x", visible=False)
    nb = R["neg_by_lean_and_president"]
    groups = ["left", "center", "right", "local"]
    x = np.arange(len(groups))
    for dx, pres, col, lab in [(-0.19, "D", BLUE, "Democratic president"), (0.19, "R", RED, "Republican president")]:
        vals = [nb[f"{pres}|{g}"]["neg_share"] for g in groups]
        d.bar(x + dx, vals, width=0.36, color=col, label=lab)
        for xx, g, v in zip(x + dx, groups, vals):
            d.text(xx, v + 0.012, f"{nb[f'{pres}|{g}']['n']}", ha="center", fontsize=6.2, color=INK2)
    d.set_xticks(x, groups)
    d.set_ylim(0, 0.92)
    d.set_ylabel("share of items negative")
    d.legend(loc="upper left", fontsize=7, ncol=2)
    d.set_title("(d) Negativity by outlet lean (numbers: items)")
    d.grid(axis="x", visible=False)
    fig.savefig(FIGURES / "fig4_bias_tests.png")
    plt.close(fig)


def fig4():
    """RQ5: out-of-sample nowcasts of sentiment, where the media and household-pressure blocks gain
    or lose (cumulative squared-error difference), and RMSE by period."""
    N = pd.read_csv(TABLES / "rq5_nowcasts.csv", index_col=0, parse_dates=True)
    A = pd.read_csv(TABLES / "rq5_accuracy.csv")
    full = pd.date_range(N.index.min(), N.index.max(), freq="MS")
    N = N.reindex(full)
    fig = plt.figure(figsize=(7.4, 3.15))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.1, 1], height_ratios=[1.35, 1], hspace=0.38, wspace=0.38)
    a = fig.add_subplot(gs[0, 0])
    b = fig.add_subplot(gs[1, 0], sharex=a)
    c = fig.add_subplot(gs[:, 1])
    for ax in (a, b):
        shade(ax, *COVID)
    a.plot(N.index, N["y"], color=INK, lw=1.5)
    a.plot(N.index, N["m1"], color=BLUE, lw=1.1, ls="--")
    a.plot(N.index, N["m2"], color=ORANGE, lw=1.1)
    a.plot(N.index, N["m1b"], color=AQUA, lw=1.1)
    a.text(pd.Timestamp("2017-02-01"), 62, "Michigan ICS", color=INK, fontsize=7.3)
    a.text(pd.Timestamp("2017-02-01"), 53, "m1 econ only", color=BLUE, fontsize=7.3)
    a.text(pd.Timestamp("2017-02-01"), 44, "m2 econ + media (real-time Tier C)", color=ORANGE, fontsize=7.3)
    a.text(pd.Timestamp("2021-04-01"), 108, "m1b econ + household pressures", color=AQUA, fontsize=7.3)
    a.set_ylim(40, 115)
    a.set_ylabel("index")
    a.set_title("(a) Expanding-window nowcasts, data to day 14")
    for col, lab, cc in [("m2", "m1 vs m2 (media)", ORANGE), ("m1b", "m1 vs m1b (household)", AQUA)]:
        dd = (N["m1"] - N["y"]) ** 2 - (N[col] - N["y"]) ** 2
        b.plot(N.index, dd.fillna(0).cumsum() / 1000, color=cc, lw=1.3, label=lab)
    b.axhline(0, color=INK2, lw=0.6)
    b.set_ylabel("thousand pts$^2$")
    b.legend(loc="upper left", fontsize=7)
    b.set_title("(b) Cumulative squared-error gain over m1")
    year_axis(b, 1)
    plt.setp(a.get_xticklabels(), visible=False)
    a_ = A[~A["dynamic"]].pivot_table(index="subperiod", columns="model", values="rmse")
    per = ["2017-19", "2021-26", "2026"]
    models = [("m1", "m1 econ", BLUE, "o"), ("m2", "m2 + media", ORANGE, "s"), ("m1b", "m1b + household", AQUA, "D"),
              ("m3", "m3 + both", VIOLET, "^")]
    y = np.arange(len(per))[::-1]
    for j, (k, lab, col, mk) in enumerate(models):
        yy = y + 0.3 - 0.2 * j
        c.barh(yy, a_.loc[per, k], height=0.18, color=col, label=lab)
        for y0, v in zip(yy, a_.loc[per, k]):
            c.text(v + 0.3, y0, f"{v:.1f}", va="center", fontsize=6.2, color=INK2)
    c.set_yticks(y, per)
    c.set_xlim(0, 27)
    c.set_xlabel("RMSE, index points")
    c.set_title("(c) Error by period")
    c.legend(loc="upper center", bbox_to_anchor=(0.45, -0.14), ncol=2, fontsize=6.8, columnspacing=0.6, handlelength=1)
    c.grid(axis="y", visible=False)
    fig.savefig(FIGURES / "fig6_prediction.png")
    plt.close(fig)


def fig5():
    """RQ4 mechanisms: price-level anchoring, recall of price news vs coverage, and partisan sentiment."""
    S = pd.read_csv(TABLES / "rq4_mechanism_series.csv", index_col=0, parse_dates=True)
    R = json.loads((OUTPUTS / "results.json").read_text())["rq4"]
    T = pd.read_parquet(PROCESSED / "umich_tables.parquet")
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.4, 2.6), gridspec_kw={"wspace": 0.42})
    d = S[["worse_prices", "price_level_gap", "pi"]].dropna()
    d = d[(d.index < COVID[0]) | (d.index > COVID[1])]
    for (lo, hi), col, lab in [(("2010", "2019"), MUTED, "2010-19"), (("2021", "2022"), BLUE, "2021-22"),
                               (("2023", "2026"), ORANGE, "2023-26")]:
        x = d.loc[lo:hi]
        a.plot(x["price_level_gap"], x["worse_prices"], "o", color=col, ms=3, mec="white", mew=0.3, label=lab)
    an = R["anchoring_price_level"]["worse_prices"]
    a.set_xlabel("PCE price level vs 2010-19 trend, log points")
    a.set_ylabel("% worse off because of prices")
    a.legend(loc="upper left", fontsize=6.8, handletextpad=0.1)
    a.text(0.98, 0.04, f"R$^2$: level gap {an['R2_price_level_gap']:.2f}\ninflation rate {an['R2_pi']:.2f}",
           transform=a.transAxes, ha="right", fontsize=6.8, color=INK2)
    a.set_title("(a) Anchoring on the price level")
    z = S[["media_price", "unfav_high_prices"]].copy()
    z.loc[COVID[0]:COVID[1]] = np.nan
    z = (z - z.mean()) / z.std()
    b.plot(z.index, z["unfav_high_prices"], color=INK, lw=1.0)
    b.plot(z.index, z["media_price"], color=BLUE, lw=1.0)
    av = R["availability_recall_vs_media"]
    b.text(pd.Timestamp("2010-06-01"), 4.1, "heard bad news about prices", color=INK, fontsize=6.8)
    b.text(pd.Timestamp("2010-06-01"), 3.4, "'prices high' share of coverage", color=BLUE, fontsize=6.8)
    b.text(pd.Timestamp("2010-06-01"), -1.9, f"r = {av['corr_levels']:.2f} (levels), {av['corr_changes']:.2f} (changes)",
           fontsize=6.8, color=INK2)
    b.set_ylim(-2.2, 4.6)
    b.set_ylabel("z-score (2010-26)")
    year_axis(b, 4)
    b.set_title("(b) Recall vs coverage")
    p = T[["ICS_DEM", "ICS_IND", "ICS_REP"]].loc["2016-01-01":].dropna()
    for k, col, lab, yy in [("ICS_REP", RED, "Republicans", None), ("ICS_IND", MUTED, "Independents", None),
                            ("ICS_DEM", BLUE, "Democrats", None)]:
        c.plot(p.index, p[k], color=col, lw=1.2)
        c.text(p.index[-1] + pd.Timedelta(days=40), p[k].iloc[-1], lab, color=col, fontsize=6.6, va="center")
    for e in ["2016-11-08", "2020-11-03", "2024-11-05"]:
        c.axvline(pd.Timestamp(e), color=MUTED, lw=0.7, ls=":")
    c.set_ylabel("ICS by party")
    c.set_xticks([pd.Timestamp(f"{y}-01-01") for y in (2016, 2020, 2024)], ["2016", "2020", "2024"])
    c.set_xlim(p.index[0], p.index[-1] + pd.Timedelta(days=1250))
    c.set_title("(c) Sentiment by party")
    fig.savefig(FIGURES / "fig5_mechanisms.png")
    plt.close(fig)


def fig6():
    """Monitoring, 2025-2026: sentiment vs the model, weekly coverage of 2026, and the June to October
    change in the gap in midterm vs other years."""
    from src.config import EVENTS_2026
    s = pd.read_csv(TABLES / "rq3_series_ICS.csv", index_col=0, parse_dates=True).loc["2025-01-01":]
    W = pd.read_parquet(PROCESSED / "media_weekly.parquet")
    R = json.loads((OUTPUTS / "results.json").read_text())["monitoring"]
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.4, 2.6), gridspec_kw={"wspace": 0.48, "width_ratios": [1.15, 1.15, 1]})
    a.fill_between(s.index, s["bb_lo"], s["bb_hi"], color=BLUE, alpha=0.16, lw=0)
    a.plot(s.index, s["pred"], color=BLUE, lw=1.2, ls="--")
    a.plot(s.index[:-1], s["actual"].iloc[:-1], "-o", color=INK, lw=1.3, ms=2.5)
    a.plot(s.index[-1], s["actual"].iloc[-1], "o", color=INK, mfc="white", ms=4)
    a.annotate("Oct prelim.", xy=(s.index[-1], s["actual"].iloc[-1]), xytext=(pd.Timestamp("2026-03-01"), 64),
               fontsize=6.8, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    a.text(pd.Timestamp("2025-01-15"), 103, "Model E prediction", color=BLUE, fontsize=6.8)
    a.text(pd.Timestamp("2025-01-15"), 66, "Michigan ICS", color=INK, fontsize=6.8)
    a.set_ylim(40, 110)
    a.xaxis.set_major_locator(__import__("matplotlib.dates", fromlist=["x"]).MonthLocator([1, 7]))
    a.xaxis.set_major_formatter(__import__("matplotlib.dates", fromlist=["x"]).DateFormatter("%b\n%Y"))
    a.set_title("(a) Sentiment vs model")
    w = W.loc["2026-01-01":]
    b.plot(w.index, w["NEGNET"], color=ORANGE, lw=1.1)
    b.plot(w.index, w["SAL_prices_high"], color=BLUE, lw=1.1)
    b.text(pd.Timestamp("2026-01-05"), 1.17, "net negativity", color=ORANGE, fontsize=6.8)
    b.text(pd.Timestamp("2026-01-05"), 1.07, "'prices high' share", color=BLUE, fontsize=6.8)
    for dte, lab in [("2026-02-28", "Iran"), ("2026-06-10", "CPI peak"), ("2026-09-16", "Fed hike")]:
        b.axvline(pd.Timestamp(dte), color=MUTED, lw=0.7, ls=":")
        right = dte > "2026-08-01"
        b.text(pd.Timestamp(dte) + pd.Timedelta(days=-3 if right else 3), 0.84 if right else 0.93, lab, fontsize=6.3, color=INK2,
               ha="right" if right else "left")
    b.set_ylim(-0.25, 1.25)
    b.xaxis.set_major_locator(__import__("matplotlib.dates", fromlist=["x"]).MonthLocator([1, 4, 7, 10]))
    b.xaxis.set_major_formatter(__import__("matplotlib.dates", fromlist=["x"]).DateFormatter("%b"))
    b.set_ylabel("share of relevant items")
    b.set_title("(b) Weekly 2026 coverage (Opus)")
    yrs = {int(k): v for k, v in R["jun_to_oct_gap_change"].items() if v is not None}
    ys = sorted(yrs)
    mid = [2010, 2014, 2018, 2022, 2026]
    cols = [ORANGE if y in mid else (SHADE_C if y == 2020 else MUTED) for y in ys]
    c.bar(ys, [yrs[y] for y in ys], color=cols, width=0.7)
    c.axhline(0, color=INK2, lw=0.6)
    c.set_xticks([2010, 2014, 2018, 2022, 2026], ["2010", "14", "18", "22", "26"])
    c.text(2009.6, -15.5, "midterm\nyears", color=ORANGE, fontsize=6.8)
    c.set_ylabel("change in gap, Jun to Oct")
    c.set_title("(c) Pre-election drift")
    c.grid(axis="x", visible=False)
    fig.savefig(FIGURES / "fig7_monitoring.png")
    plt.close(fig)


def fig_tierc():
    """How the Tier C classifier was trained and how it does: fit on its own training labels vs items it has not
    seen (cross-validation on Opus labels; the adjudicated gold labels), a learning curve, and agreement with
    Opus's own quarterly series."""
    T = pd.read_csv(TABLES / "tierc_training.csv").set_index("classifier")
    LC = pd.read_csv(TABLES / "tierc_learning_curve.csv")
    Q = pd.read_csv(TABLES / "tierc_vs_opus_quarterly.csv", index_col=0, parse_dates=True)
    R = json.loads((OUTPUTS / "results_tierc.json").read_text())
    Q = Q.reindex(pd.date_range("2010-01-01", Q.index.max(), freq="QS"))   # gaps break the lines
    fig = plt.figure(figsize=(7.4, 2.55))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 0.85, 1.35], wspace=0.55)
    a, b, c = (fig.add_subplot(gs[0, k]) for k in range(3))
    names = [("relevant", "relevance"), ("tone", "tone"), ("topic:inflation_up", "inflation up"),
             ("topic:inflation_down", "inflation down"), ("topic:prices_high", "prices high"),
             ("topic:layoffs", "layoffs"), ("topic:hiring", "hiring")]
    y = np.arange(len(names))[::-1]
    for col, lab, colr, mk in [("train_macro_f1", "training labels (fit)", INK2, "o"),
                               ("cv_macro_f1", "unseen Opus labels (5-fold CV)", BLUE, "s"),
                               ("gold_macro_f1", "gold labels (never trained on)", ORANGE, "D")]:
        a.plot(T.loc[[n for n, _ in names], col], y, mk, color=colr, ms=4.3, mec="white", mew=0.5, ls="none", label=lab)
    a.set_yticks(y, [n for _, n in names])
    a.set_xlim(0.4, 1.0)
    a.set_xlabel("macro-F1 (1 = perfect)")
    a.set_title("(a) Fit vs unseen items")
    a.legend(loc="upper left", bbox_to_anchor=(-0.55, -0.2), ncol=1, fontsize=6.8, handletextpad=0.2)
    a.grid(axis="y", visible=False)
    for name, colr in [("relevant", AQUA), ("tone", MAGENTA)]:
        d = LC[LC["classifier"] == name]
        b.plot(d["n"], d["cv_macro_f1"], "-o", color=colr, ms=3.2, mec="white", mew=0.5, lw=1.2)
        b.text(d["n"].iloc[-1] * 1.12, d["cv_macro_f1"].iloc[-1], "relevance" if name == "relevant" else "tone",
               color=colr, fontsize=7, va="center")
    b.set_xscale("log")
    b.set_xticks([450, 1000, 2000, 4000, 8000], ["450", "1k", "2k", "4k", "8k"])
    b.minorticks_off()
    b.set_xlim(350, 16000)
    b.set_ylim(0.4, 0.9)
    b.set_xlabel("training items (Opus labels)")
    b.set_ylabel("macro-F1, unseen items")
    b.set_title("(b) More labels, better")
    ag = R["agreement_with_opus_quarterly"]["TC_NEGNET"]
    c.plot(Q.index, Q["ownQ_NEGNET"], "o-", color=ORANGE, ms=2.6, lw=0.9, mec="white", mew=0.4)
    c.plot(Q.index, Q["TC_NEGNET"], "s-", color=BLUE, ms=2.4, lw=0.9, mec="white", mew=0.4)
    c.text(pd.Timestamp("2010-04-01"), 0.83, "Opus's own labels", color=ORANGE, fontsize=7)
    c.text(pd.Timestamp("2010-04-01"), 0.73, "Tier C", color=BLUE, fontsize=7)
    c.text(pd.Timestamp("2017-06-01"), -0.33, f"r = {ag['r_levels']:.2f} ({ag['N_quarters']} quarters)", color=INK2, fontsize=7)
    c.axhline(0, color=INK2, lw=0.6)
    c.set_ylim(-0.4, 0.95)
    c.set_ylabel("share neg. - share pos.")
    c.set_title("(c) Same answer as Opus, by quarter")
    year_axis(c, 4)
    fig.savefig(FIGURES / "fig2_tierc.png")
    plt.close(fig)


SHADE_C = "#c9c8c1"
# report numbering follows the order of appearance: Figure 1 media (fn fig2), Figure 2 Tier C (fn fig_tierc),
# Figure 3 baseline (fn fig1), Figure 4 bias tests (fn fig3), Figure 5 mechanisms (fn fig5), Figure 6 prediction
# (fn fig4), Figure 7 monitoring (fn fig6)
FIGS = {"fig1": fig2, "fig2": fig_tierc, "fig3": fig1, "fig4": fig3, "fig5": fig5, "fig6": fig4, "fig7": fig6}
if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    for k in want:
        try:
            FIGS[k]()
            print("wrote", k)
        except FileNotFoundError as e:
            print("skip", k, "(missing input:", e.filename, ")")
