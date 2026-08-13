"""Market sensor agent — summarizes regime and market signals."""

from __future__ import annotations

from typing import Any

from autohedge.agents.base import AgentMessage, BaseAgent
from autohedge.simulation.portfolio_sim import portfolio_return_series


class MarketSensorAgent(BaseAgent):
    name = "market_sensor"

    def run(self, context: dict[str, Any]) -> AgentMessage:
        returns = context["returns"]
        portfolio = context["portfolio"]
        vol_info = context.get("volatility", {})
        scenario = context.get("scenario", "baseline")

        port = portfolio_return_series(portfolio, returns)
        recent = port.tail(21)
        recent_return = float((1.0 + recent).prod() - 1.0) if len(recent) else 0.0
        hit_rate = float((recent < 0).mean())
        spy = returns["SPY"].tail(21) if "SPY" in returns.columns else recent
        market_return = float((1.0 + spy).prod() - 1.0) if len(spy) else 0.0

        signals = []
        if vol_info.get("vol_regime") == "elevated":
            signals.append("elevated_volatility_regime")
        if recent_return < -0.03:
            signals.append("negative_portfolio_momentum")
        if market_return < -0.03:
            signals.append("risk_off_market_tape")
        if hit_rate >= 0.55:
            signals.append("high_down_day_frequency")

        content = (
            f"Scenario={scenario}. Blended vol={vol_info.get('blended_vol', float('nan')):.1%} "
            f"({vol_info.get('vol_regime', 'n/a')}). 21d portfolio return={recent_return:.1%}, "
            f"market return={market_return:.1%}, down-day share={hit_rate:.0%}."
        )
        return AgentMessage(
            agent=self.name,
            role="observation",
            content=content,
            data={
                "scenario": scenario,
                "portfolio_return_21d": recent_return,
                "market_return_21d": market_return,
                "down_day_share_21d": hit_rate,
                "market_signals": signals,
                "recent_return": recent_return,
            },
        )
