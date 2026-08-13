"""Explainer agent — ties each recommendation to evidence in plain language."""

from __future__ import annotations

from typing import Any

from autohedge.agents.base import AgentMessage, BaseAgent


class ExplainerAgent(BaseAgent):
    name = "explainer"

    def run(self, context: dict[str, Any]) -> AgentMessage:
        recommendations = context.get("recommendations", [])
        signals = {s["code"]: s for s in context.get("signals", [])}
        metrics = context.get("metrics", {})
        score = context.get("risk_score", {})

        explanations = []
        for rec in recommendations:
            trigger_details = []
            for code in rec.get("trigger_signals", []):
                sig = signals.get(code)
                if sig:
                    trigger_details.append(
                        {
                            "code": code,
                            "severity": sig.get("severity"),
                            "message": sig.get("message"),
                            "evidence": sig.get("evidence", {}),
                        }
                    )
                else:
                    trigger_details.append({"code": code, "message": "Derived market/ML signal"})

            narrative = (
                f"Recommend `{rec['action']}` via `{rec['instrument']}` because "
                f"{rec['rationale']} "
                f"Triggered by: {', '.join(rec.get('trigger_signals', []))}. "
                f"Portfolio risk label is {score.get('risk_label')} with "
                f"vol={float(metrics.get('annualized_volatility', 0)):.1%} and "
                f"max drawdown={float(metrics.get('max_drawdown', 0)):.1%}."
            )
            explanations.append(
                {
                    "action": rec.get("action"),
                    "instrument": rec.get("instrument"),
                    "confidence": rec.get("confidence"),
                    "expected_effect": rec.get("expected_effect"),
                    "trigger_details": trigger_details,
                    "narrative": narrative,
                }
            )

        content = f"Built transparent explanations for {len(explanations)} recommendation(s)."
        return AgentMessage(
            agent=self.name,
            role="explanation",
            content=content,
            data={"explanations": explanations},
        )
