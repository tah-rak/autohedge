"""Human-readable report rendering for explainability."""

from __future__ import annotations

from typing import Any


def render_markdown_report(result: dict[str, Any]) -> str:
    portfolio = result.get("portfolio", {})
    metrics = result.get("metrics", {})
    lines: list[str] = []
    lines.append(f"# AutoHedge Report — {portfolio.get('name', 'Portfolio')}")
    lines.append("")
    lines.append(f"- Generated: `{result.get('generated_at')}`")
    lines.append(f"- Scenario: `{result.get('scenario')}`")
    lines.append(f"- Seed: `{result.get('seed')}`")
    lines.append("")
    lines.append("## Risk Snapshot")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    for key in [
        "annualized_volatility",
        "var_95",
        "cvar_95",
        "max_drawdown",
        "sharpe_proxy",
        "beta_proxy",
        "avg_correlation",
        "equity_exposure",
        "concentration_hhi",
        "top_weight",
    ]:
        val = metrics.get(key)
        if isinstance(val, float):
            if key in {"sharpe_proxy", "beta_proxy", "avg_correlation", "concentration_hhi"}:
                lines.append(f"| {key} | {val:.3f} |")
            else:
                lines.append(f"| {key} | {val:.2%} |")
        else:
            lines.append(f"| {key} | {val} |")

    score = result.get("risk_score", {})
    lines.append("")
    lines.append("## Risk Score")
    lines.append("")
    lines.append(f"- Label: `{score.get('risk_label')}`")
    lines.append(f"- Score: `{score.get('risk_score')}`")

    vol = result.get("volatility", {})
    lines.append("")
    lines.append("## Volatility Trends")
    lines.append("")
    lines.append(f"- Regime: `{vol.get('vol_regime')}`")
    lines.append(f"- Current vol: `{float(vol.get('ewma_vol', 0)):.2%}`")
    lines.append(f"- Forecast vol: `{float(vol.get('blended_vol', vol.get('forecast_vol', 0))):.2%}`")

    lines.append("")
    lines.append("## Market Signal Insights")
    lines.append("")
    for sig in result.get("signals", []):
        lines.append(
            f"- `{sig.get('code')}` ({sig.get('severity')}): {sig.get('message')}"
        )

    lines.append("")
    lines.append("## Hedge Recommendations")
    lines.append("")
    for i, rec in enumerate(result.get("recommendations", []), start=1):
        lines.append(f"### {i}. {rec.get('action')} — `{rec.get('instrument')}`")
        lines.append("")
        lines.append(f"- Confidence: `{rec.get('confidence')}`")
        lines.append(f"- Triggers: {', '.join(rec.get('trigger_signals', []))}")
        lines.append(f"- Expected effect: {rec.get('expected_effect')}")
        lines.append(f"- Recommendation rationale: {rec.get('rationale')}")
        lines.append("")

    lines.append("## Recommendation Rationale")
    lines.append("")
    for exp in result.get("explanations", []):
        lines.append(f"- {exp.get('narrative')}")

    lines.append("")
    lines.append("---")
    lines.append("_AutoHedge simulated analysis for research and education. Not investment advice._")
    return "\n".join(lines)
