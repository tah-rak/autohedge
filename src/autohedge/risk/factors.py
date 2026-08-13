"""Multi-factor risk exposures — Crypto is a first-class systematic factor."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from autohedge.simulation.portfolio_sim import portfolio_return_series

# Product-facing factor set. Crypto sits alongside classic macro/style factors.
FACTOR_ORDER = ("market", "tech", "rates", "crypto", "commodity")

FACTOR_LABELS = {
    "market": "Market",
    "tech": "Tech",
    "rates": "Rates",
    "crypto": "Crypto",
    "commodity": "Commodity",
}

# Symbols used to build tradable factor proxies (always simulated for estimation).
FACTOR_PROXY_SYMBOLS = ("SPY", "QQQ", "TLT", "BTC", "GLD")

# Approximate static loadings used when explaining holding-level factor tilt.
ASSET_FACTOR_LOADINGS: dict[str, dict[str, float]] = {
    "AAPL": {"market": 1.05, "tech": 0.85, "rates": -0.10, "crypto": 0.15, "commodity": 0.00},
    "MSFT": {"market": 1.00, "tech": 0.80, "rates": -0.05, "crypto": 0.12, "commodity": 0.00},
    "NVDA": {"market": 1.35, "tech": 1.20, "rates": -0.15, "crypto": 0.35, "commodity": 0.00},
    "AMZN": {"market": 1.15, "tech": 0.55, "rates": -0.05, "crypto": 0.10, "commodity": 0.00},
    "GOOGL": {"market": 1.05, "tech": 0.75, "rates": -0.05, "crypto": 0.12, "commodity": 0.00},
    "SPY": {"market": 1.00, "tech": 0.20, "rates": -0.05, "crypto": 0.05, "commodity": 0.00},
    "QQQ": {"market": 1.10, "tech": 1.00, "rates": -0.10, "crypto": 0.18, "commodity": 0.00},
    "EFA": {"market": 0.90, "tech": 0.10, "rates": 0.00, "crypto": 0.04, "commodity": 0.05},
    "EEM": {"market": 1.05, "tech": 0.15, "rates": 0.05, "crypto": 0.10, "commodity": 0.10},
    "AGG": {"market": 0.05, "tech": -0.05, "rates": 0.70, "crypto": -0.05, "commodity": 0.00},
    "TLT": {"market": -0.20, "tech": -0.10, "rates": 1.00, "crypto": -0.10, "commodity": 0.00},
    "GLD": {"market": 0.05, "tech": 0.00, "rates": 0.15, "crypto": 0.10, "commodity": 1.00},
    "VNQ": {"market": 0.80, "tech": 0.05, "rates": 0.35, "crypto": 0.05, "commodity": 0.05},
    "XLU": {"market": 0.45, "tech": -0.10, "rates": 0.25, "crypto": 0.00, "commodity": 0.05},
    "VYM": {"market": 0.75, "tech": 0.05, "rates": 0.10, "crypto": 0.02, "commodity": 0.00},
    "BTC": {"market": 0.55, "tech": 0.25, "rates": -0.15, "crypto": 1.00, "commodity": 0.10},
    "ETH": {"market": 0.60, "tech": 0.35, "rates": -0.15, "crypto": 1.10, "commodity": 0.08},
    "SOL": {"market": 0.65, "tech": 0.40, "rates": -0.20, "crypto": 1.25, "commodity": 0.05},
    "BTCUSD": {"market": 0.55, "tech": 0.25, "rates": -0.15, "crypto": 1.00, "commodity": 0.10},
    "BITO": {"market": 0.50, "tech": 0.20, "rates": -0.10, "crypto": 0.95, "commodity": 0.08},
    "SH": {"market": -1.00, "tech": -0.20, "rates": 0.05, "crypto": -0.05, "commodity": 0.00},
    "PSQ": {"market": -1.10, "tech": -1.00, "rates": 0.05, "crypto": -0.10, "commodity": 0.00},
}


def build_factor_proxies(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Construct factor return series from observable proxies.

    - Market: SPY
    - Tech: QQQ residualized vs SPY (tech-minus-market style)
    - Rates: TLT
    - Crypto: BTC (systematic digital-asset factor)
    - Commodity: GLD
    """
    frames: dict[str, pd.Series] = {}
    spy = returns["SPY"] if "SPY" in returns.columns else returns.iloc[:, 0]

    frames["market"] = spy.astype(float)

    if "QQQ" in returns.columns:
        qqq = returns["QQQ"].astype(float)
        beta = float(np.cov(qqq.values, spy.values)[0, 1] / max(np.var(spy.values, ddof=1), 1e-12))
        frames["tech"] = qqq - beta * spy
    else:
        frames["tech"] = spy * 0.0

    frames["rates"] = returns["TLT"].astype(float) if "TLT" in returns.columns else spy * 0.0

    if "BTC" in returns.columns:
        frames["crypto"] = returns["BTC"].astype(float)
    elif "ETH" in returns.columns:
        frames["crypto"] = returns["ETH"].astype(float)
    else:
        frames["crypto"] = spy * 0.0

    frames["commodity"] = returns["GLD"].astype(float) if "GLD" in returns.columns else spy * 0.0
    return pd.DataFrame(frames).dropna()


