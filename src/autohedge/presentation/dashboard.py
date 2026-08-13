"""Product-facing presentation layer — never expose internal system labels in UI payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from autohedge.simulation.market_simulator import SCENARIOS, asset_display_name


SIGNAL_LABELS = {
    "HIGH_VOLATILITY": "Elevated Volatility",
    "DEEP_DRAWDOWN": "Deep Drawdown",
    "CONCENTRATION": "Position Concentration",
    "CORRELATION_SPIKE": "Correlation Spike",
    "HIGH_BETA": "High Market Sensitivity",
    "EQUITY_HEAVY": "Equity-Heavy Exposure",
    "CRYPTO_HEAVY": "Crypto Sleeve Concentration",
    "CRYPTO_FACTOR": "Crypto Factor Risk",
    "TECH_FACTOR": "Tech Factor Risk",
    "RATES_FACTOR": "Rates Factor Risk",
    "SECTOR_CONCENTRATION": "Sector Concentration",
    "STABLE": "Stable Conditions",
    "RISK_OFF_TAPE": "Risk-Off Market Tape",
    "VOL_REGIME": "Volatility Regime Shift",
}

ACTION_LABELS = {
    "increase_cash": "Increase Cash Buffer",
    "add_inverse_etf_hedge": "Add Market Hedge",
    "trim_sector_and_rebalance": "Trim & Rebalance Sector",
    "reduce_crypto_exposure": "Reduce Crypto Sleeve",
    "reduce_crypto_factor": "Reduce Crypto Factor",
    "add_stable_ballast": "Add Stable Ballast",
    "add_diversifier": "Add Diversifier",
    "add_duration_ballast": "Add Bond Ballast",
    "volatility_target_rebalance": "Volatility-Target Rebalance",
    "simulate_put_overlay": "Protective Overlay (Simulated)",
    "hold_and_monitor": "Hold & Monitor",
}

ASSET_CLASS_LABELS = {
    "equity": "Stock",
    "etf": "ETF",
    "bond": "Bond",
    "commodity": "Commodity",
    "crypto": "Crypto",
    "cash": "Cash",
    "other": "Other",
}

RISK_LABELS = {
    "low": "Low",
    "moderate": "Moderate",
    "high": "High",
    "severe": "Severe",
}

VOL_REGIME_LABELS = {
    "calm": "Calm",
    "normal": "Normal",
    "elevated": "Elevated",
}

SCENARIO_LABELS = {k: v.label for k, v in SCENARIOS.items()}


def _pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.{digits}f}%"


def _num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}"


def _downsample(dates: list[str], values: list[float], max_points: int = 64) -> list[dict[str, Any]]:
    n = len(values)
    if n == 0:
        return []
    if n <= max_points:
        return [{"date": d, "value": float(v)} for d, v in zip(dates, values)]
    step = max(1, n // max_points)
    points = [{"date": dates[i], "value": float(values[i])} for i in range(0, n, step)]
    if points[-1]["date"] != dates[-1]:
        points.append({"date": dates[-1], "value": float(values[-1])})
    return points


def present_analysis(
    raw: dict[str, Any],
    *,
    portfolio_id: str,
    portfolio_version: str = "1.0",
    run_id: str | None = None,
) -> dict[str, Any]:
    """Convert internal analysis into a polished product dashboard payload."""
    metrics = raw.get("metrics", {})
    score = raw.get("risk_score", {})
    vol = raw.get("volatility", {})
    scenario = raw.get("scenario", "baseline")
    portfolio = raw.get("portfolio", {})
    series = raw.get("series", {})
    generated_at = raw.get("generated_at") or datetime.now(timezone.utc).isoformat()
    run_id = run_id or f"SIM-{raw.get('seed', 0)}-{scenario[:3].upper()}"

    risk_label = RISK_LABELS.get(str(score.get("risk_label", "moderate")), "Moderate")

    holdings = []
    for h in portfolio.get("holdings", []):
        symbol = h.get("symbol", "")
        holdings.append(
            {
                "symbol": symbol,
                "name": h.get("name") or asset_display_name(symbol),
                "assetClass": ASSET_CLASS_LABELS.get(h.get("asset_class", "other"), "Other"),
                "sector": str(h.get("sector", "unknown")).replace("_", " ").title(),
                "weight": float(h.get("weight", 0.0)),
                "weightLabel": _pct(h.get("weight", 0.0)),
            }
        )

    exposure = {
        "equityEtfs": float(metrics.get("equity_exposure", 0.0)),
        "crypto": sum(
            float(h.get("weight", 0.0))
            for h in portfolio.get("holdings", [])
            if h.get("asset_class") == "crypto" or h.get("sector") == "crypto"
        ),
        "cash": float(portfolio.get("cash_weight", 0.0)),
    }
    exposure["other"] = max(0.0, 1.0 - exposure["equityEtfs"] - exposure["crypto"] - exposure["cash"])

    signals = []
    for s in raw.get("signals", []):
        code = s.get("code", "")
        signals.append(
            {
                "id": code,
                "title": SIGNAL_LABELS.get(code, code.replace("_", " ").title()),
                "severity": s.get("severity", "low"),
                "summary": s.get("message", ""),
            }
        )

    recommendations = []
    explanations = {e.get("action"): e for e in raw.get("explanations", [])}
    for rec in raw.get("recommendations", []):
        action = rec.get("action", "")
        exp = explanations.get(action, {})
        recommendations.append(
            {
                "title": ACTION_LABELS.get(action, action.replace("_", " ").title()),
                "instrument": rec.get("instrument"),
                "confidence": float(rec.get("confidence", 0.0)),
                "confidenceLabel": f"{float(rec.get('confidence', 0.0)) * 100:.0f}%",
                "expectedEffect": rec.get("expected_effect"),
                "rationale": rec.get("rationale"),
                "triggers": [
                    SIGNAL_LABELS.get(t, t.replace("_", " ").title())
                    for t in rec.get("trigger_signals", [])
                ],
                "narrative": exp.get("narrative") or rec.get("rationale"),
            }
        )

    wealth_dates = series.get("wealth_dates", [])
    wealth_values = series.get("wealth_values", [])
    vol_dates = series.get("rolling_vol_dates", [])
    vol_values = series.get("rolling_vol_values", [])

    # Strip any internal engine keys from the product surface.
    payload = {
        "product": "AutoHedge",
        "title": "Portfolio Risk Analysis",
        "run": {
            "id": run_id,
            "generatedAt": generated_at,
            "portfolioId": portfolio_id,
            "portfolioName": portfolio.get("name"),
            "portfolioVersion": portfolio_version,
            "simulationVersion": f"scenario:{scenario}",
            "scenario": scenario,
            "scenarioLabel": SCENARIO_LABELS.get(scenario, scenario.replace("_", " ").title()),
            "seed": raw.get("seed"),
        },
        "summary": {
            "riskScore": {
                "label": risk_label,
                "value": float(score.get("risk_score", 0.0)),
                "display": f"{float(score.get('risk_score', 0.0)) * 100:.0f}",
            },
            "totalReturn": float(series.get("total_return", 0.0)),
            "totalReturnLabel": _pct(series.get("total_return", 0.0)),
            "volatility": float(metrics.get("annualized_volatility", 0.0)),
            "volatilityLabel": _pct(metrics.get("annualized_volatility", 0.0)),
            "maxDrawdown": float(metrics.get("max_drawdown", 0.0)),
            "maxDrawdownLabel": _pct(metrics.get("max_drawdown", 0.0)),
            "var95": float(metrics.get("var_95", 0.0)),
            "var95Label": _pct(metrics.get("var_95", 0.0), 2),
        },
        "riskAnalysis": {
            "metrics": [
                {"label": "Volatility", "value": _pct(metrics.get("annualized_volatility"))},
                {"label": "Value at Risk (95%)", "value": _pct(metrics.get("var_95"), 2)},
                {"label": "Expected Shortfall", "value": _pct(metrics.get("cvar_95"), 2)},
                {"label": "Max Drawdown", "value": _pct(metrics.get("max_drawdown"))},
                {"label": "Market Sensitivity", "value": _num(metrics.get("beta_proxy"))},
                {"label": "Crypto Factor", "value": _num(metrics.get("crypto_factor"))},
                {"label": "Avg Correlation", "value": _num(metrics.get("avg_correlation"))},
                {"label": "Top Position", "value": _pct(metrics.get("top_weight"))},
                {"label": "Concentration (HHI)", "value": _num(metrics.get("concentration_hhi"), 3)},
            ]
        },
        "factorExposures": {
            "title": "Factor Exposures",
            "subtitle": "Systematic risk factors including Crypto alongside Market, Tech, Rates, and Commodity.",
            "factors": [
                {
                    "id": f.get("id"),
                    "label": f.get("label"),
                    "beta": float(f.get("beta", 0.0)),
                    "betaLabel": _num(f.get("beta")),
                    "contribution": float(f.get("contribution", 0.0)),
                    "contributionLabel": _pct(f.get("contribution")),
                    "highlight": f.get("id") == "crypto",
                }
                for f in (
                    metrics.get("factor_exposures", {}).get("factors")
                    or [
                        {
                            "id": "market",
                            "label": "Market",
                            "beta": metrics.get("market_factor", 0.0),
                            "contribution": 0.0,
                        },
                        {
                            "id": "tech",
                            "label": "Tech",
                            "beta": metrics.get("tech_factor", 0.0),
                            "contribution": 0.0,
                        },
                        {
                            "id": "rates",
                            "label": "Rates",
                            "beta": metrics.get("rates_factor", 0.0),
                            "contribution": 0.0,
                        },
                        {
                            "id": "crypto",
                            "label": "Crypto",
                            "beta": metrics.get("crypto_factor", 0.0),
                            "contribution": metrics.get("crypto_factor_contribution", 0.0),
                        },
                        {
                            "id": "commodity",
                            "label": "Commodity",
                            "beta": metrics.get("commodity_factor", 0.0),
                            "contribution": 0.0,
                        },
                    ]
                )
            ],
        },
        "volatilityTrends": {
            "regime": VOL_REGIME_LABELS.get(str(vol.get("vol_regime", "normal")), "Normal"),
            "ewma": float(vol.get("ewma_vol", 0.0)),
            "forecast": float(vol.get("blended_vol", 0.0)),
            "ewmaLabel": _pct(vol.get("ewma_vol")),
            "forecastLabel": _pct(vol.get("blended_vol")),
            "series": _downsample(vol_dates, vol_values),
        },
        "marketSignalInsights": signals,
        "exposureBreakdown": {
            "byAssetClass": [
                {"label": "Equities & ETFs", "value": exposure["equityEtfs"]},
                {"label": "Crypto Assets", "value": exposure["crypto"]},
                {"label": "Cash", "value": exposure["cash"]},
                {"label": "Other", "value": exposure["other"]},
            ],
            "holdings": holdings,
        },
        "hedgeRecommendations": recommendations,
        "scenarioSimulation": {
            "label": SCENARIO_LABELS.get(scenario, scenario),
            "description": SCENARIOS.get(scenario).description if scenario in SCENARIOS else "",
            "wealthSeries": _downsample(wealth_dates, wealth_values),
            "endingWealth": float(series.get("wealth_end", 1.0)),
        },
        "disclaimer": (
            "Market insights may use free public quotes when available, "
            "otherwise a simulated tape. Not investment advice."
        ),
    }
    market = raw.get("marketInsights")
    if market:
        payload["marketInsights"] = market
    return payload
