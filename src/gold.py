"""The two annotator passes of the gold set.

I couldn't find other annotators, so each pass is one model's labels plus my corrections: pass A is Claude Sonnet 5.5
and pass B is Claude Haiku 5.5, each labelling all 450 items in its own context with prompts/annotator.md and
the guide only (data/labels/gold_prelabels_{sonnet,haiku}_part*.jsonl). My corrections (12 items in A, 15 in B),
each with its reason, are data/labels/human/human_verified_{A,B}.jsonl; every other label is kept as the model
gave it.
"""
from __future__ import annotations

from src.coded import read_jsonl
from src.config import LABELS

PASSES = {"A": ("sonnet", "Claude Sonnet 5.5"), "B": ("haiku", "Claude Haiku 5.5")}
KEYS = ["item_id", "relevant", "tone", "emotional", "topics", "frame_price", "frame_unit", "frame_time", "claims",
        "attr_target", "attr_dir"]


def model_labels(role: str) -> list[dict]:
    """The model's own labels for one pass, in sheet order."""
    m = PASSES[role][0]
    return [{k: r[k] for k in KEYS} for f in sorted(LABELS.glob(f"gold_prelabels_{m}_part*.jsonl")) for r in read_jsonl(f)]


def corrections(role: str) -> list[dict]:
    """My corrected items for one pass (with changed fields and reason), or [] before the review."""
    f = LABELS / "human" / f"human_verified_{role}.jsonl"
    return read_jsonl(f) if f.exists() else []


def load_pass(role: str) -> list[dict]:
    """One annotator pass: the model's labels with my corrections applied."""
    fix = {r["item_id"]: {k: r[k] for k in KEYS} for r in corrections(role)}
    return [fix.get(r["item_id"], r) for r in model_labels(role)]
