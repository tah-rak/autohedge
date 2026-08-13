"""Whole-market tips and suggestions (equities, rates, commodities, crypto, etc.)."""

from __future__ import annotations

from typing import Any


def generate_market_tips(
    pulse: dict[str, Any],
    *,
    portfolio: dict[str, Any] | None = None,
    factor_exposures: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Produce practical market tips across the full tape.

    Crypto tips are included only as one category among equities, rates,
    commodities, and defensives.
    """
    tips: list[dict[str, Any]] = []
    sleeves = {s["id"]: s for s in pulse.get("sleeves", [])}
    regime = pulse.get("regime", "Neutral")

    def add(
        category: str,
        title: str,
        tip: str,
        priority: int,
        action: str,
    ) -> None:
        tips.append(
            {
                "category": category,
                "title": title,
                "tip": tip,
                "priority": priority,
                "action": action,
            }
        )

    # Regime-level guidance
    if regime == "Stress":
        add(
            "Market",
            "Stay defensive while stress persists",
            "Broad risk sleeves are soft. Favor cash buffers, reduce concentrated bets, and re-check hedges.",
            1,
            "Raise cash / tighten risk",
        )
    elif regime == "Cautious":
        add(
            "Market",
            "Balance over bravado",
            "The tape is mixed. Avoid adding one-way factor risk until breadth improves.",
            1,
            "Keep allocations balanced",
        )
    elif regime == "Constructive":
        add(
            "Market",
            "Participate — but stay selective",
            "Conditions support risk assets. Prefer diversified participation over chasing a single sleeve.",
            2,
            "Stay invested with discipline",
        )
    else:
        add(
            "Market",
            "Neutral tape: process over prediction",
            "No strong regime signal. Rebalance to targets and let factor exposures stay intentional.",
            3,
            "Rebalance to targets",
        )

    eq = sleeves.get("us_equities")
    if eq:
        if eq["change1d"] <= -0.01:
            add(
                "Equities",
                "US equities under pressure",
                f"SPY is {eq['change1d']:.1%} today. Review equity-heavy portfolios and avoid averaging into weak breadth blindly.",
                1,
                "Review equity beta",
            )
        elif eq["change20d"] >= 0.05:
            add(
                "Equities",
                "Equity trend still supportive",
                f"SPY is up {eq['change20d']:.1%} over ~1 month. Keep core equity exposure, but trim extreme winners if concentration rises.",
                2,
                "Hold core equities",
            )

    tech = sleeves.get("tech")
    if tech and (tech["change1d"] <= -0.015 or abs(tech.get("change20d", 0)) >= 0.08):
        add(
            "Technology",
            "Tech factor is moving hard",
            f"QQQ 1D {tech['change1d']:.1%} / 20D {tech['change20d']:.1%}. Watch growth concentration and single-name tech risk.",
            1 if tech["change1d"] < 0 else 2,
            "Check tech concentration",
        )

    rates = sleeves.get("rates")
    bonds = sleeves.get("bonds")
    if rates and rates["change1d"] <= -0.01:
        add(
            "Rates",
            "Long bonds selling off",
            "TLT weakness often means rising-rate pressure. Revisit long-duration exposure and barbell defensives carefully.",
            1,
            "Review duration risk",
        )
    elif bonds and bonds["change20d"] >= 0.02:
        add(
            "Fixed Income",
            "Bonds providing ballast",
            "Core bonds have been firm. They can stabilize portfolios when equity volatility rises.",
            3,
            "Keep bond ballast",
        )

    gold = sleeves.get("gold")
    if gold and gold["change1d"] >= 0.01:
        add(
            "Commodities",
            "Gold bid in the tape",
            "GLD strength can signal hedging demand. A modest gold sleeve may help if equity correlations climb.",
            2,
            "Consider diversifier sleeve",
        )

    intl = sleeves.get("international")
    em = sleeves.get("emerging")
    if intl and intl["change20d"] < -0.04:
        add(
            "International",
            "International equities lagging",
            "Developed ex-US weakness suggests staying selective on overseas beta until relative strength returns.",
            2,
            "Stay selective overseas",
        )
    if em and em["change1d"] <= -0.015:
        add(
            "Emerging Markets",
            "EM risk is elevated today",
            "Emerging markets can amplify global risk-off moves. Size EM sleeves conservatively in stress regimes.",
            2,
            "Keep EM sizing modest",
        )

    utilities = sleeves.get("utilities")
    if utilities and utilities["change1d"] > 0 and eq and eq["change1d"] < 0:
        add(
            "Defensive",
            "Defensives outperforming",
            "Utilities holding up while equities soften — a classic defensive rotation cue.",
            2,
            "Lean defensive if needed",
        )

    crypto = sleeves.get("crypto")
    if crypto:
        if crypto["change1d"] <= -0.03 or crypto["volatility"] >= 0.7:
            add(
                "Crypto",
                "Crypto factor is noisy",
                f"Digital assets are volatile (1D {crypto['change1d']:.1%}). Treat crypto as one factor among many — not the whole portfolio thesis.",
                2,
                "Cap crypto factor risk",
            )
        elif crypto["change20d"] >= 0.12:
            add(
                "Crypto",
                "Crypto strength is one sleeve, not the market",
                "Crypto is firm, but keep sizing proportional. Balance with equities, bonds, and diversifiers.",
                3,
                "Keep crypto proportional",
            )

    # Portfolio-aware tips when available
    if portfolio and factor_exposures:
        betas = factor_exposures.get("betas") or {
            "market": factor_exposures.get("market_factor", 0),
            "tech": factor_exposures.get("tech_factor", 0),
            "rates": factor_exposures.get("rates_factor", 0),
            "crypto": factor_exposures.get("crypto_factor", 0),
        }
        if abs(float(betas.get("tech", 0))) >= 0.5 and tech and tech["change1d"] < 0:
            add(
                "Portfolio",
                "Your Tech factor is exposed on a soft day",
                "This portfolio’s Tech factor is elevated while tech is weaker today. Consider trimming growth beta.",
                1,
                "Trim tech factor",
            )
        if abs(float(betas.get("crypto", 0))) >= 0.35 and crypto and crypto["change1d"] < -0.02:
            add(
                "Portfolio",
                "Crypto factor is biting",
                "Your Crypto factor contribution is material and crypto is soft. Reduce digital-asset beta or add ballast.",
                1,
                "Reduce crypto factor",
            )
        if float(betas.get("market", 0)) >= 0.9 and regime in {"Stress", "Cautious"}:
            add(
                "Portfolio",
                "High market beta in a fragile tape",
                "Portfolio market sensitivity is high while the regime is fragile. A cash or hedge sleeve can soften left tails.",
                1,
                "Lower market beta",
            )

    # Always include at least one process tip.
    add(
        "Process",
        "Refresh and compare sleeves",
        "Check equities, rates, commodities, and crypto together before acting. Single-sleeve narratives miss cross-asset risk.",
        4,
        "Review full market board",
    )

    tips.sort(key=lambda t: (t["priority"], t["category"]))
    # Keep a crisp board — breadth over spam.
    return tips[:8]
