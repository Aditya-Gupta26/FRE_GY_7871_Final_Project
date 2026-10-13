"""Swap-test sets for the coder (brief: "Test whether changing political names or source labels alters
classifications of otherwise identical text"). Drawn on text features only.
- Name swap: 200 relevant-looking items that name a party side; Trump<->Biden, Republicans<->Democrats,
  GOP->Democrats, Vance<->Harris (word-boundary map, case kept). Original and swapped versions go to
  different coder batches.
- Source swap: 200 news headlines coded three ways: plain, "Source: Fox News. <headline>",
  "Source: CNN. <headline>"; each version in a different batch.
- Null swap (baseline flip rate): the same 200 source-swap headlines with a neutral prefix
  "Headline: <headline>", which should change nothing.
Every version is in a different batch, shuffled, with fresh item ids, so no coder instance sees
two versions of one text.
    python scripts/06b_make_swaps.py
"""
import _bootstrap  # noqa: F401
import json
import re

import pandas as pd

from src.config import CODED, INTERIM, LABELS, RANDOM_SEED
from src.sampling import make_batches, news_frame, reddit_frame

SWAP = [(r"\bTrump's\b", "Biden's"), (r"\bBiden's\b", "Trump's"), (r"\bTrump\b", "Biden"), (r"\bBiden\b", "Trump"),
        (r"\bRepublicans\b", "Democrats"), (r"\bDemocrats\b", "Republicans"), (r"\bRepublican\b", "Democratic"),
        (r"\bDemocratic\b", "Republican"), (r"\bGOP\b", "Democrats"), (r"\bVance\b", "Harris"), (r"\bHarris\b", "Vance")]
NAMES = re.compile(r"\b(?:Trump|Biden|Republicans?|Democrats?|Democratic|GOP|Vance|Harris)\b")


def swap(text: str) -> str:
    """Simultaneous replacement via placeholders, so Trump->Biden->Trump cannot chain."""
    out, slots = text, []
    for i, (pat, rep) in enumerate(SWAP):
        def put(m, i=i, rep=rep):
            slots.append(rep)
            return f"\u0000{len(slots) - 1}\u0000"
        out = re.sub(pat, put, out)
    return re.sub("\u0000(\\d+)\u0000", lambda m: slots[int(m.group(1))], out)


N = pd.read_parquet(INTERIM / "news.parquet")
R = pd.read_parquet(INTERIM / "reddit.parquet")
NF, RF = news_frame(N), reddit_frame(R)
gold = set(pd.read_csv(LABELS / "gold_key.csv")["doc_id"]) | set(pd.read_csv(LABELS / "dev_key.csv")["doc_id"])
pool = pd.concat([NF, RF])
pool = pool[~pool["doc_id"].isin(gold) & pool["text"].str.contains(NAMES)]
names = pool.sample(n=200, random_state=RANDOM_SEED + 6).copy()
names["swapped"] = names["text"].map(swap)
assert (names["swapped"] != names["text"]).all()
src = NF[~NF["doc_id"].isin(gold) & ~NF["doc_id"].isin(names["doc_id"])].sample(n=200, random_state=RANDOM_SEED + 7)

versions = {
    "W0_name_orig": names.assign(text=names["text"]),
    "W1_name_swap": names.assign(text=names["swapped"]),
    "W2_src_plain": src.assign(text=src["text"]),
    "W3_src_fox": src.assign(text="Source: Fox News. " + src["text"]),
    "W4_src_cnn": src.assign(text="Source: CNN. " + src["text"]),
    "W5_null": src.assign(text="Headline: " + src["text"]),
}
keys = []
for k, (v, df) in enumerate(versions.items()):
    df = df.sample(frac=1, random_state=RANDOM_SEED + 10 + k).reset_index(drop=True)
    df["item_id"] = [f"W{k}{i:04d}" for i in range(len(df))]
    keys.append(df[["item_id", "doc_id"]].assign(version=v))
    make_batches(v, df[["item_id", "text"]], size=200)
pd.concat(keys).to_csv(CODED / "swap_key.csv", index=False)
print({v: len(d) for v, d in versions.items()})
print(names[["text", "swapped"]].head(5).to_string())
