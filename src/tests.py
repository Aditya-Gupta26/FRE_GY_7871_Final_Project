"""Statistical tests used by scripts/10_analysis.py (all pre-registered in config.PREREG).

- asymmetry(): Soroka (2006)-style. NEG_t = a + b_up max(dX,0) + b_dn max(-dX,0) + ... ; the response to
  a deterioration is b_up, to an improvement -b_dn; negativity asymmetry means b_up > -b_dn, i.e.
  b_up + b_dn > 0, tested one-sided with the EWC covariance and t_nu (LLSW 2018).
- toda_yamamoto(): Granger causality in a levels VAR (Toda and Yamamoto 1995): lag p by BIC (max 6),
  fit p + 1 lags (d_max = 1), Wald test that the first p lags of the cause are zero (chi2, HC1);
  plus a circular-shift permutation p-value with shifts of more than 12 months.
- robustness_value(): Cinelli and Hazlett (2020), RV = (sqrt(f^4 + 4 f^2) - f^2) / 2, f = t / sqrt(df):
  the share of residual variance of both treatment and outcome an omitted confounder would need
  to explain to drive the estimate to zero.
- mde_r(): r* = tanh((z_.975 + z_.80) / sqrt(N_eff - 3)) (Hulley et al. 2013) with the Bartlett
  effective N, N_eff = N (1 - rho_x rho_y) / (1 + rho_x rho_y).
- shapley2(): Shapley shares of two blocks in a gap-closing value function.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.econ_model import fit


def asymmetry(neg: pd.Series, dX: dict[str, pd.Series], extra: pd.DataFrame | None = None) -> dict:
    cols = {}
    for k, d in dX.items():
        cols[f"{k}_up"] = d.clip(lower=0)
        cols[f"{k}_dn"] = (-d).clip(lower=0)
    X = pd.DataFrame(cols)
    if extra is not None:
        X = X.join(extra)
    f = fit(neg, X)
    out = {"N": int(f.nobs), "nu": f.nu, "R2": float(f.rsquared)}
    for k in dX:
        b_up, b_dn = f.params[f"{k}_up"], f.params[f"{k}_dn"]
        V = f.V.loc[[f"{k}_up", f"{k}_dn"], [f"{k}_up", f"{k}_dn"]].to_numpy()
        se = float(np.sqrt(V[0, 0] + V[1, 1] + 2 * V[0, 1]))
        diff = float(b_up + b_dn)
        t = diff / se
        out[k] = {"resp_bad": float(b_up), "resp_good": float(-b_dn), "se_bad": float(f.bse[list(f.params.index).index(f"{k}_up")]),
                  "se_good": float(f.bse[list(f.params.index).index(f"{k}_dn")]), "asym": diff, "se_asym": se,
                  "t": t, "p_one_sided": float(1 - stats.t.cdf(t, f.nu)),
                  "ci90": [diff - stats.t.ppf(0.95, f.nu) * se, diff + stats.t.ppf(0.95, f.nu) * se]}
    return out


def _lags(s: pd.Series, p: int, name: str) -> pd.DataFrame:
    return pd.concat({f"{name}_L{k}": s.shift(k) for k in range(1, p + 1)}, axis=1)


def _ty_wald(y: pd.Series, x: pd.Series, p: int, exog: pd.DataFrame | None) -> tuple[float, float, float, int]:
    Z = pd.concat([y.rename("y"), _lags(y, p + 1, "y"), _lags(x, p + 1, "x")], axis=1)
    if exog is not None:
        Z = Z.join(exog)
    Z = Z.dropna()
    Xc = sm.add_constant(Z.drop(columns="y"))
    r = sm.OLS(Z["y"], Xc).fit(cov_type="HC1")
    test = [f"x_L{k}" for k in range(1, p + 1)]
    R = np.zeros((p, len(r.params)))
    for i, c in enumerate(test):
        R[i, list(r.params.index).index(c)] = 1
    w = r.wald_test(R, scalar=True)
    return float(w.statistic), float(w.pvalue), float(r.params[test].sum()), int(r.nobs)


def bic_lag(y: pd.Series, x: pd.Series, maxlag: int = 6) -> int:
    best, bp = np.inf, 1
    base = pd.concat([y, x], axis=1).dropna()
    for p in range(1, maxlag + 1):
        Z = pd.concat([y.rename("y"), _lags(y, maxlag, "y"), _lags(x, maxlag, "x")], axis=1).dropna()
        cols = [f"y_L{k}" for k in range(1, p + 1)] + [f"x_L{k}" for k in range(1, p + 1)]
        r = sm.OLS(Z["y"], sm.add_constant(Z[cols])).fit()
        if r.bic < best:
            best, bp = r.bic, p
    return bp


def toda_yamamoto(y: pd.Series, x: pd.Series, exog: pd.DataFrame | None = None, maxlag: int = 6,
                  min_shift: int = 13, perm: bool = True) -> dict:
    """Does x Granger-cause y? y, x on a monthly index (NaN for excluded months)."""
    p = bic_lag(y, x, maxlag)
    W, pval, sumc, n = _ty_wald(y, x, p, exog)
    out = {"lag_p": p, "N": n, "wald": W, "p": pval, "sum_coef": sumc}
    if perm:
        xv = x.to_numpy(dtype=float)
        valid = ~np.isnan(xv)
        vals = xv[valid]
        Ws = []
        for k in range(min_shift, len(vals) - min_shift):
            # rotate the observed values only, keeping the same missing-month pattern
            arr = np.full(len(xv), np.nan)
            arr[valid] = np.roll(vals, k)
            xs = pd.Series(arr, index=x.index, name=x.name)
            try:
                Ws.append(_ty_wald(y, xs, p, exog)[0])
            except Exception:  # noqa: BLE001
                continue
        Ws = np.array(Ws)
        out["p_perm"] = float((1 + (Ws >= W).sum()) / (1 + len(Ws)))
        out["n_shifts"] = int(len(Ws))
    return out


def robustness_value(t: float, df: float) -> float:
    f = abs(t) / np.sqrt(df)
    return float((np.sqrt(f ** 4 + 4 * f ** 2) - f ** 2) / 2)


def ar1(s: pd.Series) -> float:
    s = s.dropna()
    return float(np.corrcoef(s.to_numpy()[:-1], s.to_numpy()[1:])[0, 1])


def mde_r(n: int, rho_x: float, rho_y: float) -> dict:
    neff = n * (1 - rho_x * rho_y) / (1 + rho_x * rho_y)
    r = float(np.tanh((stats.norm.ppf(0.975) + stats.norm.ppf(0.80)) / np.sqrt(max(neff - 3, 1))))
    return {"N": n, "rho_x": rho_x, "rho_y": rho_y, "N_eff": float(neff), "mde_r": r}


def shapley2(v: dict) -> dict:
    """v: value of each coalition, keys '', 'A', 'B', 'AB'."""
    a = 0.5 * ((v["A"] - v[""]) + (v["AB"] - v["B"]))
    b = 0.5 * ((v["B"] - v[""]) + (v["AB"] - v["A"]))
    return {"A": float(a), "B": float(b), "total": float(v["AB"] - v[""])}


def leave_one_year_out(y: pd.Series, X: pd.DataFrame, coef: str) -> dict:
    yrs = sorted(set(X.dropna().index.year))
    res = []
    for yr in yrs:
        m = X.index.year != yr
        f = fit(y[m], X[m])
        res.append({"drop": yr, "coef": float(f.params[coef]), "p": float(f.pvalues[coef])})
    d = pd.DataFrame(res)
    return {"min_coef": float(d["coef"].min()), "max_coef": float(d["coef"].max()), "max_p": float(d["p"].max()),
            "years": d.to_dict("records")}
