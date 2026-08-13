"""EWMA + sklearn residual model for short-horizon volatility analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from autohedge.simulation.portfolio_sim import portfolio_return_series


class VolatilityAnalyzer:
    """
    Role: estimate near-term portfolio volatility and flag vol regime shifts.

    Uses EWMA as a strong baseline and a gradient-boosting model on lagged
    realized-vol features to capture nonlinear persistence.
    """

    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        self.model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "gbr",
                    GradientBoostingRegressor(
                        n_estimators=n_estimators,
                        max_depth=3,
                        learning_rate=0.05,
                        random_state=random_state,
                    ),
                ),
            ]
        )
        self.is_fitted = False

    @staticmethod
    def _supervised_frame(returns: pd.Series, horizon: int = 5) -> pd.DataFrame:
        realized = returns.rolling(horizon).std() * np.sqrt(252)
        df = pd.DataFrame({"y": realized.shift(-horizon)})
        df["lag1"] = realized.shift(1)
        df["lag2"] = realized.shift(2)
        df["lag5"] = realized.shift(5)
        df["abs_ret"] = returns.abs()
        df["neg_ret"] = returns.clip(upper=0.0)
        return df.dropna()

    def fit(self, returns: pd.Series) -> "VolatilityAnalyzer":
        frame = self._supervised_frame(returns)
        if len(frame) < 40:
            self.is_fitted = False
            return self
        x = frame[["lag1", "lag2", "lag5", "abs_ret", "neg_ret"]]
        y = frame["y"]
        self.model.fit(x, y)
        self.is_fitted = True
        return self

    def ewma_vol(self, returns: pd.Series, lam: float = 0.94) -> float:
        var = 0.0
        for r in returns.values:
            var = lam * var + (1.0 - lam) * float(r) ** 2
        return float(np.sqrt(var * 252.0))

    def predict_vol(self, returns: pd.Series) -> dict[str, Any]:
        ewma = self.ewma_vol(returns)
        ml_vol = ewma
        method = "ewma"
        if self.is_fitted and len(returns) >= 20:
            realized = returns.rolling(5).std() * np.sqrt(252)
            row = pd.DataFrame(
                [
                    {
                        "lag1": float(realized.iloc[-1]),
                        "lag2": float(realized.iloc[-2]) if len(realized) > 1 else float(realized.iloc[-1]),
                        "lag5": float(realized.iloc[-5]) if len(realized) > 4 else float(realized.iloc[-1]),
                        "abs_ret": float(returns.abs().iloc[-1]),
                        "neg_ret": float(min(returns.iloc[-1], 0.0)),
                    }
                ]
            )
            ml_vol = float(self.model.predict(row)[0])
            method = "ewma+gbr"
        blended = 0.5 * ewma + 0.5 * ml_vol
        regime = "elevated" if blended >= 0.25 else "normal" if blended >= 0.15 else "calm"
        return {
            "ewma_vol": ewma,
            "ml_vol": ml_vol,
            "blended_vol": blended,
            "vol_regime": regime,
            "method": method,
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "is_fitted": self.is_fitted}, path)

    def load(self, path: str | Path) -> "VolatilityAnalyzer":
        payload = joblib.load(path)
        self.model = payload["model"]
        self.is_fitted = bool(payload.get("is_fitted", True))
        return self


def analyze_portfolio_volatility(
    portfolio: dict[str, Any],
    returns: pd.DataFrame,
    analyzer: VolatilityAnalyzer | None = None,
) -> dict[str, Any]:
    port = portfolio_return_series(portfolio, returns)
    analyzer = analyzer or VolatilityAnalyzer()
    if not analyzer.is_fitted:
        analyzer.fit(port)
    return analyzer.predict_vol(port)
