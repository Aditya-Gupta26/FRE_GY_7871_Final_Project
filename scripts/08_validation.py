"""Validation of the AI measurement (brief section 3): annotator agreement, the adjudicated gold set,
the Opus coder vs gold by class, source and period, the dictionary and TF-IDF baselines, test-retest,
the swap tests and the minimal-pair suite.
    python scripts/08_validation.py
Inputs: data/labels/gold_{sheet,key}.csv; the two annotator passes (src.gold: Sonnet 5.5 and Haiku 5.5 labels,
gold_prelabels_*.jsonl, with my corrections, human/human_verified_{A,B}.jsonl); gold_adjudicated*.jsonl (the
Fable 5.1 adjudicator); data/coded/codes.parquet, retest_key.csv, swap_key.csv, the minimal-pair outputs.
Writes outputs/results_validation.json and outputs/tables/val_*.csv; data/labels/gold_final.csv.
"""
import _bootstrap  # noqa: F401
import json

import numpy as np
import pandas as pd
from scipy import stats

from src.baselines import cv_predict, train
from src.coded import TOPICS, as_list, read_jsonl, to_frame, validate
from src.config import CODED, LABELS, OUTPUTS, TABLES
from src.dictionary import code as dict_code
from src.gold import PASSES, corrections, load_pass, model_labels
from src.minimal_pairs import build as mp_build, score as mp_score
from src.validate import accuracy, agreement, claim_f1

FIELDS = ["relevant", "tone", "emotional", "frame_price", "frame_unit", "frame_time", "attr_target", "attr_dir"]
OUT = {}


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    c = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    m = (p + z * z / (2 * n)) / (1 + z * z / n)
    return (float(m - c), float(m + c))


def load_parts(pattern):
    rows = []
    for f in sorted(LABELS.glob(pattern)):
        rows += read_jsonl(f)
    return rows


def claimset(cl):
    return frozenset((c["indicator"], round(float(c["value"]), 6)) for c in as_list(cl))


# ---------------- 1. gold: annotator passes A and B, agreement, adjudication
sheet = pd.read_csv(LABELS / "gold_sheet.csv")
key = pd.read_csv(LABELS / "gold_key.csv")
# the models' own labels before my corrections: the only fully independent pair, so the main reliability figure
MA = to_frame(model_labels("A")).set_index("item_id")
MB = to_frame(model_labels("B")).set_index("item_id")
pre = [agreement(MA[f], MB[f], f) for f in FIELDS]
pd.DataFrame(pre).to_csv(TABLES / "val_agreement_models_prereview.csv", index=False)
OUT["agreement_models_prereview"] = pre
OUT["models"] = {r: PASSES[r][1] for r in PASSES}
FIX_FIELDS = FIELDS + ["topics", "claims"]
OUT["review_corrections"] = {r: {"n_items": len(corrections(r)), "n_total": len(MA),
                                 "fields": {f: sum(f in c.get("changed", []) for c in corrections(r)) for f in FIX_FIELDS}}
                             for r in PASSES}
A_rows, B_rows = load_pass("A"), load_pass("B")
okA, pA = validate(sheet, A_rows, coder=False)
okB, pB = validate(sheet, B_rows, coder=False)
OUT["annotator_validation"] = {"A_valid": len(okA), "A_problems": pA.to_dict("records"),
                               "B_valid": len(okB), "B_problems": pB.to_dict("records")}
A = to_frame(okA.to_dict("records")).set_index("item_id")
Bn = to_frame(okB.to_dict("records")).set_index("item_id")
ids = A.index.intersection(Bn.index)
A, Bn = A.loc[ids], Bn.loc[ids]
agr = [agreement(A[f], Bn[f], f) for f in FIELDS]
rel = (A["relevant"] == "yes") & (Bn["relevant"] == "yes")
for t in TOPICS:
    if A.loc[rel, f"t_{t}"].sum() + Bn.loc[rel, f"t_{t}"].sum() >= 10:
        a = agreement(A.loc[rel, f"t_{t}"], Bn.loc[rel, f"t_{t}"], f"topic:{t}")
        a["prevalence"] = float((A.loc[rel, f"t_{t}"].mean() + Bn.loc[rel, f"t_{t}"].mean()) / 2)
        both = (A.loc[rel, f"t_{t}"] + Bn.loc[rel, f"t_{t}"])
        a["positive_agreement"] = float(2 * (both == 2).sum() / max(1, (A.loc[rel, f"t_{t}"].sum() + Bn.loc[rel, f"t_{t}"].sum())))
        agr.append(a)
cl = claim_f1(A["claims"], Bn["claims"])
pd.DataFrame(agr).to_csv(TABLES / "val_agreement_AB.csv", index=False)
OUT["agreement_AB"] = agr
OUT["agreement_AB_claims"] = cl

# items needing adjudication: any field, topic set or claim set differs
diff = pd.Series(False, index=ids)
for f in FIELDS:
    diff |= A[f].astype(str) != Bn[f].astype(str)
