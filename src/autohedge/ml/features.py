"""Feature engineering for ML risk scoring and volatility analysis."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from autohedge.simulation.portfolio_sim import portfolio_return_series


FEATURE_NAMES = [
    "ann_vol",
    "ewma_vol",
    "vol_of_vol",
    "max_drawdown_60",
    "avg_corr",
    "top_weight",
    "equity_exposure",
    "hhi",
    "downside_dev",
    "skew",
    "kurtosis",
    "beta_proxy",
    "market_factor",
    "tech_factor",
    "rates_factor",
    "crypto_factor",
    "commodity_factor",
]


def _ewma_vol(returns: pd.Series, lam: float = 0.94) -> float:
    if returns.empty:
        return 0.0
    var = 0.0
    for r in returns.values:
        var = lam * var + (1.0 - lam) * (r ** 2)
    return float(np.sqrt(var * 252.0))


def build_feature_vector(
    portfolio: dict[str, Any],
    returns: pd.DataFrame,
    metrics: dict[str, Any],
) -> dict[str, float]:
    port = portfolio_return_series(portfolio, returns)
    window = port.tail(60) if len(port) >= 20 else port
    wealth = (1.0 + window).cumprod()
    peak = wealth.cummax()
    mdd = float(((peak - wealth) / peak).max()) if len(wealth) else 0.0
    downside = window[window < 0]
    downside_dev = float(downside.std(ddof=1) * np.sqrt(252)) if len(downside) > 1 else 0.0

    return {
        "ann_vol": float(metrics.get("annualized_volatility", window.std() * np.sqrt(252))),
        "ewma_vol": _ewma_vol(window),
        "vol_of_vol": float(window.rolling(10).std().std() * np.sqrt(252)) if len(window) > 15 else 0.0,
        "max_drawdown_60": mdd,
        "avg_corr": float(metrics.get("avg_correlation", 0.0)),
        "top_weight": float(metrics.get("top_weight", 0.0)),
        "equity_exposure": float(metrics.get("equity_exposure", 0.0)),
        "hhi": float(metrics.get("concentration_hhi", 0.0)),
        "downside_dev": downside_dev,
        "skew": float(window.skew()) if len(window) > 3 else 0.0,
        "kurtosis": float(window.kurt()) if len(window) > 4 else 0.0,
        "beta_proxy": float(metrics.get("beta_proxy", 1.0)),
        "market_factor": float(metrics.get("market_factor", 0.0)),
        "tech_factor": float(metrics.get("tech_factor", 0.0)),
        "rates_factor": float(metrics.get("rates_factor", 0.0)),
        "crypto_factor": float(metrics.get("crypto_factor", 0.0)),
        "commodity_factor": float(metrics.get("commodity_factor", 0.0)),
    }


def features_to_array(features: dict[str, float]) -> np.ndarray:
    return np.array([features[name] for name in FEATURE_NAMES], dtype=float)
