"""Whole-market pulse analytics across equities, rates, commodities, and crypto."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from autohedge.market.universe import MARKET_SLEEVES


def _pct_change(series: pd.Series, windows: int) -> float:
    if len(series) <= windows:
        return 0.0
    a = float(series.iloc[-1])
    b = float(series.iloc[-1 - windows])
    if b == 0:
        return 0.0
    return a / b - 1.0


def _realized_vol(returns: pd.Series, window: int = 21) -> float:
    if len(returns) < 5:
        return 0.0
    return float(returns.tail(window).std(ddof=1) * np.sqrt(252))


def _tone(change_1d: float, change_20d: float) -> str:
    if change_1d <= -0.012 or change_20d <= -0.06:
        return "Risk-Off"
    if change_1d >= 0.012 or change_20d >= 0.06:
        return "Risk-On"
    if abs(change_1d) < 0.003 and abs(change_20d) < 0.02:
        return "Quiet"
    return "Mixed"


def build_market_pulse(prices: pd.DataFrame) -> dict[str, Any]:
    """Compute cross-asset market pulse cards and an overall regime summary."""
    rets = prices.pct_change().dropna()
    sleeves = []
    for spec in MARKET_SLEEVES:
        sym = spec["symbol"]
        if sym not in prices.columns:
            # Simulator may use BTC instead of BTC-USD
            alt = "BTC" if sym == "BTC-USD" and "BTC" in prices.columns else None
            if alt is None:
                continue
            sym = alt
        series = prices[sym].dropna()
        r = rets[sym] if sym in rets.columns else series.pct_change().dropna()
        c1 = _pct_change(series, 1)
        c5 = _pct_change(series, 5)
        c20 = _pct_change(series, 20)
        vol = _realized_vol(r)
        tone = _tone(c1, c20)
        sleeves.append(
            {
                "id": spec["id"],
                "label": spec["label"],
                "symbol": spec["symbol"],
                "category": spec["category"],
                "description": spec["description"],
                "last": float(series.iloc[-1]),
                "change1d": c1,
                "change5d": c5,
                "change20d": c20,
                "volatility": vol,
                "tone": tone,
            }
        )

    # Overall regime from major sleeves.
    by_id = {s["id"]: s for s in sleeves}
    equity = by_id.get("us_equities", {})
    tech = by_id.get("tech", {})
    rates = by_id.get("rates", {})
    gold = by_id.get("gold", {})
    crypto = by_id.get("crypto", {})

    risk_score = 0
    if equity.get("change1d", 0) < -0.008:
        risk_score += 2
    if equity.get("change20d", 0) < -0.04:
        risk_score += 2
    if tech.get("change1d", 0) < -0.01:
        risk_score += 1
    if rates.get("change1d", 0) < -0.008:  # bonds selling off => rates up pressure
        risk_score += 1
    if crypto.get("change1d", 0) < -0.03:
        risk_score += 1
    if gold.get("change1d", 0) > 0.01 and equity.get("change1d", 0) < 0:
        risk_score += 1

    if risk_score >= 5:
        regime = "Stress"
        regime_summary = "Multiple sleeves are under pressure — keep hedges and cash buffers intentional."
    elif risk_score >= 3:
        regime = "Cautious"
        regime_summary = "Mixed tape with rising cross-asset risk — favor balance over concentration."
    elif risk_score <= 1 and equity.get("change20d", 0) > 0.03:
        regime = "Constructive"
        regime_summary = "Broad conditions look supportive — still watch factor concentration."
    else:
        regime = "Neutral"
        regime_summary = "No single regime dominates — stay diversified across market factors."

    breadth = {
        "riskOnCount": sum(1 for s in sleeves if s["tone"] == "Risk-On"),
        "riskOffCount": sum(1 for s in sleeves if s["tone"] == "Risk-Off"),
        "mixedCount": sum(1 for s in sleeves if s["tone"] in {"Mixed", "Quiet"}),
    }

    return {
        "regime": regime,
        "regimeSummary": regime_summary,
        "breadth": breadth,
        "sleeves": sleeves,
        "highlights": {
            "equities1d": equity.get("change1d", 0.0),
            "tech1d": tech.get("change1d", 0.0),
            "rates1d": rates.get("change1d", 0.0),
            "gold1d": gold.get("change1d", 0.0),
            "crypto1d": crypto.get("change1d", 0.0),
        },
    }
