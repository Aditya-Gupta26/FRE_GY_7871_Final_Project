"""How the Tier C classifier was trained and how well it does (added after the main results; nothing
here feeds a test). For each Tier C classifier (the same training set and settings as scripts/09):
- training fit: macro-F1 on the Opus labels it was trained on (training error);
- 5-fold cross-validation on those Opus labels (items it has not seen);
- the adjudicated gold labels (never used in training), from scripts/08;
- a learning curve: cross-validated tone and relevance macro-F1 by number of training items;
- agreement with Opus's own quarterly series (history, three survey months pooled).
    python scripts/09c_tierc_checks.py
Needs scripts 07, 08 and 09 to have run. Writes outputs/results_tierc.json and outputs/tables/tierc_*.csv.
"""
import _bootstrap  # noqa: F401
import json

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from src.baselines import cv_predict, train
from src.coded import as_list
from src.config import CODED, INTERIM, OUTPUTS, PROCESSED, RANDOM_SEED, TABLES

C = pd.read_parquet(CODED / "codes.parquet")
K = pd.read_csv(CODED / "sample_key.csv", parse_dates=["date", "survey_month"])
X = C.merge(K, on="item_id")
corpus = pd.concat([pd.read_parquet(INTERIM / "news.parquet")[["doc_id", "clean"]],
                    pd.read_parquet(INTERIM / "reddit.parquet")[["doc_id", "clean"]]])
tr = X[X["tier"].isin(["B_news", "A_news2026", "B_reddit", "A_reddit2026", "A_release"])].merge(corpus, on="doc_id")
tr["clean"] = tr["clean"].fillna("")
rel = tr[tr["relevant"] == "yes"]
TOPICS5 = ["inflation_up", "inflation_down", "prices_high", "layoffs", "hiring"]

tasks = {"relevant": (tr["clean"], tr["relevant"].astype(str)), "tone": (rel["clean"], rel["tone"].astype(str))}
for tp in TOPICS5:
    tasks[f"topic:{tp}"] = (rel["clean"], rel["topics"].map(lambda v, tp=tp: "1" if tp in as_list(v) else "0"))

V = pd.read_csv(TABLES / "val_tools_vs_gold.csv")
V = V[V["subset"] == "all"].set_index(["tool", "field"])["macro_f1"]
rows = []
for name, (x, y) in tasks.items():
    m = train(x, y)
    fit_pred = m.predict(x)
    cv = cv_predict(x, y)
    rows.append({"classifier": name, "N_train": int(len(y)), "classes": json.dumps(y.value_counts().to_dict()),
                 "train_macro_f1": float(f1_score(y, fit_pred, average="macro")),
                 "train_accuracy": float(accuracy_score(y, fit_pred)),
                 "cv_macro_f1": float(f1_score(y, cv.astype(str), average="macro")),
                 "gold_macro_f1": float(V.get(("tfidf_opus_trained", name), np.nan)),
                 "opus_gold_macro_f1": float(V.get(("opus", name), np.nan))})
T = pd.DataFrame(rows)
T.to_csv(TABLES / "tierc_training.csv", index=False)

# learning curve: cross-validated macro-F1 on a random subset of n training items
rng = np.random.default_rng(RANDOM_SEED)
lc = []
for name in ["relevant", "tone"]:
    x, y = tasks[name]
    for n in [n for n in [450, 1000, 2000, 4000] if n < len(y)]:
        scores = []
        for _ in range(3):
            idx = rng.choice(len(y), n, replace=False)
            xs, ys = x.iloc[idx].reset_index(drop=True), y.iloc[idx].reset_index(drop=True)
            scores.append(f1_score(ys, cv_predict(xs, ys).astype(str), average="macro"))
        lc.append({"classifier": name, "n": int(n), "cv_macro_f1": float(np.mean(scores))})
    # all training items: the cross-validated score in the table above
    lc.append({"classifier": name, "n": int(len(y)), "cv_macro_f1": float(T.loc[T["classifier"] == name, "cv_macro_f1"].iloc[0])})
LC = pd.DataFrame(lc)
LC.to_csv(TABLES / "tierc_learning_curve.csv", index=False)

# agreement with Opus's own labels over time: quarterly, quarters with enough Opus items
Mq = pd.read_parquet(PROCESSED / "media_quarterly.parquet")
oq = pd.read_parquet(PROCESSED / "media_quarterly_own.parquet")
M = pd.read_parquet(PROCESSED / "media_monthly.parquet")
tcq_ph = M["TC_SAL_prices_high"].groupby(M.index.to_period("Q").start_time).mean()
Q = Mq[["TC_NEGNET", "ownQ_NEGNET", "ownQ_covered"]].join(tcq_ph.rename("TC_prices_high")).join(
    oq["SAL_prices_high"].rename("own_prices_high"))
Q = Q[Q["ownQ_covered"].fillna(False).astype(bool)]
Q.drop(columns="ownQ_covered").to_csv(TABLES / "tierc_vs_opus_quarterly.csv")
agree = {}
for a, b in [("TC_NEGNET", "ownQ_NEGNET"), ("TC_prices_high", "own_prices_high")]:
    j = Q[[a, b]].dropna()
    agree[a] = {"N_quarters": int(len(j)), "r_levels": float(j.corr().iloc[0, 1]),
                "r_changes": float(j.diff().dropna().corr().iloc[0, 1]), "mean_tierc": float(j[a].mean()),
                "mean_opus": float(j[b].mean())}

R = {"training_items": int(len(tr)), "relevant_training_items": int(len(rel)), "classifiers": rows,
     "learning_curve": lc, "agreement_with_opus_quarterly": agree,
     "settings": "TF-IDF word 1-2 grams, sublinear tf, min_df 2; logistic regression, class_weight balanced, C = 2"}
(OUTPUTS / "results_tierc.json").write_text(json.dumps(R, indent=1))
print(T.round(3).to_string())
print(LC.round(3).to_string())
print(json.dumps(agree, indent=1))
