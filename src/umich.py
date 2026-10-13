"""University of Michigan Surveys of Consumers: the indices and the historical tables.

- ICS, ICC, ICE (final values) from sca.isr.umich.edu/files/tbmics.csv and tbmiccice.csv;
  Oct 2026 is the preliminary release of Oct 9, 2026 (config.UMICH_OCT2026_PRELIM), flagged.
- Historical ("RB") Excel tables from data.sca.isr.umich.edu/tables.php (links carry a key that
  can change, so they are re-read from the page). Columns are named from each table's header.
Index formulas (UMich technical documentation): with X_i = % favourable - % unfavourable + 100 on
the five questions, ICS = (X1+X2+X3+X4+X5)/6.7558 + 2.0, ICC = (X1+X5)/2.6424 + 2.0,
ICE = (X2+X3+X4)/4.1134 + 2.0.
"""
from __future__ import annotations

import html
import io
import re
import warnings

import pandas as pd
import requests

from src.config import RAW, UMICH_CSV, UMICH_FILES, UMICH_OCT2026_PRELIM, UMICH_TABLES, UMICH_TABLES_PAGE

OUT = RAW / "umich"
UA = {"User-Agent": "Mozilla/5.0 (academic research; NYU FRE-GY 7871 course project)"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
_G3 = lambda groups: [f"{ix}_{g}" for ix in ("ICS", "ICC", "ICE") for g in groups]  # noqa: E731
COLS = {
    "2n": _G3(["bottom", "middle", "top"]),
    "3n": _G3(["age18_34", "age35_54", "age55p"]),
    "5a": _G3(["NE", "MW", "S", "W"]),          # UMich labels: NE, NC (north central), S, W
    "5b": _G3(["DEM", "IND", "REP"]),
    "7": ["better_income", "better_assets", "better_debt", "worse_income", "worse_prices",
          "worse_assets", "worse_debt"],
    "23": ["news_fav", "news_unfav", "news_none", "news_relative"],
    "24": ["fav_govt", "fav_emp", "fav_high_demand", "fav_low_prices", "fav_easy_credit", "fav_stocks",
           "fav_trade_deficit", "unfav_govt", "unfav_unemp", "unfav_low_demand", "unfav_high_prices",
           "unfav_tight_credit", "unfav_energy", "unfav_stocks", "unfav_trade_deficit"],
    "32": ["px_down", "px_same", "px_up1_2", "px_up3_4", "px_up5", "px_up6_9", "px_up10_14", "px_up15p",
           "px_dk_up", "px_dk_na", "px_total", "px_median", "px_p25", "px_p75", "px_rng", "px_mean",
           "px_var", "px_cases"],
    "36": ["dur_good_prices_low", "dur_good_prices_rising", "dur_good_rates_low", "dur_good_buy_ahead",
           "dur_good_times", "dur_good_supply", "dur_bad_prices_high", "dur_bad_rates_high",
           "dur_bad_cant_afford", "dur_bad_uncertain", "dur_bad_supply"],
    "42": ["house_good_prices_low", "house_good_prices_rising", "house_good_rates_low",
           "house_good_buy_ahead", "house_good_times", "house_good_investment", "house_bad_prices_high",
           "house_bad_rates_high", "house_bad_cant_afford", "house_bad_uncertain", "house_bad_investment"],
}


def _download(url: str, path) -> bytes:
    if path.exists():
        return path.read_bytes()
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    path.write_bytes(r.content)
    return r.content


def indices() -> pd.DataFrame:
    OUT.mkdir(parents=True, exist_ok=True)
    a = pd.read_csv(io.BytesIO(_download(UMICH_FILES + UMICH_CSV["ics"], OUT / UMICH_CSV["ics"])))
    b = pd.read_csv(io.BytesIO(_download(UMICH_FILES + UMICH_CSV["components"], OUT / UMICH_CSV["components"])))
    df = a.merge(b, on=["Month", "YYYY"], how="outer")
    df["month"] = pd.to_datetime(df["Month"] + " " + df["YYYY"].astype(str), format="%B %Y")
    df = df.set_index("month").sort_index()[["ICS_ALL", "ICC", "ICE"]].rename(columns={"ICS_ALL": "ICS"})
    df["preliminary"] = False
    oct26 = pd.Timestamp("2026-10-01")
    if oct26 not in df.index:   # the public CSV has finals only; once the Oct final is posted it is used instead
        df.loc[oct26, ["ICS", "ICC", "ICE"]] = [UMICH_OCT2026_PRELIM[k] for k in ("ICS", "ICC", "ICE")]
        df.loc[oct26, "preliminary"] = True
    return df.sort_index()


def _table_links() -> dict[str, str]:
    page = requests.get(UMICH_TABLES_PAGE, headers=UA, timeout=60).text
    out = {}
    for b in re.split(r'<div class="grid_8 table_name">', page)[1:]:
        m = re.search(r'<span class="table_number">([^<]+)</span>', b)
        rb = re.search(r'href="(get-table\.php\?c=RB[^"]+f=xls[^"]+)"', b)
        if m and rb:
            out[m.group(1).strip()] = "https://data.sca.isr.umich.edu/" + html.unescape(rb.group(1))
    return out


def table(n: str) -> pd.DataFrame:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"table_{n}.xls"
    if not path.exists():
        _download(_table_links()[n], path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        x = pd.read_excel(path, header=None)
    x = x[x[0].astype(str).str.strip().isin(MONTHS) & pd.to_numeric(x[1], errors="coerce").notna()]
    idx = pd.to_datetime(x[0].str.strip() + " " + x[1].astype(float).astype(int).astype(str), format="%B %Y")
    vals = x.iloc[:, 2:2 + len(COLS[n])].apply(pd.to_numeric, errors="coerce")
    assert vals.shape[1] == len(COLS[n]), (n, vals.shape)
    vals.columns = COLS[n]
    vals.index = idx
    vals = vals[~vals.index.duplicated(keep="last")].sort_index()
    return vals


def all_tables() -> pd.DataFrame:
    return pd.concat([table(n) for n in UMICH_TABLES], axis=1).sort_index()


# The five index questions: "Relative" = % favourable - % unfavourable + 100 (UMich), and cases
COMPONENT_TABLES = {   # table: (name, relative column, cases column), positions after Month, Year
    "6": ("X1_fin_now", 7, 8),        # personal finances now vs a year ago
    "8": ("X2_fin_exp", 7, 8),        # expected personal finances a year ahead
    "28": ("X3_bus_1y", 8, 9),        # business conditions over the next year
    "29": ("X4_bus_5y", 7, 8),        # business conditions over the next 5 years
    "35": ("X5_durables", 6, 7),      # buying conditions for large household durables
}


def components() -> pd.DataFrame:
    """X1..X5 relative scores and case counts; ICS is rebuilt from them as a check."""
    OUT.mkdir(parents=True, exist_ok=True)
    links = None
    out = {}
    for n, (name, rel_col, cases_col) in COMPONENT_TABLES.items():
        path = OUT / f"table_{n}.xls"
        if not path.exists():
            links = links or _table_links()
            _download(links[n], path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            x = pd.read_excel(path, header=None)
        x = x[x[0].astype(str).str.strip().isin(MONTHS) & pd.to_numeric(x[1], errors="coerce").notna()]
        idx = pd.to_datetime(x[0].str.strip() + " " + x[1].astype(float).astype(int).astype(str), format="%B %Y")
        rel = pd.to_numeric(x[rel_col], errors="coerce").to_numpy()
        cases = pd.to_numeric(x[cases_col], errors="coerce").to_numpy()
        s = pd.DataFrame({name: rel, f"cases_{n}": cases}, index=idx)
        out[n] = s[~s.index.duplicated(keep="last")]
    df = pd.concat(out.values(), axis=1).sort_index()
    xs = [v[0] for v in COMPONENT_TABLES.values()]
    df["ICS_rebuilt"] = df[xs].sum(axis=1, min_count=5) / 6.7558 + 2.0
    df["ICC_rebuilt"] = df[["X1_fin_now", "X5_durables"]].sum(axis=1, min_count=2) / 2.6424 + 2.0
    df["ICE_rebuilt"] = df[["X2_fin_exp", "X3_bus_1y", "X4_bus_5y"]].sum(axis=1, min_count=3) / 4.1134 + 2.0
    df["cases"] = df["cases_6"]
    return df[xs + ["ICS_rebuilt", "ICC_rebuilt", "ICE_rebuilt", "cases"]]
