"""Agreement and accuracy statistics for the gold labels and the coders.

- Cohen's kappa (Cohen 1960): kappa = (p_o - p_e) / (1 - p_e); linear-weighted kappa for ordered tone.
- Krippendorff's alpha, ordinal metric (Krippendorff 2004), two coders, from the coincidence matrix:
  alpha = 1 - D_o / D_e with ordinal distances d(c,k) = (sum_{g=c..k} n_g - (n_c + n_k)/2)^2.
- Gwet's AC1 (Gwet 2008) for skewed fields: AC1 = (p_a - p_e) / (1 - p_e), p_e = sum_k pi_k (1 - pi_k) / (q - 1).
- Per-class precision, recall, F1 and macro-F1 (scikit-learn); topics scored as one binary label each.
- Claim extraction: a claim matches if indicator and value agree (|diff| < 1e-6); F1 over claims.
- 95% percentile bootstrap CIs over items (2,000 resamples).
Landis and Koch (1977) bands for reading kappa: < .20 slight, .21-.40 fair, .41-.60 moderate,
.61-.80 substantial, > .80 almost perfect.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score, precision_recall_fscore_support

from src.coded import as_list
from src.config import RANDOM_SEED

TONE_ORDER = {"negative": 0, "neutral": 1, "positive": 2}


def kripp_alpha_ordinal(a, b, order: dict) -> float:
    a = np.array([order[x] for x in a])
    b = np.array([order[x] for x in b])
    K = len(order)
    o = np.zeros((K, K))
    for x, y in zip(a, b):
        o[x, y] += 1
        o[y, x] += 1
    n_k = o.sum(1)
    n = n_k.sum()
    if n == 0:
        return np.nan

    def delta(c, k):
        lo, hi = min(c, k), max(c, k)
        return (n_k[lo:hi + 1].sum() - (n_k[c] + n_k[k]) / 2) ** 2
    D = np.array([[delta(c, k) for k in range(K)] for c in range(K)])
    Do = (o * D).sum() / n
    De = (np.outer(n_k, n_k) * D).sum() / (n * (n - 1))
    return float(1 - Do / De) if De > 0 else np.nan


def gwet_ac1(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    cats = sorted(set(a) | set(b))
    q = len(cats)
    if q < 2:
        return 1.0
    pa = (a == b).mean()
    pi = np.array([((a == c).sum() + (b == c).sum()) / (2 * len(a)) for c in cats])
    pe = (pi * (1 - pi)).sum() / (q - 1)
    return float((pa - pe) / (1 - pe))


def _kappa(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    if len(set(a) | set(b)) < 2:
        return np.nan
    return float(cohen_kappa_score(a, b))


def agreement(a: pd.Series, b: pd.Series, field: str, n_boot: int = 2000) -> dict:
    """Two label vectors for one categorical field (aligned by index)."""
    a, b = a.astype(str).to_numpy(), b.astype(str).to_numpy()
    stats = {"field": field, "N": len(a), "pct_agree": float((a == b).mean()), "kappa": _kappa(a, b),
             "ac1": gwet_ac1(a, b)}
    if field == "tone":
        stats["kappa_linear"] = float(cohen_kappa_score([TONE_ORDER[x] for x in a], [TONE_ORDER[x] for x in b],
                                                        weights="linear"))
        stats["alpha_ordinal"] = kripp_alpha_ordinal(a, b, TONE_ORDER)
    rng = np.random.default_rng(RANDOM_SEED)
    ks, acs = [], []
    for _ in range(n_boot):
        i = rng.integers(0, len(a), len(a))
        ks.append(_kappa(a[i], b[i]))
        acs.append(gwet_ac1(a[i], b[i]))
    stats["kappa_lo"], stats["kappa_hi"] = (float(np.nanpercentile(ks, 2.5)), float(np.nanpercentile(ks, 97.5)))
    stats["ac1_lo"], stats["ac1_hi"] = (float(np.nanpercentile(acs, 2.5)), float(np.nanpercentile(acs, 97.5)))
    stats["support"] = pd.Series(np.concatenate([a, b])).value_counts().to_dict()
    return stats


def accuracy(gold: pd.Series, pred: pd.Series, field: str, n_boot: int = 2000) -> dict:
    g, p = gold.astype(str).to_numpy(), pred.astype(str).to_numpy()
    labels = sorted(set(g))
    pr, rc, f1, sup = precision_recall_fscore_support(g, p, labels=labels, zero_division=0)
    out = {"field": field, "N": len(g), "accuracy": float((g == p).mean()),
           "macro_f1": float(f1_score(g, p, labels=labels, average="macro", zero_division=0)),
           "kappa": _kappa(g, p),
           "per_class": {lab: {"precision": float(a), "recall": float(b), "f1": float(c), "support": int(s)}
                         for lab, a, b, c, s in zip(labels, pr, rc, f1, sup)}}
    rng = np.random.default_rng(RANDOM_SEED)
    fs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(g), len(g))
        fs.append(f1_score(g[i], p[i], labels=labels, average="macro", zero_division=0))
    out["f1_lo"], out["f1_hi"] = float(np.percentile(fs, 2.5)), float(np.percentile(fs, 97.5))
    return out


def claim_f1(gold: pd.Series, pred: pd.Series) -> dict:
    """gold, pred: lists of claim dicts per item, aligned by index."""
    tp = fp = fn = 0
    for g, p in zip(gold, pred):
        gs = {(c["indicator"], round(float(c["value"]), 6)) for c in as_list(g)}
        ps = {(c["indicator"], round(float(c["value"]), 6)) for c in as_list(p)}
        tp += len(gs & ps)
        fp += len(ps - gs)
        fn += len(gs - ps)
    prec = tp / (tp + fp) if tp + fp else np.nan
    rec = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * prec * rec / (prec + rec) if prec and rec else np.nan
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1}
