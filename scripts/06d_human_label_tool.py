"""Gold-set relabelling tool (brief section 3). Two modes, from the frozen guide and the gold sheet:
    python scripts/06d_human_label_tool.py
Review mode: when the model labels data/labels/gold_prelabels_{sonnet,haiku}_part*.jsonl exist (Sonnet 5.5
as pass A, Haiku 5.5 as pass B, each labelling all 450 items alone with prompts/annotator.md, in its own context
with only the guide and its sheet), the tool shows each pass pre-filled and the reviewer checks every item,
correcting what they disagree with; it records per item whether it was confirmed, which fields changed and the
seconds spent. Exports human_verified_{A,B}.jsonl. Writes data/labels/human/review_tool.html.
Plain mode (no model labels): two people label blind, with a 10-item practice round; writes label_tool.html.
Both modes compare two exports and adjudicate the items that still differ (human_adjudicated.jsonl).
The html holds headline and post text, so it is git-ignored like the sheets; the exports carry no text.
The gold order is fixed (order_key.csv): every prefix keeps the source x period design, and the first 300 (the
brief's minimum) hold two-thirds of every cell.
"""
import _bootstrap  # noqa: F401
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from markdown_it import MarkdownIt

from src.coded import read_jsonl
from src.config import LABELS, RANDOM_SEED

HUMAN = LABELS / "human"
HUMAN.mkdir(exist_ok=True)
TEMPLATE = Path(__file__).with_name("label_tool_template.html")
MIN_ITEMS = 300
N_PRACTICE = 10

# ---------------- gold order: spread every source x period cell evenly along the sequence
g = pd.read_csv(LABELS / "gold_sheet.csv").merge(
    pd.read_csv(LABELS / "gold_key.csv")[["item_id", "source_type", "period"]], on="item_id")
rng = np.random.default_rng(RANDOM_SEED + 20)
g["u"] = rng.random(len(g))
g = g.sort_values("u")
cell = g.groupby(["source_type", "period"])
g["pos"] = (cell.cumcount() + 0.5) / cell["item_id"].transform("size")
g = g.sort_values(["pos", "u"]).reset_index(drop=True)
g["order"] = np.arange(1, len(g) + 1)
g["in_first_300"] = g["order"] <= MIN_ITEMS
g[["item_id", "order", "source_type", "period", "in_first_300"]].to_csv(HUMAN / "order_key.csv", index=False)
first = g[g["in_first_300"]]
print("first 300 by cell:", first.groupby(["source_type", "period"]).size().to_dict())

# ---------------- practice: dev items (used to tune the coder prompt, never in the gold set; national and Reddit only), 6 + 4
dev = pd.read_csv(LABELS / "dev_sheet.csv").merge(pd.read_csv(LABELS / "dev_key.csv")[["item_id", "source_type"]], on="item_id")
practice = pd.concat([dev[dev["source_type"] == s].sample(n=k, random_state=RANDOM_SEED + 21)
                      for s, k in [("national", 6), ("reddit", 4)]])
practice = practice.sample(frac=1, random_state=RANDOM_SEED + 22)
assert len(practice) == N_PRACTICE and not set(practice["item_id"]) & set(g["item_id"])

# ---------------- guide: the frozen labelling guide, rendered
guide_md = (LABELS / "LABELLING_GUIDE.md").read_text()
version = re.search(r"\*\*Version ([\d.]+)", guide_md).group(1)
guide_html = MarkdownIt("commonmark").enable("table").render(guide_md)

payload = {
    "guide_version": version,
    "guide_html": guide_html,
    "min_items": MIN_ITEMS,
    "sets": {"gold": [{"id": r.item_id, "text": r.text} for r in g.itertuples()],
             "practice": [{"id": r.item_id, "text": r.text} for r in practice.itertuples()]},
}
# ---------------- review mode: each pass pre-filled with one model's labels
PASSES = {"A": ("sonnet", "Sonnet 5.5"), "B": ("haiku", "Haiku 5.5")}
pre = {role: {r["item_id"]: r for f in sorted(LABELS.glob(f"gold_prelabels_{m}_part*.jsonl")) for r in read_jsonl(f)}
       for role, (m, _) in PASSES.items()}
review = all(set(v) == set(g["item_id"]) for v in pre.values())
if review:
    payload["prelabels"] = pre
    payload["pass_model"] = {role: name for role, (_, name) in PASSES.items()}
out = HUMAN / ("review_tool.html" if review else "label_tool.html")
data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
tpl = TEMPLATE.read_text()
assert tpl.count("/*__DATA__*/null") == 1
out.write_text(tpl.replace("/*__DATA__*/null", data))
print("wrote", out, f"({len(g)} gold items; review mode: {review})")
