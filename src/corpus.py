"""Build the cleaned news and Reddit corpora with the filter waterfall.

News (Google News RSS headlines; a date, no time):
  title cleaned (the " - Outlet" suffix Google appends is removed, HTML unescaped);
  kept if the item's source is the queried outlet (site: pulls), dated inside the window (one
  day of slack for the GMT stamp), English, not promotional, at least 4 words, and not an exact
  or near duplicate (MinHash, Jaccard >= 0.8) of an earlier headline from the same outlet.
  The same headline at several outlets (wire copy) is kept and flagged `syndicated`.
  `econ_term` marks headlines with an economic term (config.ECON_RE) in the title itself; the
  coding samples are drawn from these.
Reddit posts (title + start of body): not removed or deleted, English, an economic term in the
  text, not promotional, at least 5 words, score >= 1, not a bot (AutoModerator, or > 20 posts a
  day in the sample), not a duplicate or crosspost, at most 5 posts per author per day.
Each doc gets `survey_month`: the Michigan month whose media window [day 15 of t-1, day 15 of t)
contains its date.
"""
from __future__ import annotations

import hashlib
import re
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from src import news, reddit
from src.config import (BOT_MAX_POSTS_PER_DAY, ECON_RE, ET, MAX_PER_AUTHOR_DAY, MIN_WORDS, NEAR_DUP_JACCARD,
                        OUTLETS, PROMO_RE, RD_MIN_SCORE)
from src.text_clean import ascii_ratio, dedup_key, near_duplicate_mask, normalize

ECON = re.compile(ECON_RE, re.I)
PROMO = re.compile(PROMO_RE, re.I)
AUTOMOD = reddit._hash_author("AutoModerator")


def survey_month(d: pd.Series) -> pd.Series:
    d = pd.to_datetime(d)
    first = d.dt.to_period("M").dt.start_time
    return first.where(d.dt.day < 15, first + pd.offsets.MonthBegin(1))


def _site_of(href: str | None) -> str:
    if not href:
        return ""
    host = urlparse(href).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _match_outlet(host: str) -> str | None:
    for s in OUTLETS:
        if host == s or host.endswith("." + s):
            return s
    return None


def build_news() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = news.load_raw()
    W = [("downloaded items", len(raw))]
    d = raw.copy()
    d["title_raw"] = d["title"].fillna("")
    d["clean"] = [normalize(t[: -len(" - " + s)] if s and t.endswith(" - " + s) else t)
                  for t, s in zip(d["title_raw"], d["source"].fillna(""))]
    d["clean"] = d["clean"].str.replace(r"\s*\(Published \d{4}\)\s*$", "", regex=True)
    d["opinion"] = d["clean"].str.match(r"^(?:Opinion|Perspective|Editorial|Analysis|Column|Commentary)\s*[|:]", case=False)
    d["date"] = pd.to_datetime([parsedate_to_datetime(p).astimezone(ET).strftime("%Y-%m-%d")
                                if p else None for p in d["published"]], errors="coerce")
    d["host"] = d["source_href"].map(_site_of)
    d["outlet"] = d["host"].map(_match_outlet)
    # site: pulls must return the queried outlet; release-day pulls keep any outlet
    on_site = (d["pull"] == "release") | (d["outlet"] == d["query_site"])
    d = d[on_site]
    W.append(("source is the queried outlet (site: pulls)", len(d)))
    lo = pd.to_datetime(d["win_since"]) - pd.Timedelta(days=1)
    hi = pd.to_datetime(d["win_until"])
    d = d[(d["date"] >= lo) & (d["date"] <= hi)]
    W.append(("dated inside its window (+-1 day)", len(d)))
    d = d[d["clean"].map(ascii_ratio) >= 0.8]
    W.append(("English (ASCII letters >= 80%)", len(d)))
    d = d[~d["clean"].str.contains(PROMO)]
    W.append(("not promotional", len(d)))
    d = d[d["clean"].str.split().str.len() >= 4]
    W.append(("at least 4 words", len(d)))
    d["dkey"] = d["clean"].map(dedup_key)
    d["outlet_key"] = d["outlet"].fillna(d["host"])
    # site pulls first, so release-day pulls (added later) can never displace a site-pull item
    d["pull_rank"] = d["pull"].map({"history": 0, "weekly": 1, "release": 2})
    d = d.sort_values(["pull_rank", "date"]).drop_duplicates(["outlet_key", "dkey"])
    W.append(("not an exact duplicate within outlet", len(d)))
    keep = []
    for _, g in d.groupby("outlet_key", sort=False):
        m = near_duplicate_mask(g["dkey"].tolist(), threshold=NEAR_DUP_JACCARD)
        keep.append(g[~np.array(m)])
    d = pd.concat(keep)
    W.append(("not a near duplicate within outlet (MinHash 0.8)", len(d)))
    d["syndicated"] = d.duplicated("dkey", keep=False)
    d["econ_term"] = d["clean"].str.contains(ECON)
    meta = d["outlet"].map(lambda s: OUTLETS.get(s, ("other", "other", "other")) if s else ("other", "other", "other"))
    d["group"], d["otype"], d["region"] = zip(*meta)
    d["doc_id"] = "n_" + d["link"].map(lambda u: hashlib.sha1(u.encode()).hexdigest()[:12])
    d = d.sort_values(["pull_rank", "date"]).drop_duplicates("doc_id")
    d["survey_month"] = survey_month(d["date"])
    W.append(("final headlines (unique links)", len(d)))
    W.append(("  of which with an economic term in the title (coding frame)", int(d["econ_term"].sum())))
    cols = ["doc_id", "pull", "outlet", "host", "group", "otype", "region", "date", "survey_month", "clean",
            "title_raw", "source", "link", "syndicated", "econ_term", "opinion", "release", "release_date", "n_in_window"]
    return d[cols].sort_values("date").reset_index(drop=True), pd.DataFrame(W, columns=["step", "n"])


