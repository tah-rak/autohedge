"""Whole-market universe definitions used by Market Insights."""

from __future__ import annotations

from typing import TypedDict


class MarketSleeve(TypedDict):
    id: str
    label: str
    symbol: str
    category: str
    description: str


# Broad market coverage — crypto is one sleeve among many.
MARKET_SLEEVES: list[MarketSleeve] = [
    {
        "id": "us_equities",
        "label": "US Equities",
        "symbol": "SPY",
        "category": "Equities",
        "description": "Broad US equity market pulse",
    },
    {
        "id": "tech",
        "label": "Technology",
        "symbol": "QQQ",
        "category": "Equities",
        "description": "Growth / Nasdaq-linked tech factor",
    },
    {
        "id": "international",
        "label": "International",
        "symbol": "EFA",
        "category": "Equities",
        "description": "Developed international equities",
    },
    {
        "id": "emerging",
        "label": "Emerging Markets",
        "symbol": "EEM",
        "category": "Equities",
        "description": "Emerging-market equity risk",
    },
    {
        "id": "bonds",
        "label": "Core Bonds",
        "symbol": "AGG",
        "category": "Fixed Income",
        "description": "Investment-grade bond ballast",
    },
    {
        "id": "rates",
        "label": "Long Rates",
        "symbol": "TLT",
        "category": "Fixed Income",
        "description": "Long-duration Treasury sensitivity",
    },
    {
        "id": "gold",
        "label": "Gold",
        "symbol": "GLD",
        "category": "Commodities",
        "description": "Defensive commodity diversifier",
    },
    {
        "id": "real_estate",
        "label": "Real Estate",
        "symbol": "VNQ",
        "category": "Alternatives",
        "description": "Listed real-estate exposure",
    },
    {
        "id": "utilities",
        "label": "Utilities",
        "symbol": "XLU",
        "category": "Defensive",
        "description": "Lower-beta defensive equity sleeve",
    },
    {
        "id": "crypto",
        "label": "Crypto",
        "symbol": "BTC-USD",
        "category": "Crypto",
        "description": "Digital-asset factor (one part of the full market)",
    },
]

# Map live symbols to simulator symbols when falling back.
LIVE_TO_SIM_SYMBOL = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "EFA": "EFA",
    "EEM": "EEM",
    "AGG": "AGG",
    "TLT": "TLT",
    "GLD": "GLD",
    "VNQ": "VNQ",
    "XLU": "XLU",
    "BTC-USD": "BTC",
}
