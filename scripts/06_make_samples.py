"""Draw the gold set, the coding tiers and the test-retest set, and write the coder batches.
Seeded; drawn on text features and metadata only (never on any model output). Caps from
config.PREREG["coding_caps"] and the dated note on four outlet groups.
    python scripts/06_make_samples.py
Writes data/labels/gold_{sheet,key}.csv, data/coded/sample_key.csv, data/coded/batches/*_in.jsonl.
"""
import _bootstrap  # noqa: F401
import json

import numpy as np
import pandas as pd

from src.config import END, CODED, INTERIM, LABELS, OUTLET_GROUPS, PREREG, RANDOM_SEED
from src.sampling import make_batches, make_gold, news_frame, period, reddit_frame, write_sheet

CAPS = PREREG["coding_caps"]
N = pd.read_parquet(INTERIM / "news.parquet")
R = pd.read_parquet(INTERIM / "reddit.parquet")
NF, RF = news_frame(N), reddit_frame(R)
dev = pd.read_csv(LABELS / "dev_key.csv")
exclude = set(dev["doc_id"])

# ---------------- gold (450)
if not (LABELS / "gold_sheet.csv").exists():
    gold = write_sheet("gold", make_gold(NF, RF, exclude), "G")
else:
    gold = pd.read_csv(LABELS / "gold_key.csv").merge(pd.read_csv(LABELS / "gold_sheet.csv"), on="item_id")
    print("gold sheet exists: kept as is (never redrawn)")
exclude |= set(gold["doc_id"])
print("gold", len(gold), gold.groupby(["source_type", "period"]).size().to_dict())

rng_seed = RANDOM_SEED + 3


def per_month(F: pd.DataFrame, months, per_group: int, groups) -> pd.DataFrame:
    out = []
    for t in months:
        cell = F[F["survey_month"] == t]
        for g in groups:
            c = cell[cell["group"] == g] if "group" in cell and g in OUTLET_GROUPS else cell[cell["sub"] == g]
            out.append(c.sample(n=min(per_group, len(c)), random_state=rng_seed))
    return pd.concat(out)


NFx = NF[~NF["doc_id"].isin(exclude)]
RFx = RF[~RF["doc_id"].isin(exclude)]
hist_months = pd.date_range("2010-01-01", "2025-12-01", freq="MS")
mon_months = pd.date_range("2026-01-01", END, freq="MS")
tierB_news = per_month(NFx, hist_months, CAPS["history_news_per_month"] // 4, OUTLET_GROUPS).assign(tier="B_news")
tierA_news = per_month(NFx, mon_months, CAPS["news_2026_per_month"] // 4, OUTLET_GROUPS).assign(tier="A_news2026")
# Reddit: split the monthly cap over the three subs (4/3/3 history; 17/17/16 in 2026)
rb = []
for subs_caps, months, tier in [({"Economics": 4, "economy": 3, "personalfinance": 3}, hist_months, "B_reddit"),
                                ({"Economics": 17, "economy": 17, "personalfinance": 16}, mon_months, "A_reddit2026")]:
    for sb, k in subs_caps.items():
        rb.append(per_month(RFx, months, k, [sb]).assign(tier=tier))
tier_reddit = pd.concat(rb)

# release-day items (5 per release, economic term in the headline)
rel = N[(N["pull"] == "release") & N["econ_term"] & ~N["doc_id"].isin(exclude)].copy()
rel = rel[~rel["doc_id"].isin(set(tierA_news["doc_id"]) | set(tierB_news["doc_id"]))]
rel["source_type"] = np.where(rel["group"] == "local", "local", "national")
rel["period"] = period(rel["date"])
rel["text"] = rel["clean"]
# (pandas 3 drops the grouping columns inside groupby().apply(), which once lost release / release_date:
# sample the row labels per group instead, so every column is kept)
picked = rel.groupby(["release", "release_date"]).apply(
    lambda g: list(g.sample(n=min(CAPS["release_day_per_release"], len(g)), random_state=rng_seed).index),
    include_groups=False)
rel_s = rel.loc[[i for ix in picked for i in ix]].assign(tier="A_release")

S = pd.concat([tierB_news, tierA_news, tier_reddit, rel_s], ignore_index=True)
S = S.drop_duplicates("doc_id")
prefix = {"B_news": "H", "A_news2026": "N", "B_reddit": "R", "A_reddit2026": "S", "A_release": "E"}
S["item_id"] = [f"{prefix[t]}{i:05d}" for i, t in enumerate(S["tier"])]
keep = ["item_id", "doc_id", "tier", "source_type", "outlet", "group", "sub", "kind", "date", "survey_month",
        "period", "release", "release_date"]
S[[c for c in keep if c in S]].to_csv(CODED / "sample_key.csv", index=False)
print(S.groupby("tier").size().to_dict(), "total", len(S))

# test-retest: 150 gold items, coded a second time in separate batches
# own item ids (T....), so the second coding can never overwrite the first in the merged codes
retest = gold.sample(n=150, random_state=RANDOM_SEED + 4)[["item_id", "text"]].rename(columns={"item_id": "gold_item_id"})
retest["item_id"] = "T" + retest["gold_item_id"].str[1:]
retest[["item_id", "gold_item_id"]].to_csv(LABELS / "retest_key.csv", index=False)

# coder batches: gold (coded like any other item), the sample, the retest copy
paths = make_batches("gold", gold[["item_id", "text"]], size=150)
paths += make_batches("sample", S[["item_id", "text"]].sample(frac=1, random_state=RANDOM_SEED + 5), size=200)
paths += make_batches("retest", retest[["item_id", "text"]], size=150)
json.dump({"batches": paths, "n_items": {"gold": len(gold), "sample": len(S), "retest": len(retest)}},
          open(CODED / "batches_index.json", "w"), indent=1)
# annotator sheets for the gold set: 5 batches of 90
for b in range(5):
    gold.iloc[b * 90:(b + 1) * 90][["item_id", "text"]].to_csv(LABELS / f"gold_sheet_part{b}.csv", index=False)
print(len(paths), "coder batches")