def build_reddit() -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.DataFrame(reddit.load_raw())
    W = [("downloaded posts", len(d))]
    d = d.drop_duplicates("id")
    W.append(("unique posts", len(d)))
    d["selftext"] = d["selftext"].fillna("")
    removed = d["selftext"].isin(["[removed]", "[deleted]"]) | d["author"].isin(["[deleted]", "[removed]"]) | d["author"].isna()
    d = d[~removed]
    W.append(("not removed or deleted", len(d)))
    title = d["title"].fillna("").str.strip()
    body = d["selftext"].str.strip()
    same = pd.Series([b == ti or (len(ti) > 0 and b.startswith(ti)) for b, ti in zip(body, title)], index=d.index)
    d["clean"] = np.where(same | (body == ""), np.where(body == "", title, body), title + ". " + body)
    d["clean"] = d["clean"].map(normalize).str.strip(". ")
    d = d[d["clean"].map(ascii_ratio) >= 0.8]
    W.append(("English (ASCII letters >= 80%)", len(d)))
    d = d[d["clean"].str.contains(ECON)]
    W.append(("an economic term in the text", len(d)))
    d = d[~d["clean"].str.contains(PROMO)]
    W.append(("not promotional", len(d)))
    d = d[d["clean"].str.split().str.len() >= MIN_WORDS]
    W.append((f"at least {MIN_WORDS} words", len(d)))
    d["score"] = pd.to_numeric(d["score"], errors="coerce")
    d = d[d["score"] >= RD_MIN_SCORE]
    W.append((f"score >= {RD_MIN_SCORE}", len(d)))
    d["ts"] = pd.to_datetime(d["created_utc"].astype(int), unit="s", utc=True)
    d["date"] = d["ts"].dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    per_day = d.groupby(["author", "date"])["id"].transform("count")
    d = d[(d["author"] != AUTOMOD) & (per_day <= BOT_MAX_POSTS_PER_DAY)]
    W.append(("not a bot (AutoModerator, > 20 posts a day)", len(d)))
    d = d.sort_values("ts")
    d["dkey"] = d["title"].fillna("").map(normalize).map(dedup_key)
    d = d.drop_duplicates("dkey")
    W.append(("not an exact duplicate or crosspost (title)", len(d)))
    d = d[~np.array(near_duplicate_mask(d["clean"].map(dedup_key).tolist(), threshold=NEAR_DUP_JACCARD))]
    W.append(("not a near duplicate (MinHash 0.8)", len(d)))
    d = d[d.groupby(["author", "date"]).cumcount() < MAX_PER_AUTHOR_DAY]
    W.append((f"at most {MAX_PER_AUTHOR_DAY} posts per author per day", len(d)))
    d["kind"] = np.where(d["url"].fillna("").str.contains(r"reddit\.com/r/|redd\.it/gallery|^$", regex=True),
                         "self", "link")
    d["doc_id"] = "r_" + d["id"].astype(str)
    d["survey_month"] = survey_month(d["date"])
    d["sub"] = d["subreddit"]
    cols = ["doc_id", "sub", "kind", "author", "ts", "date", "survey_month", "clean", "title", "score",
            "num_comments", "url", "window_start", "window_limit"]
    return d[cols].reset_index(drop=True), pd.DataFrame(W, columns=["step", "n"])
