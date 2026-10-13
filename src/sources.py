"""Small official-source fetchers used for cross-checks and benchmarks.

- BLS public API v2 (no key): LNS14000000, the official U-3 rate, to confirm ALFRED's UNRATE.
- SF Fed Daily News Sentiment Index (Buckman, Shapiro, Sudhof and Wilson 2020; Shapiro,
  Sudhof and Wilson 2022), daily, from 1980; built from economic articles in 24 major US
  newspapers (national and local).
- The course Excel (Perceptual_Bias_Data.xlsx): four (date, value) column pairs.
"""
from __future__ import annotations

import json

import pandas as pd
import requests

from src.config import BLS_API, BLS_U3, COURSE_XLSX, RAW, SFFED_NEWS_XLSX

UA = {"User-Agent": "Mozilla/5.0 (academic research; NYU FRE-GY 7871 course project)"}


def bls_u3(start: int = 2010, end: int = 2026) -> pd.Series:
    out = RAW / "bls"
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"{BLS_U3}_{start}_{end}.json"
    if not f.exists():
        data = []
        for a in range(start, end + 1, 10):          # keyless v2: at most 10 years per request
            b = min(a + 9, end)
            r = requests.post(BLS_API, json={"seriesid": [BLS_U3], "startyear": str(a), "endyear": str(b)},
                              headers=UA, timeout=60)
            js = r.json()
            assert js.get("status") == "REQUEST_SUCCEEDED", js.get("message")
            data += js["Results"]["series"][0]["data"]
        f.write_text(json.dumps(data))
    data = json.loads(f.read_text())
    s = {pd.Timestamp(f"{d['year']}-{d['period'][1:]}-01"): float(d["value"])
         for d in data if d["period"].startswith("M") and d["period"] != "M13" and d["value"] not in ("-", "")}
    return pd.Series(s, name="bls_u3").sort_index()


def sffed_daily() -> pd.Series:
    out = RAW / "sffed"
    out.mkdir(parents=True, exist_ok=True)
    f = out / "news_sentiment_data.xlsx"
    if not f.exists():
        r = requests.get(SFFED_NEWS_XLSX, headers=UA, timeout=60)
        r.raise_for_status()
        f.write_bytes(r.content)
    d = pd.read_excel(f, sheet_name="Data")
    s = d.set_index(pd.to_datetime(d["date"]))["News Sentiment"].astype(float).sort_index()
    return s.rename("sffed")


def course_file() -> dict[str, pd.Series]:
    x = pd.read_excel(COURSE_XLSX, header=None)
    out = {}
    for (dc, vc), name in zip([(0, 1), (3, 4), (7, 8), (10, 11)], ["unemployment", "sentiment", "pce_yoy", "gdp_qoq"]):
        p = x.iloc[1:, [dc, vc]].dropna()
        idx = pd.to_datetime(p[dc])
        if name == "gdp_qoq":   # dated at quarter end: map to the quarter's first month (FRED convention)
            idx = idx.dt.to_period("Q").dt.start_time
        else:
            idx = idx.dt.to_period("M").dt.start_time
        out[name] = pd.Series(p[vc].astype(float).to_numpy(), index=idx, name=name).sort_index()
    assert x.iloc[0, [0, 1, 3, 4, 7, 8, 10, 11]].tolist() == [
        "Date", "Unemployment", "Date", "Consumer Sentiment", "Date", "PCE YoY", "Date", "Real GDP QoQ Annualized"]
    return out


def epu_news() -> pd.Series:
    """News-based EPU (Baker, Bloom and Davis 2016), monthly, from policyuncertainty.com. FRED's
    USEPUINDXM is the older three-component index and is heavily revised, so it is not used."""
    f = RAW / "epu" / "US_Policy_Uncertainty_Data.xlsx"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get("https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.xlsx", headers=UA, timeout=60)
        r.raise_for_status()
        f.write_bytes(r.content)
    x = pd.read_excel(f)
    x = x[pd.to_numeric(x["Year"], errors="coerce").notna() & x["Month"].notna()]
    idx = pd.to_datetime(dict(year=x["Year"].astype(int), month=x["Month"].astype(int), day=1))
    return pd.Series(x["News_Based_Policy_Uncert_Index"].astype(float).to_numpy(), index=idx, name="epu_news").sort_index()
