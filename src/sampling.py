"""Seeded samples for labelling and coding: the dev set, the gold set, the coding tiers, the
minimal-pair suite and the swap sets. Every sample is drawn on text features and metadata only,
never on any model output. Sheets hold (item_id, text); keys map item_id to doc_id and metadata.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from src.config import CODED, LABELS, OUTLET_GROUPS, PREREG, RANDOM_SEED

POL_RE = re.compile(r"\b(?:trump\w*|biden\w*|obama\w*|harris|vance|democrat\w*|republican\w*|gop|"
                    r"congress\w*|white house|administration|president\w*|senat\w+|powell|yellen|warsh|"
                    r"the fed\b|federal reserve)\b", re.I)
NUM_RE = re.compile(r"\d")
REDDIT_MAX_CHARS = 600


def item_text(df: pd.DataFrame) -> pd.Series:
    t = df["clean"].astype(str)
    if "sub" in df:
        t = t.str.slice(0, REDDIT_MAX_CHARS)
    return t


def period(d: pd.Series) -> pd.Series:
    y = pd.to_datetime(d).dt.year
    return np.where(y <= 2019, "2010-19", np.where(y <= 2024, "2020-24", "2025-26"))


def _take(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    return df.sample(n=min(n, len(df)), random_state=seed)


def news_frame(N: pd.DataFrame) -> pd.DataFrame:
    f = N[N["econ_term"] & N["outlet"].notna() & (N["pull"] != "release")].copy()
    f["source_type"] = np.where(f["group"] == "local", "local", "national")
    f["period"] = period(f["date"])
    f["text"] = item_text(f)
    f["has_pol"] = f["text"].str.contains(POL_RE)
    f["has_num"] = f["text"].str.contains(NUM_RE)
    return f


def reddit_frame(R: pd.DataFrame) -> pd.DataFrame:
    f = R.copy()
    f["source_type"] = "reddit"
    f["period"] = period(f["date"])
    f["text"] = item_text(f)
    f["has_pol"] = f["text"].str.contains(POL_RE)
    f["has_num"] = f["text"].str.contains(NUM_RE)
    return f


def write_sheet(name: str, items: pd.DataFrame, prefix: str) -> pd.DataFrame:
    items = items.reset_index(drop=True).copy()
    items["item_id"] = [f"{prefix}{i:04d}" for i in range(len(items))]
    LABELS.mkdir(parents=True, exist_ok=True)
    items[["item_id", "text"]].to_csv(LABELS / f"{name}_sheet.csv", index=False)
    keep = [c for c in ["item_id", "doc_id", "source_type", "outlet", "group", "sub", "kind", "date",
                        "survey_month", "period", "has_pol", "has_num", "stratum"] if c in items]
    items[keep].to_csv(LABELS / f"{name}_key.csv", index=False)
    return items


def make_dev(NF: pd.DataFrame, RF: pd.DataFrame, n_news: int = 60, n_reddit: int = 40) -> pd.DataFrame:
    s = RANDOM_SEED + 1
    news = pd.concat([_take(NF[NF["period"] == p], n_news // 3, s) for p in ["2010-19", "2020-24", "2025-26"]])
    red = pd.concat([_take(RF[RF["sub"] == sb], n_reddit // 3 + (sb == "personalfinance"), s)
                     for sb in ["Economics", "economy", "personalfinance"]])
    return pd.concat([news, red]).sample(frac=1, random_state=s)


def make_gold(NF: pd.DataFrame, RF: pd.DataFrame, exclude: set[str]) -> pd.DataFrame:
    """450 items: 180 national, 120 local, 150 Reddit; equal thirds by period; within each cell
    at least a sixth of items with a political name and a sixth with a number (text features)."""
    s = RANDOM_SEED + 2
    out = []
    plan = [("national", NF[NF["source_type"] == "national"], 180),
            ("local", NF[NF["source_type"] == "local"], 120),
            ("reddit", RF, 150)]
    for st, F, n in plan:
        F = F[~F["doc_id"].isin(exclude)]
        for p in ["2010-19", "2020-24", "2025-26"]:
            cell = F[F["period"] == p]
            k = n // 3
            pol = _take(cell[cell["has_pol"]], k // 6, s)
            num = _take(cell[cell["has_num"] & ~cell["doc_id"].isin(pol["doc_id"])], k // 6, s)
            rest = cell[~cell["doc_id"].isin(set(pol["doc_id"]) | set(num["doc_id"]))]
            if st == "national":   # spread over the three national lean groups
                rest = pd.concat([_take(rest[rest["group"] == g], (k - len(pol) - len(num)) // 3 + 1, s)
                                  for g in ["left", "center", "right"]])
            r = _take(rest, k - len(pol) - len(num), s)
            c = pd.concat([pol.assign(stratum="pol"), num.assign(stratum="num"), r.assign(stratum="random")])
            out.append(c)
    return pd.concat(out).sample(frac=1, random_state=s)


def make_batches(name: str, items: pd.DataFrame, size: int = 140) -> list[str]:
    d = CODED / "batches"
    d.mkdir(parents=True, exist_ok=True)
    paths = []
    for b, start in enumerate(range(0, len(items), size)):
        chunk = items.iloc[start:start + size]
        p = d / f"{name}_{b:03d}_in.jsonl"
        with p.open("w") as f:
            for _, r in chunk.iterrows():
                f.write(json.dumps({"item_id": r["item_id"], "text": r["text"]}) + "\n")
        paths.append(str(p))
    return paths
