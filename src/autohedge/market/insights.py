"""Whole-market insights orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from autohedge.market.live_data import load_market_history
from autohedge.market.pulse import build_market_pulse
from autohedge.market.tips import generate_market_tips


def build_market_insights(
    *,
    prefer_live: bool = True,
    seed: int | None = None,
    scenario: str = "baseline",
    portfolio: dict[str, Any] | None = None,
    factor_exposures: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Full-market analysis package for the dashboard.

    Covers equities, tech, international, bonds/rates, gold, real estate,
    utilities, and crypto — with actionable tips across the tape.
    """
    prices, data_meta = load_market_history(
        prefer_live=prefer_live,
        seed=seed,
        scenario=scenario,
    )
    pulse = build_market_pulse(prices)
    tips = generate_market_tips(
        pulse,
        portfolio=portfolio,
        factor_exposures=factor_exposures,
    )

    return {
        "title": "Market Insights",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "data": {
            "mode": data_meta.get("mode"),
            "provider": data_meta.get("provider"),
            "note": data_meta.get("note"),
            "requiresApiKey": False,
        },
        "regime": pulse.get("regime"),
        "regimeSummary": pulse.get("regimeSummary"),
        "breadth": pulse.get("breadth"),
        "sleeves": [
            {
                **s,
                "change1dLabel": f"{s['change1d'] * 100:+.2f}%",
                "change5dLabel": f"{s['change5d'] * 100:+.2f}%",
                "change20dLabel": f"{s['change20d'] * 100:+.1f}%",
                "volatilityLabel": f"{s['volatility'] * 100:.1f}%",
                "lastLabel": f"{s['last']:.2f}",
            }
            for s in pulse.get("sleeves", [])
        ],
        "tips": tips,
        "suggestions": [
            {
                "title": t["title"],
                "detail": t["tip"],
                "action": t["action"],
                "category": t["category"],
            }
            for t in tips
        ],
    }
