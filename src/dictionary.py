"""Dictionary baseline (no AI): Loughran and McDonald (2011) word lists for tone, and fixed keyword
rules for relevance, topics, frames, emotional wording, attribution and numerical claims.

LM lists come from the master-dictionary file used in Assignment 1 (data/raw/lexicons); a word is
in a list if its column is non-zero (A1's rule: 2,355 negative and 354 positive words; the
-2020 entries mark words dropped in 2020 and are kept, as in A1). Tone: net = #positive - #negative
LM words; positive if net > 0, negative if net < 0, else neutral. The keyword rules were written
before any gold label was seen and are not tuned on them.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from src.config import ECON_RE, RAW

TOK = re.compile(r"[a-z]+(?:'[a-z]+)?")
_LM = None


def lm_sets() -> tuple[set[str], set[str]]:
    global _LM
    if _LM is None:
        m = pd.read_csv(RAW / "lexicons" / "LoughranMcDonald_MasterDictionary.csv", encoding="utf-8-sig")
        neg = set(m.loc[m["Negative"].fillna(0) != 0, "Word"].str.lower())
        pos = set(m.loc[m["Positive"].fillna(0) != 0, "Word"].str.lower())
        _LM = (neg, pos)
    return _LM


R = lambda p: re.compile(p, re.I)  # noqa: E731
TOPIC_RULES = {
    "layoffs": R(r"\b(?:layoffs?|laid off|lay off|job cuts?|cuts? \d+[,\d]* jobs|lost [\d,]+ jobs|jobless claims (?:rise|jump|climb)|"
                 r"unemployment (?:rises|rose|jumps|climbs|up)|fired|firings|job losses)\b"),
    "hiring": R(r"\b(?:hiring|hires?|added [\d,]+ jobs|adds [\d,]+ jobs|job gains?|unemployment (?:falls|fell|drops|down)|"
                r"jobs report beats|strong labor market|new jobs)\b"),
    "prices_high": R(r"\b(?:cost of living|afford\w*|expensive|pricier|higher prices|prices? (?:soar|surge|climb|jump|rise|rising|up)|"
                     r"grocery (?:bills|prices)|gas prices|rent (?:hikes?|increases?)|price gouging|sticker shock)\b"),
    "inflation_up": R(r"\b(?:inflation (?:rises|rose|jumps|accelerat\w*|heats? up|hotter|surges?|climbs?|up)|"
                      r"hotter[- ]than[- ]expected|(?:cpi|inflation) (?:beats|tops))\b"),
    "inflation_down": R(r"\b(?:inflation (?:cools?|eases?|slows?|falls?|fell|drops?|declines?|moderat\w*)|disinflation|"
                        r"prices? (?:fall|drop|ease|decline|cool)\w*|deflation)\b"),
    "growth": R(r"\b(?:econom\w* (?:grows?|grew|expands?|booms?)|gdp (?:grows?|grew|rises?|beats)|growth|boom|"
                r"strong economy|robust economy)\b"),
    "recession": R(r"\b(?:recession\w*|downturn|slowdown|contraction|econom\w* (?:shrinks?|shrank|contracts?|slows?)|"
                   r"gdp (?:falls?|shrinks?|contracts?|declines?))\b"),
    "rates": R(r"\b(?:interest rates?|rate (?:hikes?|cuts?)|the fed\b|federal reserve|fomc|mortgage rates?|borrowing costs?|powell|yellen|warsh)\b"),
    "tariffs": R(r"\b(?:tariffs?|trade war|import tax\w*|duties)\b"),
    "housing": R(r"\b(?:housing|home prices?|house prices?|rents?|rental|mortgages?|homebuyers?|real estate)\b"),
    "markets": R(r"\b(?:stocks?|stock market|dow|s&p|nasdaq|wall street|401\(?k\)?|shares)\b"),
    "income": R(r"\b(?:wages?|salar\w+|pay (?:raise|cut)|paychecks?|raises?|earnings|income\w*)\b"),
}
LEVEL = R(r"\b(?:cost of living|afford\w*|expensive|pricier|bills?|price of|prices? (?:are|remain|still) high|"
          r"\$\d|higher than (?:before|in 20\d\d)|budgets?)\b")
RATE = R(r"\b(?:inflation rate|inflation (?:rose|rises|fell|falls|slowed|slows|cools|cooled|accelerat\w*|eases?)|"
         r"\d+(?:\.\d+)?\s?%|percent|cpi|pce|consumer price index)\b")
HOUSEHOLD = R(r"\b(?:famil(?:y|ies)|households?|consumers?|shoppers?|workers?|americans|parents|renters|"
              r"homeowners|you|your|i|my|me|we|our)\b")
AGGREGATE = R(r"\b(?:economy|gdp|nationwide|national|jobs report|payrolls|unemployment rate|inflation rate|"
              r"data show|labor department|commerce department|government (?:said|reported))\b")
FORECAST = R(r"\b(?:will|could|may|might|expected? to|expects?|forecasts?|predict\w*|warns?|outlook|next year|"
             r"coming months|likely|projected|risk of)\b")
EMOTION = R(r"\b(?:soar\w*|skyrocket\w*|plunge\w*|plummet\w*|crash\w*|brutal|crisis|nightmare|devastat\w*|"
            r"slam\w*|bloodbath|boom\w*|stunning|shock\w*|explod\w*|crushing|meltdown|panic|chaos|disaster|"
            r"historic|massive|staggering)\b|!")
ACTORS = [("president", R(r"\b(?:president|trump\w*|biden\w*|obama\w*|white house|administration)\b")),
          ("fed", R(r"\b(?:the fed|federal reserve|powell|yellen|warsh|bernanke)\b")),
          ("congress", R(r"\bcongress\w*\b")),
          ("democrats", R(r"\b(?:democrats?|dems)\b")),
          ("republicans", R(r"\b(?:republicans?|gop)\b")),
          ("business", R(r"\b(?:corporat\w+|companies|greed\w*|landlords?|banks?|oil companies)\b")),
          ("foreign_trade", R(r"\b(?:china|opec|imports?|trade partners?|war)\b"))]
BLAME = R(r"\b(?:blame\w*|fault|caused?|because of|due to|thanks to|responsible)\b")
CREDIT = R(r"\b(?:credit\w*|touts?|praise\w*|takes? credit|thanks to)\b")
CLAIM_RE = [
    ("unemployment_rate", R(r"(?:unemployment|jobless) rate[^.%]{0,40}?(\d+(?:\.\d+)?)\s?(?:%|percent)")),
    ("inflation", R(r"(?:inflation|cpi|consumer prices|pce)[^.%]{0,40}?(\d+(?:\.\d+)?)\s?(?:%|percent)")),
    ("gdp_growth", R(r"(?:gdp|economy) (?:grew|grows|expanded|shrank|rose|fell)[^.%]{0,30}?(\d+(?:\.\d+)?)\s?(?:%|percent)")),
    ("payrolls", R(r"(?:added|adds|lost|loses|created|shed)\s+([\d,]+)(?:,000| thousand|k)?\s+jobs")),
]
ECON = re.compile(ECON_RE, re.I)


def code(texts: pd.Series) -> pd.DataFrame:
    neg, pos = lm_sets()
    out = []
    for t in texts.astype(str):
        toks = TOK.findall(t.lower())
        n_neg, n_pos = sum(w in neg for w in toks), sum(w in pos for w in toks)
        net = n_pos - n_neg
        topics = [k for k, r in TOPIC_RULES.items() if r.search(t)]
        price = bool({"prices_high", "inflation_up", "inflation_down"} & set(topics))
        lv, rt = bool(LEVEL.search(t)), bool(RATE.search(t))
        fp = ("level" if lv and not rt else "rate" if rt and not lv else "level" if lv and rt else "none") if price else "none"
        hh, ag = bool(HOUSEHOLD.search(t)), bool(AGGREGATE.search(t))
        fu = "household" if hh else "aggregate" if ag else "none"
        ft = "forecast" if FORECAST.search(t) else "current"
        tgt = next((k for k, r in ACTORS if r.search(t)), "none")
        if tgt != "none" and BLAME.search(t):
            ad = "blame"
        elif tgt != "none" and CREDIT.search(t):
            ad = "credit"
        else:
            ad, tgt = "none", "none"
        claims = []
        for ind, r in CLAIM_RE:
            for m in r.finditer(t):
                v = float(m.group(1).replace(",", ""))
                if ind == "payrolls":
                    v = v / 1000 if v >= 1000 else v
                    if re.search(r"\b(?:lost|loses|shed)\b", m.group(0), re.I):
                        v = -v
                claims.append({"indicator": ind, "value": v})
        out.append({"relevant": "yes" if ECON.search(t) else "no",
                    "tone": "positive" if net > 0 else "negative" if net < 0 else "neutral",
                    "lm_neg": n_neg, "lm_pos": n_pos, "n_tokens": len(toks),
                    "emotional": int(bool(EMOTION.search(t))), "topics": topics, "frame_price": fp,
                    "frame_unit": fu, "frame_time": ft, "attr_target": tgt, "attr_dir": ad, "claims": claims})
    return pd.DataFrame(out, index=texts.index)