diff |= A["topics"].map(lambda v: frozenset(as_list(v))) != Bn["topics"].map(lambda v: frozenset(as_list(v)))
diff |= A["claims"].map(claimset) != Bn["claims"].map(claimset)
OUT["n_items_any_disagreement"] = int(diff.sum())
adj_rows = load_parts("gold_adjudicated*.jsonl")
adj = to_frame(adj_rows).set_index("item_id") if adj_rows else pd.DataFrame()
gold = A.copy()
missing_adj = []
for i in diff[diff].index:
    if len(adj) and i in adj.index:
        gold.loc[i] = adj.loc[i, gold.columns]
    else:
        missing_adj.append(i)
OUT["adjudication_missing"] = missing_adj
gold["agreed_all"] = ~diff
for f in FIELDS:
    gold[f"agreed_{f}"] = A[f].astype(str) == Bn[f].astype(str)
gold = gold.join(key.set_index("item_id")).join(sheet.set_index("item_id"))
out_cols = ["doc_id", "source_type", "period", "agreed_all"] + FIELDS + ["topics", "claims"]
g2 = gold[out_cols].copy()
g2["topics"] = g2["topics"].map(lambda v: ";".join(as_list(v)))
g2["claims"] = g2["claims"].map(json.dumps)
g2.to_csv(LABELS / "gold_final.csv")

# ---------------- 2. tools vs gold
C = pd.read_parquet(CODED / "codes.parquet").set_index("item_id")
gi = gold.index.intersection(C.index)
coder = C.loc[gi]
G = gold.loc[gi]
D = dict_code(G["text"])
train_items = C[C.index.str[0].isin(list("HNRSE"))]
corpus_text = pd.concat([pd.read_parquet(p)[["doc_id", "clean"]] for p in
                         [CODED.parent / "interim" / "news.parquet", CODED.parent / "interim" / "reddit.parquet"]])
skey = pd.read_csv(CODED / "sample_key.csv").set_index("item_id")
train_items = train_items.join(skey[["doc_id"]]).merge(corpus_text, on="doc_id", how="left").set_index(train_items.index)
rows, per_class = [], []


def add(tool, field, gold_s, pred_s, subset="all"):
    m = accuracy(gold_s, pred_s, field)
    rows.append({"tool": tool, "field": field, "subset": subset, **{k: m[k] for k in
                 ["N", "accuracy", "macro_f1", "f1_lo", "f1_hi", "kappa"]}})
    if subset == "all":
        for lab, v in m["per_class"].items():
            per_class.append({"tool": tool, "field": field, "class": lab, **v})


for f in FIELDS:
    add("opus", f, G[f], coder[f])
    add("dictionary", f, G[f], D[f]) if f in D else None
    if f != "attr_target":
        add("tfidf_goldcv", f, G[f], cv_predict(G["text"], G[f]))
        if f in train_items and train_items[f].nunique() > 1:
            mdl = train(train_items["clean"].fillna(""), train_items[f])
            add("tfidf_opus_trained", f, G[f], pd.Series(mdl.predict(G["text"]), index=G.index))
    add("majority", f, G[f], pd.Series(G[f].mode().iloc[0], index=G.index))
    for st in ["national", "local", "reddit"]:
        s = G["source_type"] == st
        add("opus", f, G.loc[s, f], coder.loc[s, f], f"source:{st}")
    for p in ["2010-19", "2020-24", "2025-26"]:
        s = G["period"] == p
        add("opus", f, G.loc[s, f], coder.loc[s, f], f"period:{p}")
    for flag in [True, False]:
        s = G[f"agreed_{f}"] == flag
        if s.sum() >= 5:   # items where A and B agreed / disagreed on THIS field ("adjudicated" = disagreed on it)
            add("opus", f, G.loc[s, f], coder.loc[s, f], "annotators_agreed" if flag else "adjudicated")
    s = ~G["agreed_all"].astype(bool)   # the items with any disagreement, all sent to the adjudicator
    add("opus", f, G.loc[s, f], coder.loc[s, f], "any_disagreement")
relg = G["relevant"] == "yes"
tr_rel = train_items[train_items["relevant"] == "yes"]
for t in TOPICS:
    if G.loc[relg, f"t_{t}"].sum() >= 10:
        add("opus", f"topic:{t}", G.loc[relg, f"t_{t}"], coder.loc[relg, f"t_{t}"])
        add("dictionary", f"topic:{t}", G.loc[relg, f"t_{t}"], D.loc[relg, "topics"].map(lambda v, t=t: int(t in v)))
        yb = tr_rel["topics"].map(lambda v, t=t: "1" if t in as_list(v) else "0")
        if yb.nunique() > 1:
            mdl = train(tr_rel["clean"].fillna(""), yb)
            add("tfidf_opus_trained", f"topic:{t}", G.loc[relg, f"t_{t}"].astype(str),
                pd.Series(mdl.predict(G.loc[relg, "text"]), index=G.index[relg]))
