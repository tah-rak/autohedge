"""Risk analyst agent — interprets metrics, ML score, and threshold signals."""

from __future__ import annotations

from typing import Any

from autohedge.agents.base import AgentMessage, BaseAgent


class RiskAnalystAgent(BaseAgent):
    name = "risk_analyst"

    def run(self, context: dict[str, Any]) -> AgentMessage:
        metrics = context["metrics"]
        signals = context["signals"]
        score = context["risk_score"]
        vol = context.get("volatility", {})

        high = [s for s in signals if s.get("severity") in {"high", "medium"} and s["code"] != "STABLE"]
        content = (
            f"Risk label={score.get('risk_label')} (score={score.get('risk_score'):.2f}, "
            f"method={score.get('method')}). "
            f"Vol={metrics['annualized_volatility']:.1%}, VaR95={metrics['var_95']:.2%}, "
            f"MDD={metrics['max_drawdown']:.1%}, beta={metrics['beta_proxy']:.2f}, "
            f"HHI={metrics['concentration_hhi']:.3f}. "
            f"Active signals={len(high)}."
        )
        return AgentMessage(
            agent=self.name,
            role="analysis",
            content=content,
            data={
                "active_signal_codes": [s["code"] for s in high],
                "metrics": metrics,
                "risk_score": score,
                "volatility": vol,
            },
        )
