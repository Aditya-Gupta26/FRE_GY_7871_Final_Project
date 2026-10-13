"""Minimal-pair validity suite (CheckList-style; Ribeiro et al. 2020): template texts whose codes are
known by construction, so the coder can be scored without any LLM-made labels. Each item lists the
expected value only for the fields its template controls. Pairs differ in one feature (direction,
level vs rate wording, forecast vs current, credit vs blame, emotional vs plain wording).
"""
from __future__ import annotations

import itertools

import pandas as pd

MONTHS = ["March", "June", "August", "November", "January"]


def build() -> pd.DataFrame:
    rows = []

    def add(text, **exp):
        rows.append({"text": text, "expected": exp, "template": exp.pop("_t")})

    # A. unemployment rate direction (aggregate, current, a claim)
    for x, m in zip([3.6, 3.9, 4.1, 4.4, 4.7, 5.0, 5.8, 6.3, 7.1, 8.5], itertools.cycle(MONTHS)):
        add(f"The unemployment rate rose to {x}% in {m}.", _t="A_unemp", tone="negative", relevant="yes",
            topic_has="layoffs", frame_unit="aggregate", frame_time="current", claim=("unemployment_rate", x))
        add(f"The unemployment rate fell to {x}% in {m}.", _t="A_unemp", tone="positive", relevant="yes",
            topic_has="hiring", frame_unit="aggregate", frame_time="current", claim=("unemployment_rate", x))
    # B. inflation rate wording
    for x, m in zip([1.8, 2.3, 2.7, 3.1, 3.4, 4.2, 5.0, 6.2, 7.5, 9.1], itertools.cycle(MONTHS)):
        add(f"Inflation accelerated to {x}% in {m}, the government said.", _t="B_infl", tone="negative",
            relevant="yes", topic_has="inflation_up", frame_price="rate", frame_unit="aggregate",
            frame_time="current", claim=("inflation", x))
        add(f"Inflation slowed to {x}% in {m}, the government said.", _t="B_infl", tone="positive",
            relevant="yes", topic_has="inflation_down", frame_price="rate", frame_unit="aggregate",
            frame_time="current", claim=("inflation", x))
    # C. price level wording, household focus
    for item in ["grocery bills", "rent payments", "gas prices", "car insurance premiums", "child care costs", "electric bills"]:
        add(f"Families say {item} keep climbing and are squeezing their budgets.", _t="C_level", tone="negative",
            relevant="yes", topic_has="prices_high", frame_price="level", frame_unit="household", frame_time="current")
        add(f"Families say {item} are finally easing and their budgets have some room again.", _t="C_level",
            tone="positive", relevant="yes", topic_has="inflation_down", frame_unit="household", frame_time="current")
    # D. forecast vs current
    for who in ["Economists", "Forecasters", "Bank analysts"]:
        add(f"{who} warn a recession is likely next year.", _t="D_time", tone="negative", relevant="yes",
            topic_has="recession", frame_time="forecast")
        add(f"{who} expect solid growth next year.", _t="D_time", tone="positive", relevant="yes",
            topic_has="growth", frame_time="forecast")
    for verb, tone, topic in [("shrank", "negative", "recession"), ("grew strongly", "positive", "growth")]:
        for src in ["official data show", "the Commerce Department reported", "new figures show"]:
            add(f"The economy {verb} last quarter, {src}.", _t="D_time", tone=tone, relevant="yes",
                topic_has=topic, frame_unit="aggregate", frame_time="current")
    # E. attribution: credit vs blame, by actor
    actors = [("President Trump", "president"), ("President Biden", "president"), ("The Federal Reserve", "fed"),
              ("Congress", "congress"), ("Democrats", "democrats"), ("Republicans", "republicans"),
              ("Oil companies", "business"), ("OPEC", "foreign_trade")]
    for a, tgt in actors:
        add(f"{a} blamed for rising gas prices.", _t="E_attr", tone="negative", relevant="yes",
            attr_target=tgt, attr_dir="blame")
        add(f"{a} credited for falling gas prices.", _t="E_attr", tone="positive", relevant="yes",
            attr_target=tgt, attr_dir="credit")
        add(f"Voters blame {a.replace('The F', 'the F').replace('Oil c', 'oil c')} for higher grocery prices, poll finds.",
            _t="E_attr", tone="negative", relevant="yes", attr_target=tgt, attr_dir="blame")
        add(f"{a} get credit as grocery prices drop, poll finds." if a.endswith("s") and not a.startswith("President")
            else f"{a} gets credit as grocery prices drop, poll finds.",
            _t="E_attr", tone="positive", relevant="yes", attr_target=tgt, attr_dir="credit")
    # F. payrolls
    for n, m in zip([25, 80, 150, 220, 310, 450, 95, 175], itertools.cycle(MONTHS)):
        add(f"The economy added {n},000 jobs in {m}.", _t="F_payrolls", tone="positive", relevant="yes",
            topic_has="hiring", claim=("payrolls", n))
        add(f"The economy lost {n},000 jobs in {m}.", _t="F_payrolls", tone="negative", relevant="yes",
            topic_has="layoffs", claim=("payrolls", -n))
    # G. emotional vs plain wording, same direction
    for emo, plain, tone, topic in [
            ("Grocery prices soar again", "Grocery prices rise again", "negative", "prices_high"),
            ("Stocks plunge on recession fears", "Stocks fall on recession fears", "negative", "markets"),
            ("Unemployment skyrockets in Ohio", "Unemployment rises in Ohio", "negative", "layoffs"),
            ("Rents explode in big cities", "Rents increase in big cities", "negative", "housing"),
            ("Hiring booms as companies scramble for workers", "Hiring picks up as companies look for workers", "positive", "hiring"),
            ("Mortgage rates crash to record lows", "Mortgage rates fall to low levels", "positive", "rates")]:
        add(emo + ".", _t="G_emotion", tone=tone, relevant="yes", topic_has=topic, emotional=1)
        add(plain + ".", _t="G_emotion", tone=tone, relevant="yes", topic_has=topic, emotional=0)
    # H. not relevant
    for t in ["Best deals on TVs this weekend at major retailers", "Steve Jobs biography tops the bestseller list",
              "Local high school team wins state football title", "Ten easy recipes for a quick weeknight dinner",
              "New superhero movie breaks opening weekend record", "How to train your puppy to sit and stay",
              "Celebrity couple announces engagement on vacation", "City council renames park after war hero",
              "Scientists discover new species of frog in the rainforest", "Should I use a Roth or traditional IRA for retirement?"]:
        add(t + ".", _t="H_irrelevant", relevant="no")
    # I. personal experience (household)
    for t, tone, topic in [("I got laid off last week and can't find any work", "negative", "layoffs"),
                           ("My hours were cut again and I am falling behind on bills", "negative", "income"),
                           ("Just got a raise that finally beats inflation", "positive", "income"),
                           ("Finally landed a new job with better pay after months of searching", "positive", "hiring"),
                           ("Our rent went up 20% this year and we might have to move", "negative", "housing"),
                           ("Paid off my credit card for the first time thanks to lower gas prices", "positive", "inflation_down")]:
        add(t + ".", _t="I_household", tone=tone, relevant="yes", topic_has=topic, frame_unit="household")
    d = pd.DataFrame(rows)
    d["item_id"] = [f"M{i:04d}" for i in range(len(d))]
    return d[["item_id", "text", "template", "expected"]]


def score(d: pd.DataFrame, codes: pd.DataFrame) -> pd.DataFrame:
    """Accuracy per field and template; codes has the coder's fields by item_id."""
    c = codes.set_index("item_id")
    out = []
    for _, r in d.iterrows():
        if r["item_id"] not in c.index:
            continue
        got = c.loc[r["item_id"]]
        for k, v in r["expected"].items():
            if k == "topic_has":
                ok = v in list(got["topics"] if got["topics"] is not None else [])
            elif k == "claim":
                ok = any(cl.get("indicator") == v[0] and abs(float(cl.get("value", 1e9)) - v[1]) < 1e-6
                         for cl in list(got["claims"] if got["claims"] is not None else []))
            else:
                ok = got.get(k) == v
            out.append({"item_id": r["item_id"], "template": r["template"], "field": k, "ok": bool(ok)})
    return pd.DataFrame(out)
