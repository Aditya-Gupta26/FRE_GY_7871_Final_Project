"""Validate and load Claude codes (coder batches) and labels (annotators), one JSON object per line.

Checks per item: allowed values for every field; every input item_id present exactly once;
the coder's `evidence` is a verbatim substring of the item (whitespace-normalised, case-insensitive);
every claim value appears as a number in the text (deterministic check: commas dropped, and
thousands / millions read as thousands for payrolls). Items failing any check are listed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

TOPICS = ["layoffs", "hiring", "prices_high", "inflation_up", "inflation_down", "growth", "recession",
          "rates", "tariffs", "housing", "markets", "income", "other"]
ALLOWED = {
    "relevant": {"yes", "no"},
    "tone": {"negative", "neutral", "positive"},
    "emotional": {0, 1},
    "frame_price": {"level", "rate", "none"},
    "frame_unit": {"household", "aggregate", "none"},
    "frame_time": {"current", "forecast", "none"},
    "attr_target": {"president", "fed", "congress", "democrats", "republicans", "business", "foreign_trade", "none"},
    "attr_dir": {"credit", "blame", "none"},
}
INDICATORS = {"unemployment_rate", "inflation", "gdp_growth", "payrolls"}
MEASURES = {"CPI", "PCE", "core CPI", "core PCE", "unspecified", "na"}
NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")


def as_list(v) -> list:
    """List-valued fields (topics, claims) are lists in JSON but numpy arrays after a parquet round trip."""
    if v is None or (isinstance(v, float) and v != v):
        return []
    return list(v)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def _numbers(text: str) -> set[float]:
    t = text.replace(",", "")
    out = set()
    for m in NUM.finditer(t):
        x = abs(float(m.group()))
        tail = t[m.end(): m.end() + 10].lower()
        out |= {x, round(x / 1000, 6)}
        if tail.strip().startswith(("million", "m ")):
            out.add(round(x * 1000, 6))
        if tail.strip().startswith(("k", "thousand")):
            out.add(x)
    return out


def read_jsonl(path: str | Path) -> list[dict]:
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def validate(items: pd.DataFrame, rows: list[dict], coder: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """items: item_id, text. Returns (valid codes, problems)."""
    text = dict(zip(items["item_id"], items["text"]))
    probs, ok, seen = [], [], {}
    for r in rows:
        iid = r.get("item_id")
        seen[iid] = seen.get(iid, 0) + 1
    for r in rows:
        iid = r.get("item_id")
        p = []
        if iid not in text:
            p.append("unknown item_id")
        if seen.get(iid, 0) > 1:
            p.append("duplicate item_id")
        for k, allowed in ALLOWED.items():
            if r.get(k) not in allowed:
                p.append(f"{k}={r.get(k)!r}")
        tp = r.get("topics")
        if not isinstance(tp, list) or any(t not in TOPICS for t in tp):
            p.append(f"topics={tp!r}")
        cl = r.get("claims")
        if not isinstance(cl, list):
            p.append("claims not a list")
            cl = []
        for c in cl:
            if not isinstance(c, dict) or c.get("indicator") not in INDICATORS or c.get("measure") not in MEASURES \
                    or c.get("forecast") not in (0, 1) or not isinstance(c.get("value"), (int, float)):
                p.append(f"bad claim {c!r}")
            elif iid in text and round(abs(float(c["value"])), 6) not in _numbers(text[iid]):
                p.append(f"claim value {c['value']} not in text")
        if (r.get("attr_target") == "none") != (r.get("attr_dir") == "none"):
            p.append("attr_target/attr_dir inconsistent")
        if r.get("relevant") == "no" and (r.get("topics") or r.get("claims")):
            p.append("not relevant but has topics/claims")
        if coder and iid in text and r.get("relevant") == "yes":
            ev = r.get("evidence", "")
            if not ev or _norm(ev) not in _norm(text[iid]):
                p.append("evidence not verbatim")
        if p:
            probs.append({"item_id": iid, "problems": "; ".join(p)})
        else:
            ok.append(r)
    missing = sorted(set(text) - set(seen))
    for m in missing:
        probs.append({"item_id": m, "problems": "missing"})
    return pd.DataFrame(ok), pd.DataFrame(probs, columns=["item_id", "problems"])


def load_codes() -> pd.DataFrame:
    """All Opus codes. data/coded/codes.parquet (written by 07, with evidence quotes) when present; otherwise the
    committed text-free data/coded/codes.csv (topics ';'-joined, claims as JSON), so a fresh clone can run 10."""
    from src.config import CODED
    if (CODED / "codes.parquet").exists():
        return pd.read_parquet(CODED / "codes.parquet")
    d = pd.read_csv(CODED / "codes.csv")
    d["topics"] = d["topics"].fillna("").map(lambda s: [x for x in str(s).split(";") if x])
    d["claims"] = d["claims"].map(json.loads)
    return d


def to_frame(rows: list[dict]) -> pd.DataFrame:
    d = pd.DataFrame(rows)
    for t in TOPICS:
        d[f"t_{t}"] = d["topics"].map(lambda x, t=t: int(t in as_list(x)))
    d["n_claims"] = d["claims"].map(lambda x: len(as_list(x)))
    return d
