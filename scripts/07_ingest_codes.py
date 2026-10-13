"""Validate every returned coder batch and every annotator file, list items to re-send, and merge.
    python scripts/07_ingest_codes.py            # report + write the merged files
    python scripts/07_ingest_codes.py resend     # also write *_resend_in.jsonl batches for failed items
Writes data/coded/codes.parquet (with evidence quotes), data/coded/codes.csv (no text, for git),
data/labels/gold_labels_{A,B}.jsonl checks, outputs/tables/coding_validation.csv.
"""
import _bootstrap  # noqa: F401
import json
import sys
from pathlib import Path

import pandas as pd

from src.coded import as_list, read_jsonl, to_frame, validate
from src.config import CODED, LABELS, TABLES

B = CODED / "batches"
rows, report = [], []
for f_in in sorted(B.glob("*_in.jsonl")):
    name = f_in.name.replace("_in.jsonl", "")
    if name.startswith(("dev_", "minpairs")):
        continue
    items = pd.DataFrame(read_jsonl(f_in))
    outs = sorted(B.glob(name + "_out*.jsonl"))
    got = [r for f in outs for r in read_jsonl(f)]
    # a re-sent item overrides an earlier invalid one: keep the last valid code per item
    ok, probs = validate(items, got, coder=True)
    ok = ok.drop_duplicates("item_id", keep="last") if len(ok) else ok
    fixed = set(ok["item_id"]) if len(ok) else set()
    probs = probs[~probs["item_id"].isin(fixed)] if len(probs) else probs
    report.append({"batch": name, "items": len(items), "valid": len(fixed), "problems": len(probs),
                   "files": len(outs)})
    if len(ok):
        ok["batch"] = name
        rows.append(ok)
    if "resend" in sys.argv and len(probs) and outs:
        bad = items[items["item_id"].isin(probs["item_id"])]
        with (B / f"{name}_resend_in.jsonl").open("w") as fh:
            for _, r in bad.iterrows():
                fh.write(json.dumps({"item_id": r["item_id"], "text": r["text"]}) + "\n")
    if len(probs):
        print(name, probs.to_dict("records")[:5])
rep = pd.DataFrame(report)
rep.to_csv(TABLES / "coding_validation.csv", index=False)
print(rep.to_string())
if rows:
    C = to_frame(pd.concat(rows).to_dict("records"))
    C = C.drop_duplicates("item_id", keep="last")
    C["coder_prompt"] = "prompts/coder_v1.md"
    C["model"] = "claude-opus-5-5"
    C.to_parquet(CODED / "codes.parquet")
    flat = C.drop(columns=["evidence"]).copy()
    flat["topics"] = flat["topics"].map(lambda v: ";".join(as_list(v)))
    flat["claims"] = flat["claims"].map(json.dumps)
    flat.to_csv(CODED / "codes.csv", index=False)
    # item-level outcome: every item sent to a coder (batches with an output), valid at the end or not
    sent = set()
    for f_in in sorted(B.glob("*_in.jsonl")):
        if f_in.name.startswith(("dev_", "minpairs")) or not list(B.glob(f_in.name.replace("_in.jsonl", "_out*.jsonl"))):
            continue
        sent |= {r["item_id"] for r in read_jsonl(f_in)}
    first_pass_problems = int(rep.loc[rep["files"] > 0, "problems"].sum())
    summary = {"items_sent": len(sent), "items_with_valid_code": int(C["item_id"].isin(sent).sum()),
               "items_never_valid": len(sent - set(C["item_id"])),
               "first_pass_problem_items": first_pass_problems,
               "batches_with_output": int((rep["files"] > 0).sum())}
    (TABLES / "coding_summary.json").write_text(json.dumps(summary, indent=1))
    print("codes:", len(C), summary)
