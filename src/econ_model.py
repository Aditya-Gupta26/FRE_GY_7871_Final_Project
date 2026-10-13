"""Economic-only model, out-of-sample predictions with intervals, the sentiment gap, and
"how much is explained".

Model E: S_t = a + b_U U_t + b_pi pi_t + b_g g_t + e_t, OLS on the real-time panel, fitted on
the training months only. Primary inference: EWC HAR covariance with t_nu critical values
(Lazarus, Lewis, Stock and Watson 2018); Newey-West (L = 12; Newey and West 1987) as a check.

Prediction interval for one month: moving-block bootstrap (Kunsch 1989; block 12): coefficients
  re-estimated on y* = X b + e* (e* = blocks of training residuals), plus a residual draw (class
  Boot). Analytic check: yhat +- t_nu * sqrt(s^2 + x' V_EWC x).
Mean gap over k months: null distribution if the training model still held,
  mean(X_W (b - b*)) + mean of k consecutive training residuals (Boot.mean_gap_null, no wrap-around);
  conservative check with coefficients drawn from N(b, V_EWC) and AR(1) errors fitted to the training
  residuals (mean_gap_null_ar1); analytic check x_bar' V x_bar + (1/k^2) 1' Gamma 1 (mean_gap_band).
Decomposition: predicted change between two periods = b' (xbar_2 - xbar_1); share explained =
  predicted / actual change; CI from the bootstrap draws and from t_nu * sqrt(dx' V_EWC dx).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

HAC_LAGS = 12


def ewc_nu(T: int) -> int:
    """LLSW (2018) rule: nu = 0.4 T^(2/3), rounded (T = 120 gives 10)."""
    return int(round(0.4 * T ** (2 / 3)))


def ewc_cov(X: np.ndarray, u: np.ndarray, nu: int) -> np.ndarray:
    """Equal-weighted cosine (EWC) HAR covariance of OLS coefficients (Lazarus, Lewis, Stock and
    Watson 2018): Lambda_j = sqrt(2/T) sum_t z_t cos(pi j (t - 1/2) / T), z_t = x_t u_t,
    Omega = (1/nu) sum_j Lambda_j Lambda_j', V = (X'X)^-1 (T Omega) (X'X)^-1.
    t-stats use t_nu critical values; a Wald test of q restrictions uses
    F = (nu - q + 1) / (nu q) x W ~ F(q, nu - q + 1)."""
    T = len(u)
    z = X * u[:, None]
    tt = np.arange(1, T + 1)
    lam = np.array([np.sqrt(2 / T) * (np.cos(np.pi * j * (tt - 0.5) / T)[:, None] * z).sum(0)
                    for j in range(1, nu + 1)])
    omega = lam.T @ lam / nu
    xtx_inv = np.linalg.inv(X.T @ X)
    return xtx_inv @ (T * omega) @ xtx_inv


class Fit:
    """OLS with EWC (primary) and Newey-West (check) covariances, statsmodels-like attributes."""

    def __init__(self, y: pd.Series, X: pd.DataFrame, nu: int | None = None, hac_lags: int = HAC_LAGS):
        d = pd.concat([y.rename("y"), X], axis=1).dropna()
        self.index = d.index
        Xc = sm.add_constant(d[X.columns], has_constant="add")
        self.ols = sm.OLS(d["y"], Xc).fit()
        self.nw = sm.OLS(d["y"], Xc).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
        self.nu = nu or ewc_nu(len(d))
        self.V = pd.DataFrame(ewc_cov(Xc.to_numpy(), self.ols.resid.to_numpy(), self.nu),
                              index=Xc.columns, columns=Xc.columns)
        self.params, self.resid, self.model = self.ols.params, self.ols.resid, self.ols.model
        self.ssr, self.df_resid, self.rsquared, self.nobs = self.ols.ssr, self.ols.df_resid, self.ols.rsquared, self.ols.nobs
        self.bse = np.sqrt(np.diag(self.V))
        self.tvalues = self.params / self.bse
        self.pvalues = pd.Series(2 * (1 - stats.t.cdf(np.abs(self.tvalues), self.nu)), index=self.params.index)

    def cov_params(self) -> pd.DataFrame:
        return self.V

    def wald(self, cols: list[str]) -> dict:
        b = self.params[cols].to_numpy()
        V = self.V.loc[cols, cols].to_numpy()
        W = float(b @ np.linalg.solve(V, b))
        q = len(cols)
        F = (self.nu - q + 1) / (self.nu * q) * W
        p = float(1 - stats.f.cdf(F, q, self.nu - q + 1)) if self.nu - q + 1 > 0 else np.nan
        Vn = self.nw.cov_params().loc[cols, cols].to_numpy()
        Wn = float(b @ np.linalg.solve(Vn, b))
        return {"q": q, "F_ewc": F, "p_ewc": p, "p_nw": float(1 - stats.chi2.cdf(Wn, q))}

    def table(self) -> pd.DataFrame:
        return pd.DataFrame({"coef": self.params, "se_ewc": self.bse, "p_ewc": self.pvalues,
                             "se_nw": self.nw.bse, "p_nw": self.nw.pvalues})


def fit(y: pd.Series, X: pd.DataFrame, nu: int | None = None) -> Fit:
    return Fit(y, X, nu)


def predict(res, X: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    Xc = sm.add_constant(X[res.model.exog_names[1:]], has_constant="add")
    mean = Xc @ res.params
    V = res.cov_params().to_numpy()
    se_par = np.sqrt(np.einsum("ij,jk,ik->i", Xc.to_numpy(), V, Xc.to_numpy()))
    s2 = res.ssr / res.df_resid
    se = np.sqrt(s2 + se_par ** 2)
    t = stats.t.ppf(1 - alpha / 2, getattr(res, "nu", res.df_resid))
    return pd.DataFrame({"pred": mean, "se_pred": se, "lo": mean - t * se, "hi": mean + t * se},
                        index=X.index)


def mean_gap_band(res, Xwin: pd.DataFrame, gap: pd.Series, alpha: float = 0.05) -> dict:
    """Mean of the gap over the window, with the exact variance of a k-month mean of a
    stationary error (training autocovariances) plus coefficient uncertainty."""
    k = len(gap.dropna())
    e = res.resid.to_numpy() - res.resid.mean()
    n = len(e)
    gam = np.array([np.sum(e[: n - h] * e[h:]) / n for h in range(k)])
    var_err = sum(gam[abs(i - j)] for i in range(k) for j in range(k)) / k ** 2
    xbar = sm.add_constant(Xwin[res.model.exog_names[1:]], has_constant="add").mean().to_numpy()
    var_par = float(xbar @ res.cov_params().to_numpy() @ xbar)
    se = float(np.sqrt(var_err + var_par))
    m = float(gap.mean())
    z = stats.norm.ppf(1 - alpha / 2)
    # empirical check: k-month circular means of training residuals
    circ = np.array([np.mean(np.take(res.resid.to_numpy(), range(i, i + k), mode="wrap")) for i in range(n)])
    return {"k": k, "mean_gap": m, "se": se, "lo": m - z * se, "hi": m + z * se,
            "se_error_part": float(np.sqrt(var_err)), "se_param_part": float(np.sqrt(var_par)),
            "z": m / se, "p_two_sided": float(2 * (1 - stats.norm.cdf(abs(m / se)))),
            "empirical_q025": float(np.quantile(circ, 0.025)), "empirical_q975": float(np.quantile(circ, 0.975)),
            "share_train_kmeans_below": float((circ <= m).mean())}


def decompose(res, X: pd.DataFrame, y: pd.Series, p1: slice, p2: slice) -> dict:
    cols = res.model.exog_names[1:]
    dx = X.loc[p2, cols].mean() - X.loc[p1, cols].mean()
    b = res.params[cols]
    contrib = (b * dx).to_dict()
    pred = float((b * dx).sum())
    act = float(y.loc[p2].mean() - y.loc[p1].mean())
    V = res.cov_params().loc[cols, cols].to_numpy()
    se_pred = float(np.sqrt(dx.to_numpy() @ V @ dx.to_numpy()))
    tc = stats.t.ppf(0.975, getattr(res, "nu", 1e6))
    ends = sorted([(pred - tc * se_pred) / act, (pred + tc * se_pred) / act])
    return {"actual_change": act, "predicted_change": pred, "se_predicted": se_pred,
            "share_explained": pred / act, "share_lo": ends[0], "share_hi": ends[1],
            "contributions": contrib, "dx": dx.to_dict(), "coef": b.to_dict()}


class Boot:
    """Moving-block bootstrap of the training fit (Kunsch 1989), block 12, shared by the
    prediction intervals, the mean-gap null distribution and the decomposition CIs."""

    def __init__(self, y: pd.Series, X: pd.DataFrame, block: int = 12, reps: int = 2000, seed: int = 7871):
        d = pd.concat([y.rename("y"), X], axis=1).dropna()
        self.cols = list(X.columns)
        self.Xc = sm.add_constant(d[self.cols], has_constant="add").to_numpy()
        self.b = np.linalg.lstsq(self.Xc, d["y"].to_numpy(), rcond=None)[0]
        self.e = d["y"].to_numpy() - self.Xc @ self.b
        n = len(self.e)
        self.rng = np.random.default_rng(seed)
        nb = int(np.ceil(n / block))
        draws = []
        for _ in range(reps):
            starts = self.rng.integers(0, n - block + 1, nb)
            es = np.concatenate([self.e[s:s + block] for s in starts])[:n]
            draws.append(np.linalg.lstsq(self.Xc, self.Xc @ self.b + es, rcond=None)[0])
        self.B = np.array(draws)          # reps x (k+1)

    def _xn(self, Xnew: pd.DataFrame) -> np.ndarray:
        return sm.add_constant(Xnew[self.cols], has_constant="add").to_numpy()

    def pi(self, Xnew: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
        Xn = self._xn(Xnew)
        sims = self.B @ Xn.T + self.e[self.rng.integers(0, len(self.e), (len(self.B), len(Xn)))]
        return pd.DataFrame({"pred": Xn @ self.b, "bb_lo": np.quantile(sims, alpha / 2, 0),
                             "bb_hi": np.quantile(sims, 1 - alpha / 2, 0)}, index=Xnew.index)

    def mean_gap_null(self, Xwin: pd.DataFrame, observed: float, alpha: float = 0.05) -> dict:
        """Null distribution of a k-month mean gap if the training model still held:
        mean(X_W (b - b*)) + mean of a contiguous k-month block of training residuals."""
        Xn = self._xn(Xwin)
        k, n = len(Xn), len(self.e)
        par = (Xn @ (self.b[None, :] - self.B).T).mean(0)
        assert k <= n, "window longer than the training sample"
        starts = self.rng.integers(0, n - k + 1, len(self.B))      # contiguous blocks, no wrap-around
        err = np.array([self.e[s:s + k].mean() for s in starts])
        sims = par + err
        p = float((np.abs(sims) >= abs(observed)).mean())
        return {"k": k, "observed": observed, "null_lo": float(np.quantile(sims, alpha / 2)),
                "null_hi": float(np.quantile(sims, 1 - alpha / 2)), "null_sd": float(sims.std()),
                "p_two_sided": p, "p_floor": 1 / len(self.B), "p_text": f"< {1 / len(self.B):.4f}" if p == 0 else f"{p:.4f}",
                "obs_band_lo": float(observed - np.quantile(sims, 1 - alpha / 2)),
                "obs_band_hi": float(observed - np.quantile(sims, alpha / 2))}

    def decomp_ci(self, dx: pd.Series, actual: float) -> tuple[float, float]:
        pred = self.B[:, 1:] @ dx[self.cols].to_numpy()
        lo, hi = np.quantile(pred / actual, [0.025, 0.975])
        return float(lo), float(hi)


def mean_gap_null_ar1(res, Xwin: pd.DataFrame, observed: float, reps: int = 20000, seed: int = 7871,
                      alpha: float = 0.05) -> dict:
    """Conservative check of the mean-gap null: coefficients ~ N(b, V_EWC); errors from an AR(1)
    fitted to the training residuals, started from its stationary distribution."""
    rng = np.random.default_rng(seed)
    cols = res.model.exog_names[1:]
    Xn = sm.add_constant(Xwin[cols], has_constant="add").to_numpy()
    k = len(Xn)
    e = res.resid.to_numpy()
    rho = float(np.corrcoef(e[:-1], e[1:])[0, 1])
    su = float(np.std(e[1:] - rho * e[:-1], ddof=1))
    b = res.params.to_numpy()
    B = rng.multivariate_normal(b, res.cov_params().to_numpy(), reps)
    par = (Xn @ (b[None, :] - B).T).mean(0)
    u = np.empty((reps, k))
    u[:, 0] = rng.normal(0, su / np.sqrt(1 - rho ** 2), reps)
    for j in range(1, k):
        u[:, j] = rho * u[:, j - 1] + rng.normal(0, su, reps)
    sims = par + u.mean(1)
    p = float((np.abs(sims) >= abs(observed)).mean())
    return {"k": k, "rho": rho, "null_lo": float(np.quantile(sims, alpha / 2)),
            "null_hi": float(np.quantile(sims, 1 - alpha / 2)), "null_sd": float(sims.std()),
            "p_two_sided": p, "p_text": f"< {1 / reps:.5f}" if p == 0 else f"{p:.5f}"}
