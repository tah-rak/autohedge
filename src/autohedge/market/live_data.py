"""Market data fetchers — prefer free live quotes, fall back to simulation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from autohedge.market.universe import LIVE_TO_SIM_SYMBOL, MARKET_SLEEVES
from autohedge.simulation.market_simulator import simulate_prices

logger = logging.getLogger("autohedge.market.data")


def _empty_frame(symbols: list[str]) -> pd.DataFrame:
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=2)
    return pd.DataFrame(100.0, index=idx, columns=symbols)


def fetch_live_history(period: str = "6mo") -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Try free Yahoo Finance data via yfinance (no API key).

    Returns (prices, meta). On failure, caller should use simulation fallback.
    """
    symbols = [s["symbol"] for s in MARKET_SLEEVES]
    meta: dict[str, Any] = {
        "mode": "live",
        "provider": "Yahoo Finance (yfinance)",
        "requiresApiKey": False,
        "asOf": datetime.now(timezone.utc).isoformat(),
        "note": "Near-real-time public market quotes. Delays may apply.",
    }
    try:
        import yfinance as yf
    except ImportError:
        meta.update({"mode": "unavailable", "error": "yfinance not installed"})
        return _empty_frame(symbols), meta

    try:
        raw = yf.download(
            tickers=symbols,
            period=period,
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=False,
        )
        if raw is None or raw.empty:
            meta.update({"mode": "unavailable", "error": "empty live response"})
            return _empty_frame(symbols), meta

        frames: dict[str, pd.Series] = {}
        for sym in symbols:
            try:
                if isinstance(raw.columns, pd.MultiIndex):
                    if (sym, "Close") in raw.columns:
                        series = raw[(sym, "Close")]
                    else:
                        continue
                else:
                    series = raw["Close"]
                series = pd.Series(series).dropna()
                if not series.empty:
                    frames[sym] = series.astype(float)
            except Exception:
                continue

        if len(frames) < 3:
            meta.update({"mode": "unavailable", "error": "too few live symbols"})
            return _empty_frame(symbols), meta

        prices = pd.DataFrame(frames).dropna(how="all").ffill().dropna()
        meta["symbols"] = list(prices.columns)
        meta["asOf"] = datetime.now(timezone.utc).isoformat()
        return prices, meta
    except Exception as exc:
        logger.warning("Live market fetch failed: %s", exc)
        meta.update({"mode": "unavailable", "error": str(exc)})
        return _empty_frame(symbols), meta


def fetch_simulated_history(
    seed: int = 42,
    trading_days: int = 120,
    scenario: str = "baseline",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Offline-friendly whole-market path used when live data is unavailable."""
    sim_symbols = list(dict.fromkeys(LIVE_TO_SIM_SYMBOL.values()))
    sim_prices = simulate_prices(
        sim_symbols, trading_days=trading_days, seed=seed, scenario=scenario
    )
    # Map simulator symbols back to market-board labels (BTC -> BTC-USD).
    columns = {}
    for live_sym, sim_sym in LIVE_TO_SIM_SYMBOL.items():
        if sim_sym in sim_prices.columns:
            columns[live_sym] = sim_prices[sim_sym]
    prices = pd.DataFrame(columns, index=sim_prices.index)
    meta = {
        "mode": "simulated",
        "provider": "AutoHedge market simulator",
        "requiresApiKey": False,
        "asOf": datetime.now(timezone.utc).isoformat(),
        "note": "Live quotes unavailable — using a fresh simulated market tape.",
        "symbols": list(prices.columns),
        "seed": seed,
        "scenario": scenario,
    }
    return prices, meta


def load_market_history(
    *,
    prefer_live: bool = True,
    seed: int | None = None,
    scenario: str = "baseline",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load whole-market history with live-first, simulation fallback."""
    if prefer_live:
        prices, meta = fetch_live_history()
        if meta.get("mode") == "live" and not prices.empty:
            return prices, meta
    if seed is None:
        seed = int(datetime.now(timezone.utc).timestamp() // 60) % 10_000
    return fetch_simulated_history(seed=seed, scenario=scenario)
