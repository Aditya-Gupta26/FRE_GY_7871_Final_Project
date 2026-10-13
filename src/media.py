"""Media measures from coded items, aligned to the Michigan survey month.

Survey month t's media window is [day 15 of t-1, day 15 of t), so it ends at the prediction date.
News measures are computed per outlet group (left, center, right, local) and averaged with equal,
fixed group weights: no weights or effects are estimated, so nothing leaks from later months.
A month enters the own-AI series only if it has >= 20 relevant coded items from >= 3 of the 4 groups
(PREREG + dated note). Measures (shares among relevant items unless stated):
  NEGNET = share negative - share positive; EMO = share with emotional wording;
  SAL_<topic> = topic share; INFL_BAL = inflation_up / (inflation_up + inflation_down) items;
  JOB_BAL = layoffs / (layoffs + hiring) items; LEVEL = level frame among price-framed items;
  HH = household frame; FC = forecast frame; N1..N4 = narrative shares; BLAME_PRES / CREDIT_PRES =
  share blaming / crediting the president.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.coded import TOPICS, as_list
from src.config import OUTLET_GROUPS

MIN_ITEMS, MIN_GROUPS = 20, 3


def item_measures(d: pd.DataFrame) -> pd.DataFrame:
    """d: coded items with relevant == 'yes' and the coder fields; returns item-level indicators."""
    x = pd.DataFrame(index=d.index)
    x["neg"] = (d["tone"] == "negative").astype(float)
    x["pos"] = (d["tone"] == "positive").astype(float)
    x["NEGNET"] = x["neg"] - x["pos"]
    x["EMO"] = d["emotional"].astype(float)
    for t in TOPICS:
        x[f"SAL_{t}"] = d["topics"].map(lambda v, t=t: float(t in as_list(v)))
    x["infl_up"], x["infl_dn"] = x["SAL_inflation_up"], x["SAL_inflation_down"]
    x["lay"], x["hire"] = x["SAL_layoffs"], x["SAL_hiring"]
    price = d["frame_price"].isin(["level", "rate"])
    x["LEVEL"] = np.where(price, (d["frame_price"] == "level").astype(float), np.nan)
    x["HH"] = (d["frame_unit"] == "household").astype(float)
    x["FC"] = (d["frame_time"] == "forecast").astype(float)
    tp = d["topics"].map(lambda v: set(as_list(v)))
    x["N1"] = (tp.map(lambda s: "prices_high" in s) & ((d["frame_price"] == "level") | (d["frame_unit"] == "household"))).astype(float)
    x["N2"] = tp.map(lambda s: "inflation_down" in s).astype(float)
    x["N3"] = (tp.map(lambda s: bool({"layoffs", "recession"} & s)) & (d["tone"] == "negative")).astype(float)
    x["N4"] = (tp.map(lambda s: bool({"growth", "hiring"} & s)) & (d["tone"] == "positive")).astype(float)
    x["BLAME_PRES"] = ((d["attr_target"] == "president") & (d["attr_dir"] == "blame")).astype(float)
    x["CREDIT_PRES"] = ((d["attr_target"] == "president") & (d["attr_dir"] == "credit")).astype(float)
    x["ATTR_ANY"] = (d["attr_dir"] != "none").astype(float)
    return x


MEASURES = ["NEGNET", "neg", "pos", "EMO", "LEVEL", "HH", "FC", "N1", "N2", "N3", "N4", "BLAME_PRES",
            "CREDIT_PRES", "ATTR_ANY"] + [f"SAL_{t}" for t in TOPICS]


def _balance(g: pd.DataFrame) -> pd.Series:
    up, dn, lay, hire = g["infl_up"].sum(), g["infl_dn"].sum(), g["lay"].sum(), g["hire"].sum()
    return pd.Series({"INFL_BAL": up / (up + dn) if up + dn else np.nan,
                      "JOB_BAL": lay / (lay + hire) if lay + hire else np.nan})


def monthly_news(coded: pd.DataFrame, key: str = "survey_month") -> pd.DataFrame:
    """coded: relevant coded news items with columns group, survey_month (or week) and the coder fields."""
    x = item_measures(coded).join(coded[[key, "group"]])
    x = x[x["group"].isin(OUTLET_GROUPS)]
    by_g = x.groupby([key, "group"])
    gm = by_g[MEASURES].mean().join(by_g.apply(_balance, include_groups=False)).join(by_g.size().rename("n"))
    m = gm.groupby(level=0)[MEASURES + ["INFL_BAL", "JOB_BAL"]].mean()   # equal weights over groups present
    m["n_items"] = gm.groupby(level=0)["n"].sum()
    m["n_groups"] = gm.groupby(level=0).size()
    m["covered"] = (m["n_items"] >= MIN_ITEMS) & (m["n_groups"] >= MIN_GROUPS)
    return m


def monthly_simple(coded: pd.DataFrame, key: str = "survey_month") -> pd.DataFrame:
    """Plain monthly means (Reddit, Tier C, dictionary): no groups."""
    x = item_measures(coded).join(coded[[key]])
    m = x.groupby(key)[MEASURES].mean()
    m = m.join(x.groupby(key).apply(_balance, include_groups=False))
    m["n_items"] = x.groupby(key).size()
    return m


def sffed_monthly(daily: pd.Series, months: pd.DatetimeIndex) -> pd.Series:
    """Mean of the daily SF Fed index over [day 15 of t-1, day 15 of t). The daily value is itself a
    trailing, exponentially weighted (half-life about 13.5 days) average of article scores."""
    out = {}
    for t in months:
        lo, hi = t - pd.DateOffset(months=1) + pd.Timedelta(days=14), t + pd.Timedelta(days=14)
        s = daily.loc[(daily.index >= lo) & (daily.index < hi)]
        out[t] = s.mean() if len(s) else np.nan
    return pd.Series(out, name="SFFED")


def split_half(coded: pd.DataFrame, measure: str = "NEGNET", key: str = "survey_month", reps: int = 200,
               seed: int = 7871) -> dict:
    """Split-half reliability of a monthly measure: split each month's items at random into halves,
    correlate the two monthly series, Spearman-Brown r_sb = 2r / (1 + r); averaged over reps."""
    x = item_measures(coded).join(coded[[key]])
    rng = np.random.default_rng(seed)
    rs = []
    for _ in range(reps):
        h = rng.integers(0, 2, len(x))
        a = x[h == 0].groupby(key)[measure].mean()
        b = x[h == 1].groupby(key)[measure].mean()
        j = pd.concat([a, b], axis=1).dropna()
        if len(j) > 5:
            rs.append(j.corr().iloc[0, 1])
    r = float(np.mean(rs))
    return {"r_half": r, "spearman_brown": 2 * r / (1 + r), "reps": len(rs),
            "r_min": float(np.min(rs)), "r_max": float(np.max(rs))}
