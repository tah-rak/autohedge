"""Supervised risk scoring model (Random Forest / Gradient Boosting)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from autohedge.ml.features import build_feature_vector, features_to_array
from autohedge.risk.metrics import compute_risk_metrics
from autohedge.simulation.market_simulator import SCENARIOS
from autohedge.simulation.portfolio_sim import simulate_portfolio_market


RISK_LABELS = ["low", "moderate", "high", "severe"]


class RiskScorer:
    """
    Role: map portfolio/market features to an ordinal risk score label.

    Trained on simulated portfolios across scenarios so the project never depends
    on paid market-data APIs. Labels are derived from transparent metric rules.
    """

    def __init__(self, n_estimators: int = 120, random_state: int = 42):
        self.model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "rf",
                    RandomForestClassifier(
                        n_estimators=n_estimators,
                        max_depth=6,
                        random_state=random_state,
                        class_weight="balanced",
                    ),
                ),
            ]
        )
        self.is_fitted = False

    @staticmethod
    def label_from_metrics(metrics: dict[str, Any]) -> str:
        score = 0
        if metrics["annualized_volatility"] >= 0.30:
            score += 2
        elif metrics["annualized_volatility"] >= 0.22:
            score += 1
        if metrics["max_drawdown"] >= 0.18:
            score += 2
        elif metrics["max_drawdown"] >= 0.10:
            score += 1
        if metrics["avg_correlation"] >= 0.75:
            score += 1
        if metrics["beta_proxy"] >= 1.3:
            score += 1
        if metrics["concentration_hhi"] >= 0.18:
            score += 1
        if abs(float(metrics.get("crypto_factor", 0.0))) >= 0.45:
            score += 2
        elif abs(float(metrics.get("crypto_factor", 0.0))) >= 0.30:
            score += 1
        if score >= 5:
            return "severe"
        if score >= 3:
            return "high"
        if score >= 1:
            return "moderate"
        return "low"

    def fit_synthetic(
        self,
        base_portfolios: list[dict[str, Any]],
        seed: int = 42,
    ) -> dict[str, Any]:
        xs: list[np.ndarray] = []
        ys: list[str] = []
        rng = np.random.default_rng(seed)
        for i, portfolio in enumerate(base_portfolios):
            for scenario in SCENARIOS:
                for _ in range(3):
                    local_seed = int(rng.integers(0, 10_000_000)) + i
                    _, returns = simulate_portfolio_market(
                        portfolio,
                        trading_days=252,
                        seed=local_seed,
                        scenario=scenario,
                    )
                    metrics = compute_risk_metrics(portfolio, returns)
                    feats = build_feature_vector(portfolio, returns, metrics)
                    xs.append(features_to_array(feats))
                    ys.append(self.label_from_metrics(metrics))
        x = np.vstack(xs)
        self.model.fit(x, ys)
        self.is_fitted = True
        acc = float(self.model.score(x, ys))
        return {"train_samples": len(ys), "train_accuracy": acc, "labels": sorted(set(ys))}

    def predict(
        self,
        portfolio: dict[str, Any],
        returns: Any,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        feats = build_feature_vector(portfolio, returns, metrics)
        x = features_to_array(feats).reshape(1, -1)
        rule_label = self.label_from_metrics(metrics)
        if not self.is_fitted:
            return {
                "risk_label": rule_label,
                "risk_score": RISK_LABELS.index(rule_label) / (len(RISK_LABELS) - 1),
                "proba": {},
                "features": feats,
                "method": "rule_based",
            }
        proba = self.model.predict_proba(x)[0]
        classes = list(self.model.named_steps["rf"].classes_)
        proba_map = {str(c): float(p) for c, p in zip(classes, proba)}
        pred = str(self.model.predict(x)[0])
        # Blend model + transparent rules for robustness.
        if RISK_LABELS.index(rule_label) > RISK_LABELS.index(pred):
            pred = rule_label
        score = RISK_LABELS.index(pred) / (len(RISK_LABELS) - 1)
        return {
            "risk_label": pred,
            "risk_score": score,
            "proba": proba_map,
            "features": feats,
            "method": "random_forest+rules",
            "rule_label": rule_label,
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "is_fitted": self.is_fitted}, path)

    def load(self, path: str | Path) -> "RiskScorer":
        payload = joblib.load(path)
        self.model = payload["model"]
        self.is_fitted = bool(payload.get("is_fitted", True))
        return self
