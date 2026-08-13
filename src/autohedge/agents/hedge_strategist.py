"""Hedge strategist agent — maps risk signals to actionable hedges."""

from __future__ import annotations

from typing import Any

from autohedge.agents.base import AgentMessage, BaseAgent, Recommendation


class HedgeStrategistAgent(BaseAgent):
    name = "hedge_strategist"

    def run(self, context: dict[str, Any]) -> AgentMessage:
        signals = context["signals"]
        metrics = context["metrics"]
        score = context["risk_score"]
        market = context.get("market_sensor", {})
        portfolio = context["portfolio"]
        min_confidence = float(context.get("min_confidence", 0.55))
        max_recs = int(context.get("max_recommendations", 5))

        codes = {s["code"] for s in signals}
        recs: list[Recommendation] = []

        if "HIGH_VOLATILITY" in codes or "DEEP_DRAWDOWN" in codes or score.get("risk_label") in {
            "high",
            "severe",
        }:
            cash_bump = 0.05 if score.get("risk_label") != "severe" else 0.10
            recs.append(
                Recommendation(
                    action="increase_cash",
                    instrument="CASH",
                    rationale=(
                        "Raise cash to reduce beta and absorb volatility while risk remains elevated."
                    ),
                    trigger_signals=sorted(
                        codes.intersection({"HIGH_VOLATILITY", "DEEP_DRAWDOWN", "HIGH_BETA", "EQUITY_HEAVY"})
                        or {"HIGH_VOLATILITY"}
                    ),
                    expected_effect=f"Lower equity exposure by ~{cash_bump:.0%} and dampen drawdowns.",
                    confidence=min(0.92, 0.60 + float(score.get("risk_score", 0.5)) * 0.3),
                    priority=1,
                    details={"suggested_cash_increase": cash_bump},
                )
            )

        market_signals = set(market.get("market_signals", []))
        risk_label = score.get("risk_label", "moderate")
        if (
            "HIGH_BETA" in codes
            or "EQUITY_HEAVY" in codes
            or ("risk_off_market_tape" in market_signals and risk_label in {"moderate", "high", "severe"})
        ):
            triggers = sorted(
                codes.intersection({"HIGH_BETA", "EQUITY_HEAVY", "CORRELATION_SPIKE"})
            )
            if "risk_off_market_tape" in market_signals:
                triggers = sorted(set(triggers) | {"RISK_OFF_TAPE"})
            if not triggers:
                triggers = ["RISK_OFF_TAPE"]
            recs.append(
                Recommendation(
                    action="add_inverse_etf_hedge",
                    instrument="SH",
                    rationale=(
                        "Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes."
                    ),
                    trigger_signals=triggers,
                    expected_effect="Partial market-beta offset without liquidating core holdings.",
                    confidence=0.72,
                    priority=2,
                    details={"suggested_weight": 0.05, "hedge_type": "inverse_etf"},
                )
            )

        tech_weight = sum(
            float(h["weight"])
            for h in portfolio["holdings"]
            if h.get("sector") == "technology"
        )
        if "SECTOR_CONCENTRATION" in codes and tech_weight >= 0.40:
            recs.append(
                Recommendation(
                    action="trim_sector_and_rebalance",
                    instrument="QQQ/AAPL/MSFT/NVDA",
                    rationale=(
                        "Technology concentration amplifies idiosyncratic and factor drawdowns; "
                        "trim winners and rotate toward broad market / defensives."
                    ),
                    trigger_signals=["SECTOR_CONCENTRATION", "CONCENTRATION"]
                    if "CONCENTRATION" in codes
                    else ["SECTOR_CONCENTRATION"],
                    expected_effect="Reduce single-factor vulnerability and lower portfolio HHI.",
                    confidence=0.78,
                    priority=2,
                    details={
                        "technology_weight": tech_weight,
                        "rebalance_toward": ["SPY", "XLU", "AGG"],
                        "trim_fraction": 0.15,
                    },
                )
            )

        crypto_weight = sum(
            float(h["weight"])
            for h in portfolio["holdings"]
            if h.get("asset_class") == "crypto" or h.get("sector") == "crypto"
        )
        crypto_factor = float(metrics.get("crypto_factor", 0.0))
        crypto_factor_share = float(metrics.get("crypto_factor_contribution", 0.0))
        if (
            "CRYPTO_FACTOR" in codes
            or "CRYPTO_HEAVY" in codes
            or abs(crypto_factor) >= 0.35
            or crypto_weight >= 0.25
        ):
            recs.append(
                Recommendation(
                    action="reduce_crypto_factor",
                    instrument="BTC/ETH/SOL/BITO",
                    rationale=(
                        "Elevated Crypto factor exposure is a systematic risk driver — not just a "
                        "ticker sleeve. Trim digital-asset beta and rotate into lower-factor sleeves "
                        "such as cash, bonds, or gold."
                    ),
                    trigger_signals=sorted(
                        codes.intersection(
                            {
                                "CRYPTO_FACTOR",
                                "CRYPTO_HEAVY",
                                "HIGH_VOLATILITY",
                                "DEEP_DRAWDOWN",
                                "SECTOR_CONCENTRATION",
                            }
                        )
                        or {"CRYPTO_FACTOR"}
                    ),
                    expected_effect="Lower Crypto factor beta and reduce factor risk contribution.",
                    confidence=0.82,
                    priority=1,
                    details={
                        "crypto_factor_beta": crypto_factor,
                        "crypto_factor_contribution": crypto_factor_share,
                        "crypto_weight": crypto_weight,
                        "suggested_trim_fraction": 0.25,
                        "rebalance_toward": ["CASH", "AGG", "GLD"],
                    },
                )
            )
            if score.get("risk_label") in {"high", "severe"} or "CRYPTO_FACTOR" in codes:
                recs.append(
                    Recommendation(
                        action="add_stable_ballast",
                        instrument="CASH",
                        rationale=(
                            "Increase cash as ballast while the Crypto factor remains an active "
                            "systematic risk contributor."
                        ),
                        trigger_signals=sorted(
                            codes.intersection({"CRYPTO_FACTOR", "CRYPTO_HEAVY", "HIGH_VOLATILITY"})
                            or {"CRYPTO_FACTOR"}
                        ),
                        expected_effect="Dilute Crypto factor weight and improve liquidity buffer.",
                        confidence=0.76,
                        priority=2,
                        details={"suggested_cash_increase": 0.08},
                    )
                )

        if "TECH_FACTOR" in codes:
            recs.append(
                Recommendation(
                    action="trim_sector_and_rebalance",
                    instrument="QQQ/NVDA",
                    rationale=(
                        "Tech factor beta is elevated; trim growth exposure and rebalance toward "
                        "broader market or defensive sleeves."
                    ),
                    trigger_signals=["TECH_FACTOR"],
                    expected_effect="Reduce Tech factor vulnerability.",
                    confidence=0.74,
                    priority=2,
                    details={"rebalance_toward": ["SPY", "XLU", "AGG"]},
                )
            )

        if "CORRELATION_SPIKE" in codes or metrics.get("avg_correlation", 0) > 0.7:
            recs.append(
                Recommendation(
                    action="add_diversifier",
                    instrument="GLD",
                    rationale=(
                        "Rising cross-asset correlations erode diversification; gold historically "
                        "provides a lower-correlation ballast in stress regimes."
                    ),
                    trigger_signals=["CORRELATION_SPIKE"],
                    expected_effect="Improve diversification and reduce average pairwise correlation.",
                    confidence=0.70,
                    priority=3,
                    details={"suggested_weight": 0.05, "funding": "trim_equities"},
                )
            )

        if metrics.get("equity_exposure", 0) >= 0.70 and "AGG" not in {
            h["symbol"] for h in portfolio["holdings"]
        }:
            recs.append(
                Recommendation(
                    action="add_duration_ballast",
                    instrument="AGG",
                    rationale="Bond allocation provides ballast when equity beta dominates risk.",
                    trigger_signals=sorted(codes.intersection({"EQUITY_HEAVY", "HIGH_BETA"}) or {"EQUITY_HEAVY"}),
                    expected_effect="Lower equity share and soften left-tail outcomes.",
                    confidence=0.68,
                    priority=3,
                    details={"suggested_weight": 0.08},
                )
            )

        if context.get("volatility", {}).get("vol_regime") == "elevated":
            recs.append(
                Recommendation(
                    action="volatility_target_rebalance",
                    instrument="PORTFOLIO",
                    rationale=(
                        "Scale risky sleeve toward a volatility target while blended vol regime is elevated."
                    ),
                    trigger_signals=["HIGH_VOLATILITY"] if "HIGH_VOLATILITY" in codes else ["VOL_REGIME"],
                    expected_effect="Stabilize realized volatility near policy target.",
                    confidence=0.74,
                    priority=1,
                    details={
                        "current_blended_vol": context.get("volatility", {}).get("blended_vol"),
                        "target_vol": 0.15,
                        "scale_factor": min(
                            1.0,
                            0.15 / max(float(context.get("volatility", {}).get("blended_vol", 0.15)), 1e-6),
                        ),
                    },
                )
            )

        # Options-style simulated hedge (educational; not a brokerage order).
        if score.get("risk_label") in {"high", "severe"} and metrics.get("var_95", 0) >= 0.02:
            recs.append(
                Recommendation(
                    action="simulate_put_overlay",
                    instrument="SPY_PUT_OVERLAY",
                    rationale=(
                        "A simulated protective-put overlay caps left-tail loss if the market "
                        "continues to sell off (options-style hedge for analysis only)."
                    ),
                    trigger_signals=sorted(
                        codes.intersection({"DEEP_DRAWDOWN", "HIGH_VOLATILITY", "HIGH_BETA"})
                        or {"HIGH_VOLATILITY"}
                    ),
                    expected_effect="Bound downside beyond strike in exchange for premium drag.",
                    confidence=0.66,
                    priority=4,
                    details={
                        "hedge_type": "options_style_simulated",
                        "notional_fraction": 0.5,
                        "approx_premium_drag_annual": 0.02,
                    },
                )
            )

        if not recs:
            recs.append(
                Recommendation(
                    action="hold_and_monitor",
                    instrument="PORTFOLIO",
                    rationale="No material hedge trigger; maintain allocation and refresh signals next run.",
                    trigger_signals=["STABLE"],
                    expected_effect="Avoid unnecessary turnover while risk remains contained.",
                    confidence=0.80,
                    priority=5,
                    details={},
                )
            )

        filtered = [r for r in recs if r.confidence >= min_confidence]
        filtered.sort(key=lambda r: (r.priority, -r.confidence))
        filtered = filtered[:max_recs]

        content = f"Generated {len(filtered)} hedge recommendation(s) from {len(codes)} signal code(s)."
        return AgentMessage(
            agent=self.name,
            role="recommendation",
            content=content,
            data={"recommendations": [r.to_dict() for r in filtered]},
        )
