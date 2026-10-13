"""Expanding-window real-time nowcasts and tests of equal predictive accuracy.

Nowcast of S_t made on the prediction date of month t (day 14): the model is re-fitted on every
earlier month (their targets are all published by then: the final value of month t-1 comes out
at the end of month t-1) and applied to month t's real-time regressors.

Clark and West (2007), nested models (model 1 is nested in model 2):
  f_t = (y_t - yhat1_t)^2 - [(y_t - yhat2_t)^2 - (yhat1_t - yhat2_t)^2]
  regress f_t on a constant; one-sided test of mean(f) > 0 with a HAC standard error.
Diebold and Mariano (1995): d_t = e1_t^2 - e2_t^2, two-sided HAC t-test of mean(d) = 0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


def expanding_nowcast(y: pd.Series, X: pd.DataFrame, first_origin: str, train_start: str,
                      min_train: int = 60) -> pd.DataFrame:
    d = pd.concat([y.rename("y"), X], axis=1)
    d = d.loc[train_start:]
    out = []
    for t in d.loc[first_origin:].index:
        tr = d.loc[: t - pd.DateOffset(months=1)].dropna()
        x_t = d.loc[t, X.columns]
        if len(tr) < min_train or x_t.isna().any():
            continue
        Xc = sm.add_constant(tr[X.columns], has_constant="add")
        b = np.linalg.lstsq(Xc.to_numpy(), tr["y"].to_numpy(), rcond=None)[0]
        pred = float(np.r_[1.0, x_t.to_numpy(dtype=float)] @ b)
        out.append({"month": t, "y": d.loc[t, "y"], "pred": pred, "n_train": len(tr)})
    r = pd.DataFrame(out).set_index("month")
    r["err"] = r["y"] - r["pred"]
    return r


def _hac_mean_t(x: pd.Series, lags: int) -> tuple[float, float, float]:
    x = x.dropna()
    res = sm.OLS(x.to_numpy(), np.ones((len(x), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(res.params[0]), float(res.bse[0]), float(res.tvalues[0])


def clark_west(y: pd.Series, p1: pd.Series, p2: pd.Series, lags: int = 12) -> dict:
    j = pd.concat([y.rename("y"), p1.rename("p1"), p2.rename("p2")], axis=1).dropna()
    f = (j.y - j.p1) ** 2 - ((j.y - j.p2) ** 2 - (j.p1 - j.p2) ** 2)
    m, se, t = _hac_mean_t(f, lags)
    return {"N": int(len(j)), "cw_mean": m, "cw_t": t, "p_one_sided": float(1 - stats.norm.cdf(t)),
            "rmse1": float(np.sqrt(((j.y - j.p1) ** 2).mean())),
            "rmse2": float(np.sqrt(((j.y - j.p2) ** 2).mean()))}


def diebold_mariano(y: pd.Series, p1: pd.Series, p2: pd.Series, lags: int = 12) -> dict:
    j = pd.concat([y.rename("y"), p1.rename("p1"), p2.rename("p2")], axis=1).dropna()
    d = (j.y - j.p1) ** 2 - (j.y - j.p2) ** 2
    m, se, t = _hac_mean_t(d, lags)
    return {"N": int(len(j)), "dm_mean": m, "dm_t": t, "p_two_sided": float(2 * (1 - stats.norm.cdf(abs(t))))}


def metrics(r: pd.DataFrame) -> dict:
    e = r["err"].dropna()
    return {"N": int(len(e)), "rmse": float(np.sqrt((e ** 2).mean())), "mae": float(e.abs().mean()),
            "bias": float(e.mean())}
