"""Adjudication sheets for the gold set: every item where annotators A and B differ on any field
(topics and claims compared as sets). The two labels are shown in a seeded random order as
label_1 / label_2, with no annotator names.
    python scripts/06c_make_adjudication.py
Writes data/labels/adjudicate_sheet_{k}.jsonl (up to 120 items each) and adjudicate_key.csv.
"""
import _bootstrap  # noqa: F401
import json

import numpy as np
import pandas as pd

from src.coded import read_jsonl, validate
from src.config import LABELS, RANDOM_SEED

FIELDS = ["relevant", "tone", "emotional", "frame_price", "frame_unit", "frame_time", "attr_target", "attr_dir"]
sheet = pd.read_csv(LABELS / "gold_sheet.csv")
A = [r for f in sorted(LABELS.glob("gold_labels_A_part*.jsonl")) for r in read_jsonl(f)]
B = [r for f in sorted(LABELS.glob("gold_labels_B_part*.jsonl")) for r in read_jsonl(f)]
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
for k in range(0, len(rows), 120):
    with (LABELS / f"adjudicate_sheet_{k // 120}.jsonl").open("w") as f:
        for r in rows[k:k + 120]:
            f.write(json.dumps(r, default=str) + "\n")
pd.DataFrame(key).to_csv(LABELS / "adjudicate_key.csv", index=False)
print(len(rows), "items to adjudicate in", (len(rows) + 119) // 120, "sheets")
