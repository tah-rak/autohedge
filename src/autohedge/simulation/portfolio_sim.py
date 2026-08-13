"""Portfolio-level simulation helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from autohedge.simulation.market_simulator import ASSET_SPECS, prices_to_returns, simulate_prices


def portfolio_symbols(portfolio: dict[str, Any]) -> list[str]:
    # Factor proxies for Market / Tech / Rates / Crypto / Commodity estimation.
    factor_proxies = ("SPY", "QQQ", "TLT", "BTC", "GLD")
    symbols = [h["symbol"] for h in portfolio["holdings"]]
    for sym in factor_proxies:
        if sym not in symbols:
            symbols.append(sym)
    return symbols


def simulate_portfolio_market(
    portfolio: dict[str, Any],
    trading_days: int = 252,
    seed: int = 42,
    scenario: str = "baseline",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    symbols = portfolio_symbols(portfolio)
    prices = simulate_prices(symbols, trading_days=trading_days, seed=seed, scenario=scenario)
    returns = prices_to_returns(prices)
    return prices, returns


def portfolio_return_series(portfolio: dict[str, Any], returns: pd.DataFrame) -> pd.Series:
    weights = {h["symbol"]: float(h["weight"]) for h in portfolio["holdings"]}
    cash = float(portfolio.get("cash_weight", 0.0))
    aligned = returns[[s for s in weights if s in returns.columns]].copy()
    w = np.array([weights[s] for s in aligned.columns], dtype=float)
    # Cash earns ~0 in this simulation; remaining weight assumed cash.
    port = aligned.values @ w
    if cash > 0:
        # already excluded from invested weights; no extra return
        pass
    return pd.Series(port, index=aligned.index, name="portfolio")


def wealth_curve(returns: pd.Series) -> pd.Series:
    return (1.0 + returns).cumprod()


def holding_table(portfolio: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for h in portfolio["holdings"]:
        spec = ASSET_SPECS.get(h["symbol"], {})
        rows.append(
            {
                "symbol": h["symbol"],
                "name": h.get("name", spec.get("name", h["symbol"])),
                "asset_class": h.get("asset_class", spec.get("asset_class", "other")),
                "sector": h.get("sector", spec.get("sector", "unknown")),
                "weight": float(h["weight"]),
            }
        )
    return pd.DataFrame(rows)
