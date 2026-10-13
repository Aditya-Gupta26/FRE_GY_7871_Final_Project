"""Conventional classifier baseline (no AI): TF-IDF (word 1-2 grams, sublinear tf, min_df 2) +
logistic regression (class_weight balanced), one model per field; each topic is its own binary
label. Two versions:
- "gold CV": trained and tested on the gold labels with stratified 5-fold cross-validation;
- "Opus-trained": trained on thousands of Opus-coded non-gold items, tested on the gold labels;
  it is also applied to the full corpus as the large-n "Tier C" series.
Psomakelis et al. (2014) and Carvalho and Plastino (2020) motivate comparing a learned model with
a lexicon.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline

from src.config import RANDOM_SEED

FIELDS = ["relevant", "tone", "frame_price", "frame_unit", "frame_time", "attr_dir"]


def _pipe():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2, lowercase=True),
                         LogisticRegression(max_iter=3000, class_weight="balanced", C=2.0))


def cv_predict(texts: pd.Series, y: pd.Series, k: int = 5) -> pd.Series:
    y = y.astype(str)
    pred = pd.Series(index=y.index, dtype=object)
    counts = y.value_counts()
    if len(counts) < 2:
        return pd.Series(counts.index[0], index=y.index)
    k = int(min(k, counts.min())) if counts.min() >= 2 else 2
    if counts.min() < 2:   # a class with one item: fold on the rest, predict majority for it
        skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=RANDOM_SEED)
        strat = y.where(y.map(counts) >= 2, counts.index[0])
    else:
        skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=RANDOM_SEED)
        strat = y
    for tr, te in skf.split(texts, strat):
        m = _pipe().fit(texts.iloc[tr], y.iloc[tr]) if y.iloc[tr].nunique() > 1 else None
        pred.iloc[te] = m.predict(texts.iloc[te]) if m is not None else y.iloc[tr].iloc[0]
    return pred


def train(texts: pd.Series, y: pd.Series):
    return _pipe().fit(texts, y.astype(str))
