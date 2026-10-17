"""Adjudication sheets for the gold set: every item where pass A (Sonnet 5.5, with my corrections) and pass B
(Haiku 5.5, with my corrections) differ on any field (topics and claims compared as sets). The two labels are
shown in a seeded random order as label_1 / label_2, with no names, to an adjudicator that labelled neither pass
and is not the coder being validated (Claude Fable 5.1, prompts/adjudicator.md).
    python scripts/06c_make_adjudication.py
Writes data/labels/adjudicate_sheet_{k}.jsonl (up to 90 items each; they hold text, so git-ignored) and
adjudicate_key.csv (which pass is label_1).
"""
import _bootstrap  # noqa: F401
import json

import numpy as np
import pandas as pd

from src.coded import validate
from src.config import LABELS, RANDOM_SEED
from src.gold import load_pass

FIELDS = ["relevant", "tone", "emotional", "frame_price", "frame_unit", "frame_time", "attr_target", "attr_dir"]
sheet = pd.read_csv(LABELS / "gold_sheet.csv")
A, B = load_pass("A"), load_pass("B")
okA, pA = validate(sheet, A, coder=False)
okB, pB = validate(sheet, B, coder=False)
assert len(pA) == 0 and len(pB) == 0, (pA.head(), pB.head())
a, b = okA.set_index("item_id"), okB.set_index("item_id")


def norm(r):
    return {**{f: r[f] for f in FIELDS}, "topics": sorted(r["topics"] or []),
            "claims": sorted([(c["indicator"], round(float(c["value"]), 6)) for c in (r["claims"] or [])])}


rng = np.random.default_rng(RANDOM_SEED + 8)
rows, key = [], []
for iid in sheet["item_id"]:
    ra, rb = a.loc[iid].to_dict(), b.loc[iid].to_dict()
    if norm(ra) != norm(rb):
        flip = bool(rng.integers(0, 2))
        l1, l2 = (rb, ra) if flip else (ra, rb)
        strip = lambda r: {k: r[k] for k in FIELDS + ["topics", "claims"]}  # noqa: E731
        rows.append({"item_id": iid, "text": sheet.set_index("item_id").loc[iid, "text"],
                     "label_1": strip(l1), "label_2": strip(l2)})
        key.append({"item_id": iid, "label_1_is": "B" if flip else "A"})
for old in LABELS.glob("adjudicate_sheet_*.jsonl"):
    old.unlink()
for k in range(0, len(rows), 90):
    with (LABELS / f"adjudicate_sheet_{k // 90}.jsonl").open("w") as f:
        for r in rows[k:k + 90]:
            f.write(json.dumps(r, default=str) + "\n")
pd.DataFrame(key).to_csv(LABELS / "adjudicate_key.csv", index=False)
print(len(rows), "items to adjudicate in", (len(rows) + 89) // 90, "sheets")
