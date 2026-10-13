"""FRED / ALFRED client (api.stlouisfed.org; the keyless fredgraph.csv endpoint hangs from here).

ALFRED stores every published value with its real-time period: a row (date, value,
realtime_start, realtime_end) means "this was the published value for observation `date`
from realtime_start to realtime_end, both inclusive". realtime_start of a new value is the
publication (vintage) date, so the vintage dates are the release calendar.
The API key is read from .env and never printed or written anywhere.
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests
from dotenv import dotenv_values

from src.config import FRED_API, OBS_START, RAW, ROOT, VINTAGE_START

OUT = RAW / "fred"


def _key() -> str:
    k = dotenv_values(ROOT / ".env").get("FRED_API_KEY") or os.environ.get("FRED_API_KEY")
    if not k:
        raise RuntimeError("FRED_API_KEY missing from .env (see README: Setup)")
    return k.strip().strip('"').strip("'")


def _get(path: str, params: dict) -> dict:
    params = {**params, "api_key": _key(), "file_type": "json"}
    for attempt in range(6):
        try:
            r = requests.get(f"{FRED_API}/{path}", params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"FRED {path} {params.get('series_id')}: HTTP {r.status_code} {r.text[:200]}")
        except requests.RequestException:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"FRED {path} failed")


def vintages(series: str, obs_start: str = OBS_START, rt_start: str = VINTAGE_START,
             refresh: bool = False) -> pd.DataFrame:
    """All published values with their real-time periods, cached to data/raw/fred/."""
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "" if (obs_start, rt_start) == (OBS_START, VINTAGE_START) else f"_{obs_start}_{rt_start}"
    f = OUT / f"{series}_vintages{tag}.json"
    if f.exists() and not refresh:
        rows = json.loads(f.read_text())
    else:
        rows, offset = [], 0
        while True:
            js = _get("series/observations", {"series_id": series, "observation_start": obs_start,
                                               "realtime_start": rt_start, "realtime_end": "9999-12-31",
                                               "limit": 100000, "offset": offset})
            obs = js["observations"]
            rows += obs
            if len(rows) >= int(js["count"]) or not obs:
                break
            offset += len(obs)
        f.write_text(json.dumps(rows))
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["rt_start"] = pd.to_datetime(df["realtime_start"])
    df["rt_end"] = pd.to_datetime(df["realtime_end"].replace("9999-12-31", "2262-04-11"))
    df["value"] = pd.to_numeric(df["value"].replace(".", None), errors="coerce")
    return df[["date", "value", "rt_start", "rt_end"]].sort_values(["date", "rt_start"]).reset_index(drop=True)


def latest(series: str, obs_start: str = "1950-01-01", refresh: bool = False) -> pd.Series:
    """Latest-vintage observations, cached."""
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{series}_latest.json"
    if f.exists() and not refresh:
        obs = json.loads(f.read_text())
    else:
        obs = _get("series/observations", {"series_id": series, "observation_start": obs_start,
                                           "limit": 100000})["observations"]
        f.write_text(json.dumps(obs))
    s = pd.Series({pd.Timestamp(o["date"]): o["value"] for o in obs}, name=series)
    return pd.to_numeric(s.replace(".", None), errors="coerce")


def asof(v: pd.DataFrame, when: pd.Timestamp) -> pd.Series:
    """The vintage known at the end of day `when` (rows with rt_start <= when <= rt_end)."""
    m = (v["rt_start"] <= when) & (v["rt_end"] >= when)
    s = v.loc[m].set_index("date")["value"].sort_index()
    assert not s.index.duplicated().any(), "two values for one date in one vintage"
    return s


def release_dates(v: pd.DataFrame) -> pd.DataFrame:
    """For each observation date: the first publication date and the first-published value."""
    first = v.dropna(subset=["value"]).sort_values("rt_start").groupby("date").first()
    return first.rename(columns={"rt_start": "first_release", "value": "first_value"})[
        ["first_release", "first_value"]]