val = pd.DataFrame(rows)
val.to_csv(TABLES / "val_tools_vs_gold.csv", index=False)
pd.DataFrame(per_class).to_csv(TABLES / "val_per_class.csv", index=False)
OUT["tools_vs_gold"] = val.to_dict("records")
OUT["claims_vs_gold"] = {"opus": claim_f1(G["claims"], coder["claims"]),
                         "dictionary_regex": claim_f1(G["claims"], D["claims"])}
for who, lab in [("A", A), ("B", Bn)]:
    OUT[f"opus_vs_annotator_{who}"] = {f: agreement(lab.loc[gi, f], coder[f], f, n_boot=200)["kappa"] for f in FIELDS}

# ---------------- 3. test-retest
rk = pd.read_csv(LABELS / "retest_key.csv")
rk = rk[rk["item_id"].isin(C.index) & rk["gold_item_id"].isin(C.index)]
OUT["test_retest"] = {f: agreement(C.loc[rk["gold_item_id"], f].reset_index(drop=True),
                                   C.loc[rk["item_id"], f].reset_index(drop=True), f, n_boot=500)
                      for f in FIELDS} if len(rk) else {}
OUT["test_retest_N"] = int(len(rk))

# ---------------- 4. swap tests
sw = pd.read_csv(CODED / "swap_key.csv")
sw = sw[sw["item_id"].isin(C.index)]
V = {v: C.loc[g["item_id"]].assign(doc_id=g["doc_id"].to_numpy()).set_index("doc_id") for v, g in sw.groupby("version")}
MAP = {"democrats": "republicans", "republicans": "democrats"}
swaps = []


def flips(a, b, field, mapped=False):
    j = a[[field]].join(b[[field]], lsuffix="_a", rsuffix="_b", how="inner")
    x, y = j[f"{field}_a"].astype(str), j[f"{field}_b"].astype(str)
    if mapped:
        x = x.map(lambda v: MAP.get(v, v))
    k, n = int((x != y).sum()), len(j)
    return k, n


for name, a, b in [("names: original vs swapped", "W0_name_orig", "W1_name_swap"),
                   ("source: plain vs Fox News", "W2_src_plain", "W3_src_fox"),
                   ("source: plain vs CNN", "W2_src_plain", "W4_src_cnn"),
                   ("source: Fox News vs CNN", "W3_src_fox", "W4_src_cnn"),
                   ("null: plain vs 'Headline:'", "W2_src_plain", "W5_null")]:
    if a not in V or b not in V:
        continue
    for f in ["relevant", "tone", "attr_dir", "attr_target", "frame_price", "frame_unit"]:
        k, n = flips(V[a], V[b], f, mapped=(f == "attr_target" and name.startswith("names")))
        swaps.append({"comparison": name, "field": f, "flips": k, "N": n, "rate": k / n if n else np.nan,
                      "ci_lo": wilson(k, n)[0], "ci_hi": wilson(k, n)[1]})
SW = pd.DataFrame(swaps)
if len(SW):
    nul = SW[SW["comparison"].str.startswith("null")].set_index("field")
    for i, r in SW.iterrows():
        if r["field"] in nul.index and not r["comparison"].startswith("null"):
            k0, n0 = nul.loc[r["field"], "flips"], nul.loc[r["field"], "N"]
            # two-proportion test of the flip rate against the null-swap flip rate (Fisher exact)
            SW.loc[i, "p_vs_null"] = stats.fisher_exact([[r["flips"], r["N"] - r["flips"]], [k0, n0 - k0]])[1]
    # direction of tone shift under source labels: mean tone score (+1 pos, -1 neg)
    sc = {"negative": -1, "neutral": 0, "positive": 1}
    OUT["source_tone_means"] = {v: float(V[v]["tone"].map(sc).mean()) for v in V if v.startswith(("W2", "W3", "W4", "W5"))}
SW.to_csv(TABLES / "val_swaps.csv", index=False)
OUT["swaps"] = SW.to_dict("records")

# ---------------- 5. minimal pairs
mp = mp_build()
mrows = read_jsonl(CODED / "batches" / "minpairs_000_out.jsonl")
ms = mp_score(mp, pd.DataFrame(mrows))
ms.groupby(["template", "field"])["ok"].mean().reset_index().to_csv(TABLES / "val_minpairs.csv", index=False)
OUT["minimal_pairs"] = {"items": int(len(mp)), "checks": int(len(ms)), "accuracy": float(ms["ok"].mean()),
                        "by_field": ms.groupby("field")["ok"].mean().round(4).to_dict()}


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        o = o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


(OUTPUTS / "results_validation.json").write_text(json.dumps(_clean(OUT), indent=1, default=str, allow_nan=False))
print(pd.DataFrame(agr)[["field", "N", "pct_agree", "kappa", "ac1"]].round(3).to_string())
print(val[val.subset == "all"].pivot_table(index="field", columns="tool", values="macro_f1").round(3).to_string())
print(SW.round(3).to_string() if len(SW) else "no swaps yet")
