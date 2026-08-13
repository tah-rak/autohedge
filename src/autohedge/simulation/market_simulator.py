"""Realistic correlated market path simulator (extendable to live data adapters)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


# Approximate annualized drifts, vols, and a factor-style correlation scaffold.
# These are simulation priors — not live quotes. See docs/DATA.md.
ASSET_SPECS: Dict[str, dict] = {
    "AAPL": {
        "name": "Apple",
        "asset_class": "equity",
        "sector": "technology",
        "mu": 0.11,
        "sigma": 0.28,
        "beta": 1.15,
    },
    "MSFT": {
        "name": "Microsoft",
        "asset_class": "equity",
        "sector": "technology",
        "mu": 0.10,
        "sigma": 0.24,
        "beta": 1.05,
    },
    "NVDA": {
        "name": "NVIDIA",
        "asset_class": "equity",
        "sector": "technology",
        "mu": 0.18,
        "sigma": 0.48,
        "beta": 1.60,
    },
    "AMZN": {
        "name": "Amazon",
        "asset_class": "equity",
        "sector": "consumer",
        "mu": 0.12,
        "sigma": 0.32,
        "beta": 1.20,
    },
    "GOOGL": {
        "name": "Alphabet",
        "asset_class": "equity",
        "sector": "technology",
        "mu": 0.10,
        "sigma": 0.26,
        "beta": 1.10,
    },
    "SPY": {
        "name": "S&P 500 ETF",
        "asset_class": "etf",
        "sector": "broad_market",
        "mu": 0.08,
        "sigma": 0.16,
        "beta": 1.00,
    },
    "QQQ": {
        "name": "Nasdaq-100 ETF",
        "asset_class": "etf",
        "sector": "technology",
        "mu": 0.10,
        "sigma": 0.22,
        "beta": 1.20,
    },
    "EFA": {
        "name": "Developed Markets ETF",
        "asset_class": "etf",
        "sector": "international",
        "mu": 0.06,
        "sigma": 0.18,
        "beta": 0.90,
    },
    "EEM": {
        "name": "Emerging Markets ETF",
        "asset_class": "etf",
        "sector": "emerging",
        "mu": 0.07,
        "sigma": 0.22,
        "beta": 1.10,
    },
    "AGG": {
        "name": "US Aggregate Bond ETF",
        "asset_class": "bond",
        "sector": "fixed_income",
        "mu": 0.03,
        "sigma": 0.05,
        "beta": -0.10,
    },
    "TLT": {
        "name": "Long-Term Treasury ETF",
        "asset_class": "bond",
        "sector": "rates",
        "mu": 0.02,
        "sigma": 0.14,
        "beta": -0.30,
    },
    "GLD": {
        "name": "Gold Trust",
        "asset_class": "commodity",
        "sector": "precious_metals",
        "mu": 0.04,
        "sigma": 0.15,
        "beta": 0.05,
    },
    "VNQ": {
        "name": "Real Estate ETF",
        "asset_class": "etf",
        "sector": "real_estate",
        "mu": 0.06,
        "sigma": 0.20,
        "beta": 0.80,
    },
    "XLU": {
        "name": "Utilities Select Sector",
        "asset_class": "etf",
        "sector": "utilities",
        "mu": 0.05,
        "sigma": 0.14,
        "beta": 0.45,
    },
    "VYM": {
        "name": "High Dividend Yield ETF",
        "asset_class": "etf",
        "sector": "dividend",
        "mu": 0.07,
        "sigma": 0.15,
        "beta": 0.75,
    },
    "BTC": {
        "name": "Bitcoin",
        "asset_class": "crypto",
        "sector": "crypto",
        "mu": 0.22,
        "sigma": 0.68,
        "beta": 1.45,
    },
    "ETH": {
        "name": "Ethereum",
        "asset_class": "crypto",
        "sector": "crypto",
        "mu": 0.20,
        "sigma": 0.75,
        "beta": 1.55,
    },
    "SOL": {
        "name": "Solana",
        "asset_class": "crypto",
        "sector": "crypto",
        "mu": 0.28,
        "sigma": 0.95,
        "beta": 1.70,
    },
    "BTCUSD": {
        "name": "Bitcoin",
        "asset_class": "crypto",
        "sector": "crypto",
        "mu": 0.22,
        "sigma": 0.68,
        "beta": 1.45,
    },
    "SH": {
        "name": "Short S&P 500 ETF",
        "asset_class": "etf",
        "sector": "hedge",
        "mu": -0.07,
        "sigma": 0.16,
        "beta": -1.00,
    },
    "PSQ": {
        "name": "Short QQQ ETF",
        "asset_class": "etf",
        "sector": "hedge",
        "mu": -0.09,
        "sigma": 0.22,
        "beta": -1.20,
    },
    "BITO": {
        "name": "Bitcoin Strategy ETF",
        "asset_class": "etf",
        "sector": "crypto",
        "mu": 0.18,
        "sigma": 0.62,
        "beta": 1.35,
    },
}


@dataclass
class MarketScenario:
    name: str
    label: str
    description: str
    market_shock: float = 0.0
    vol_multiplier: float = 1.0
    corr_boost: float = 0.0
    rate_shock: float = 0.0
    crypto_shock: float = 0.0
    crypto_vol_multiplier: float = 1.0


SCENARIOS: Dict[str, MarketScenario] = {
    "baseline": MarketScenario(
        name="baseline",
        label="Baseline Market",
        description="Typical market conditions with historical-like volatility.",
    ),
    "risk_off": MarketScenario(
        name="risk_off",
        label="Risk-Off Stress",
        description="Broad selloff with rising correlations and defensive flows.",
        market_shock=-0.0012,
        vol_multiplier=1.6,
        corr_boost=0.20,
        rate_shock=-0.0002,
        crypto_shock=-0.0020,
        crypto_vol_multiplier=1.4,
    ),
    "tech_drawdown": MarketScenario(
        name="tech_drawdown",
        label="Tech Drawdown",
        description="Technology factor stress with elevated growth-stock volatility.",
        market_shock=-0.0008,
        vol_multiplier=1.4,
        corr_boost=0.15,
        crypto_shock=-0.0010,
        crypto_vol_multiplier=1.2,
    ),
    "inflation_spike": MarketScenario(
        name="inflation_spike",
        label="Inflation Spike",
        description="Rising rates pressure bonds while commodities firm.",
        market_shock=-0.0004,
        vol_multiplier=1.25,
        corr_boost=0.10,
        rate_shock=0.0005,
        crypto_shock=-0.0006,
        crypto_vol_multiplier=1.15,
    ),
    "crypto_stress": MarketScenario(
        name="crypto_stress",
        label="Crypto Stress",
        description="Sharp digital-asset drawdown with elevated crypto volatility.",
        market_shock=-0.0003,
        vol_multiplier=1.15,
        corr_boost=0.12,
        crypto_shock=-0.0035,
        crypto_vol_multiplier=2.0,
    ),
}


def asset_display_name(symbol: str) -> str:
    return ASSET_SPECS.get(symbol, {}).get("name", symbol)


def _correlation_matrix(symbols: List[str], corr_boost: float = 0.0) -> np.ndarray:
    n = len(symbols)
    betas = np.array([ASSET_SPECS.get(s, {"beta": 1.0})["beta"] for s in symbols], dtype=float)
    corr = np.outer(betas, betas)
    corr /= max(np.max(np.abs(corr)), 1e-6)
    corr = np.clip(corr, -0.85, 0.95)
    np.fill_diagonal(corr, 1.0)
    # Crypto cluster: boost pairwise correlation among crypto names.
    for i, a in enumerate(symbols):
        for j, b in enumerate(symbols):
            if i >= j:
                continue
            ac = ASSET_SPECS.get(a, {}).get("asset_class")
            bc = ASSET_SPECS.get(b, {}).get("asset_class")
            if ac == "crypto" and bc == "crypto":
                corr[i, j] = corr[j, i] = max(corr[i, j], 0.72)
    if corr_boost:
        corr = corr + corr_boost * (np.ones_like(corr) - np.eye(n))
        corr = np.clip(corr, -0.95, 0.98)
        np.fill_diagonal(corr, 1.0)
    eigvals, eigvecs = np.linalg.eigh(corr)
    eigvals = np.clip(eigvals, 1e-6, None)
    corr = eigvecs @ np.diag(eigvals) @ eigvecs.T
    d = np.sqrt(np.diag(corr))
    corr = corr / np.outer(d, d)
    np.fill_diagonal(corr, 1.0)
    return corr


def simulate_prices(
    symbols: Iterable[str],
    trading_days: int = 252,
    seed: int = 42,
    scenario: str = "baseline",
    start_price: float = 100.0,
) -> pd.DataFrame:
    """Simulate correlated GBM-like daily prices for the requested symbols."""
    symbols = list(dict.fromkeys(symbols))
    if not symbols:
        raise ValueError("At least one symbol is required")

    sc = SCENARIOS.get(scenario, SCENARIOS["baseline"])
    rng = np.random.default_rng(seed)
    corr = _correlation_matrix(symbols, corr_boost=sc.corr_boost)
    chol = np.linalg.cholesky(corr)

    mus = []
    sigmas = []
    for s in symbols:
        spec = ASSET_SPECS.get(
            s, {"mu": 0.06, "sigma": 0.20, "asset_class": "other", "beta": 1.0, "sector": "unknown"}
        )
        mu = spec["mu"] / 252.0 + sc.market_shock * spec.get("beta", 1.0)
        if spec.get("asset_class") == "bond":
            mu += sc.rate_shock
        if s in {"GLD"} and sc.name == "inflation_spike":
            mu += 0.0004
        if sc.name == "tech_drawdown" and spec.get("sector") == "technology":
            mu -= 0.0007
            sigma = spec["sigma"] * sc.vol_multiplier * 1.15 / np.sqrt(252.0)
        elif spec.get("asset_class") == "crypto":
            mu += sc.crypto_shock
            sigma = spec["sigma"] * sc.vol_multiplier * sc.crypto_vol_multiplier / np.sqrt(252.0)
        else:
            sigma = spec["sigma"] * sc.vol_multiplier / np.sqrt(252.0)
        mus.append(mu)
        sigmas.append(sigma)

    mus = np.asarray(mus)
    sigmas = np.asarray(sigmas)
    z = rng.standard_normal(size=(trading_days, len(symbols)))
    shocks = z @ chol.T
    rets = mus + sigmas * shocks
    prices = start_price * np.cumprod(1.0 + rets, axis=0)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=trading_days)
    return pd.DataFrame(prices, index=idx, columns=symbols)


def prices_to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()