def _ols_betas(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Return OLS coefficients for y ~ X (no intercept for return-factor attribution)."""
    if len(y) < x.shape[1] + 2:
        return np.zeros(x.shape[1], dtype=float)
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    return beta.astype(float)


def estimate_factor_betas(
    portfolio: dict[str, Any],
    returns: pd.DataFrame,
) -> dict[str, float]:
    """Estimate portfolio betas to Market / Tech / Rates / Crypto / Commodity."""
    port = portfolio_return_series(portfolio, returns)
    factors = build_factor_proxies(returns)
    aligned = pd.concat([port.rename("portfolio"), factors], axis=1).dropna()
    if aligned.empty:
        return {name: 0.0 for name in FACTOR_ORDER}

    y = aligned["portfolio"].values
    x = aligned[list(FACTOR_ORDER)].values
    betas = _ols_betas(y, x)
    return {name: float(betas[i]) for i, name in enumerate(FACTOR_ORDER)}


def weighted_static_factor_tilt(portfolio: dict[str, Any]) -> dict[str, float]:
    """Weight-average of static asset loadings — useful when returns history is short."""
    totals = {name: 0.0 for name in FACTOR_ORDER}
    for h in portfolio.get("holdings", []):
        w = float(h.get("weight", 0.0))
        loads = ASSET_FACTOR_LOADINGS.get(h.get("symbol", ""), {})
        for name in FACTOR_ORDER:
            totals[name] += w * float(loads.get(name, 0.0))
    return totals


def compute_factor_exposures(
    portfolio: dict[str, Any],
    returns: pd.DataFrame,
) -> dict[str, Any]:
    """
    Combined factor view:
    - estimated betas from returns (primary)
    - static allocation tilt (secondary confirmation)
    - contribution share highlighting Crypto as a distinct risk factor
    """
    estimated = estimate_factor_betas(portfolio, returns)
    static = weighted_static_factor_tilt(portfolio)
    # Blend: estimated dominates when available; static anchors crypto sleeve visibility.
    blended = {
        name: 0.7 * estimated[name] + 0.3 * static[name] for name in FACTOR_ORDER
    }
    abs_sum = sum(abs(v) for v in blended.values()) or 1.0
    contribution = {name: abs(blended[name]) / abs_sum for name in FACTOR_ORDER}

    return {
        "betas": blended,
        "estimated_betas": estimated,
        "static_tilt": static,
        "contribution": contribution,
        "crypto_factor": blended["crypto"],
        "market_factor": blended["market"],
        "tech_factor": blended["tech"],
        "rates_factor": blended["rates"],
        "commodity_factor": blended["commodity"],
        "factors": [
            {
                "id": name,
                "label": FACTOR_LABELS[name],
                "beta": blended[name],
                "contribution": contribution[name],
            }
            for name in FACTOR_ORDER
        ],
    }


def detect_factor_signals(
    factor_exposures: dict[str, Any],
    *,
    crypto_beta_alert: float = 0.35,
    crypto_contrib_alert: float = 0.22,
) -> list[dict[str, Any]]:
    """Map elevated factor tilts into risk signals (Crypto included)."""
    signals: list[dict[str, Any]] = []
    crypto_beta = float(factor_exposures.get("crypto_factor", 0.0))
    crypto_share = float(factor_exposures.get("contribution", {}).get("crypto", 0.0))

    if abs(crypto_beta) >= crypto_beta_alert or crypto_share >= crypto_contrib_alert:
        severity = "high" if abs(crypto_beta) >= 0.6 or crypto_share >= 0.35 else "medium"
        signals.append(
            {
                "code": "CRYPTO_FACTOR",
                "severity": severity,
                "message": (
                    f"Crypto factor beta {crypto_beta:.2f} "
                    f"(risk contribution {crypto_share:.0%}) is a material systematic driver."
                ),
                "evidence": {
                    "crypto_factor_beta": crypto_beta,
                    "crypto_factor_contribution": crypto_share,
                },
            }
        )

    tech_beta = float(factor_exposures.get("tech_factor", 0.0))
    if abs(tech_beta) >= 0.55:
        signals.append(
            {
                "code": "TECH_FACTOR",
                "severity": "medium",
                "message": f"Tech factor beta {tech_beta:.2f} elevates growth-factor vulnerability.",
                "evidence": {"tech_factor_beta": tech_beta},
            }
        )

    rates_beta = float(factor_exposures.get("rates_factor", 0.0))
    if abs(rates_beta) >= 0.45:
        signals.append(
            {
                "code": "RATES_FACTOR",
                "severity": "medium",
                "message": f"Rates factor beta {rates_beta:.2f} increases duration sensitivity.",
                "evidence": {"rates_factor_beta": rates_beta},
            }
        )
    return signals
