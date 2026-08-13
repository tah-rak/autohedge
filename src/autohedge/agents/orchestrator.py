"""Multi-agent orchestrator for AutoHedge reasoning workflows."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np

from autohedge.agents.explainer import ExplainerAgent
from autohedge.agents.hedge_strategist import HedgeStrategistAgent
from autohedge.agents.market_sensor import MarketSensorAgent
from autohedge.agents.risk_analyst import RiskAnalystAgent
from autohedge.ml.risk_scorer import RiskScorer
from autohedge.ml.volatility_model import VolatilityAnalyzer, analyze_portfolio_volatility
from autohedge.risk.metrics import detect_risk_signals
from autohedge.risk.ocaml_bridge import compute_risk
from autohedge.simulation.portfolio_sim import (
    holding_table,
    portfolio_return_series,
    simulate_portfolio_market,
    wealth_curve,
)

logger = logging.getLogger("autohedge.agents")


class AgentOrchestrator:
    """
    Agent workflow:
      1) MarketSensorAgent
      2) RiskAnalystAgent
      3) HedgeStrategistAgent
      4) ExplainerAgent
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.market_sensor = MarketSensorAgent()
        self.risk_analyst = RiskAnalystAgent()
        self.hedge_strategist = HedgeStrategistAgent()
        self.explainer = ExplainerAgent()
        self.risk_scorer = RiskScorer(
            n_estimators=int(config.get("ml", {}).get("n_estimators", 100)),
            random_state=int(config.get("ml", {}).get("random_state", 42)),
        )
        self.vol_analyzer = VolatilityAnalyzer(
            n_estimators=int(config.get("ml", {}).get("n_estimators", 100)),
            random_state=int(config.get("ml", {}).get("random_state", 42)),
        )

    def maybe_load_models(self) -> None:
        from pathlib import Path

        root = Path(self.config.get("_root", "."))
        model_dir = root / self.config.get("ml", {}).get("model_dir", "models")
        risk_path = model_dir / "risk_scorer.joblib"
        vol_path = model_dir / "volatility_analyzer.joblib"
        if risk_path.exists():
            self.risk_scorer.load(risk_path)
            logger.info("Loaded risk scorer from %s", risk_path)
        if vol_path.exists():
            self.vol_analyzer.load(vol_path)
            logger.info("Loaded volatility model from %s", vol_path)

    def run(
        self,
        portfolio: dict[str, Any],
        *,
        scenario: str = "baseline",
        seed: int | None = None,
    ) -> dict[str, Any]:
        sim_cfg = self.config.get("simulation", {})
        risk_cfg = self.config.get("risk", {})
        agent_cfg = self.config.get("agents", {})
        seed = int(sim_cfg.get("seed", 42) if seed is None else seed)

        logger.info("Simulating market paths scenario=%s seed=%s", scenario, seed)
        prices, returns = simulate_portfolio_market(
            portfolio,
            trading_days=int(sim_cfg.get("trading_days", 252)),
            seed=seed,
            scenario=scenario,
        )

        metrics = compute_risk(portfolio, returns, self.config)
        # Never surface internal engine names in product payloads.
        metrics = {k: v for k, v in metrics.items() if k != "engine"}
        signals = detect_risk_signals(metrics, portfolio, risk_cfg)

        port_rets = portfolio_return_series(portfolio, returns)
        if not self.vol_analyzer.is_fitted:
            self.vol_analyzer.fit(port_rets)
        volatility = analyze_portfolio_volatility(portfolio, returns, self.vol_analyzer)
        # Remove method labels from product-facing volatility block.
        volatility = {
            k: v for k, v in volatility.items() if k not in {"method", "ml_vol"}
        } | {"forecast_vol": volatility.get("blended_vol", volatility.get("ewma_vol", 0.0))}

        if not self.risk_scorer.is_fitted and self.config.get("ml", {}).get("retrain_on_run"):
            logger.info("Retraining risk scorer on synthetic data for this run")
            self.risk_scorer.fit_synthetic([portfolio], seed=seed)

        risk_score = self.risk_scorer.predict(portfolio, returns, metrics)
        risk_score = {
            "risk_label": risk_score.get("risk_label"),
            "risk_score": risk_score.get("risk_score"),
            "features": risk_score.get("features", {}),
        }

        context: dict[str, Any] = {
            "portfolio": portfolio,
            "returns": returns,
            "prices": prices,
            "metrics": metrics,
            "signals": signals,
            "volatility": {
                **volatility,
                "blended_vol": volatility.get("forecast_vol", volatility.get("ewma_vol", 0.0)),
            },
            "risk_score": {**risk_score, "method": "ensemble"},
            "scenario": scenario,
            "min_confidence": agent_cfg.get("min_confidence", 0.55),
            "max_recommendations": agent_cfg.get("max_recommendations", 5),
        }

        transcript = []
        market_msg = self.market_sensor.run(context)
        transcript.append({"agent": market_msg.agent, "role": market_msg.role, "content": market_msg.content})
        context["market_sensor"] = market_msg.data

        risk_msg = self.risk_analyst.run(context)
        transcript.append({"agent": risk_msg.agent, "role": risk_msg.role, "content": risk_msg.content})

        hedge_msg = self.hedge_strategist.run(context)
        transcript.append({"agent": hedge_msg.agent, "role": hedge_msg.role, "content": hedge_msg.content})
        recommendations = hedge_msg.data.get("recommendations", [])
        context["recommendations"] = recommendations

        explain_msg = self.explainer.run(context)
        transcript.append(
            {"agent": explain_msg.agent, "role": explain_msg.role, "content": explain_msg.content}
        )

        wealth = wealth_curve(port_rets)
        rolling_vol = port_rets.rolling(21).std() * np.sqrt(252)
        rolling_vol = rolling_vol.dropna()

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "portfolio": {
                "name": portfolio.get("name"),
                "version": portfolio.get("version", "1.0"),
                "cash_weight": portfolio.get("cash_weight", 0.0),
                "holdings": holding_table(portfolio).to_dict(orient="records"),
            },
            "scenario": scenario,
            "seed": seed,
            "metrics": metrics,
            "signals": signals,
            "volatility": context["volatility"],
            "risk_score": risk_score,
            "recommendations": recommendations,
            "explanations": explain_msg.data.get("explanations", []),
            "agent_transcript": transcript,
            "series": {
                "portfolio_returns_tail": port_rets.tail(10).round(6).tolist(),
                "wealth_start": float(wealth.iloc[0]),
                "wealth_end": float(wealth.iloc[-1]),
                "total_return": float(wealth.iloc[-1] / wealth.iloc[0] - 1.0),
                "wealth_dates": [d.strftime("%Y-%m-%d") for d in wealth.index],
                "wealth_values": [float(x) for x in wealth.values],
                "rolling_vol_dates": [d.strftime("%Y-%m-%d") for d in rolling_vol.index],
                "rolling_vol_values": [float(x) for x in rolling_vol.values],
            },
        }
