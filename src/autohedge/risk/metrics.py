"""Python risk metrics engine (primary fallback; mirrors OCaml engine)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from autohedge.simulation.portfolio_sim import portfolio_return_series, wealth_curve


def _max_drawdown(wealth: pd.Series) -> float:
    peak = wealth.cummax()
    dd = (peak - wealth) / peak.replace(0, np.nan)
    return float(dd.max()) if len(dd) else 0.0


def _herfindahl(weights: list[float]) -> float:
    return float(sum(w * w for w in weights))


def average_pairwise_correlation(returns: pd.DataFrame) -> float:
    if returns.shape[1] < 2:
        return 0.0
    corr = returns.corr().values
    n = corr.shape[0]
    vals = [corr[i, j] for i in range(n) for j in range(i + 1, n)]
    return float(np.nanmean(vals)) if vals else 0.0


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    q = np.quantile(returns.values, 1.0 - confidence)
    return float(-q)


def historical_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    threshold = np.quantile(returns.values, 1.0 - confidence)
    tail = returns[returns <= threshold]
    if tail.empty:
        return historical_var(returns, confidence)
    return float(-tail.mean())


def compute_risk_metrics(
    portfolio: dict[str, Any],
    returns: pd.DataFrame,
    *,
    annualization: float = 252.0,
    confidence: float = 0.95,
    risk_free: float = 0.02,
) -> dict[str, float | str]:
    port = portfolio_return_series(portfolio, returns)
    wealth = wealth_curve(port)
    weights = [float(h["weight"]) for h in portfolio["holdings"]]
    equity_like = sum(
        float(h["weight"])
        for h in portfolio["holdings"]
        if h.get("asset_class") in {"equity", "etf"}
    )
    bench = returns["SPY"] if "SPY" in returns.columns else port
    cov = np.cov(port.values, bench.values)[0, 1] if len(port) > 1 else 0.0
    var_b = float(np.var(bench.values, ddof=1)) if len(bench) > 1 else 1.0
    beta = float(cov / var_b) if var_b > 1e-18 else 1.0
    vol = float(port.std(ddof=1) * np.sqrt(annualization))
    mu_ann = float(port.mean() * annualization)
    sharpe = (mu_ann - risk_free) / vol if vol > 1e-12 else 0.0

    held = [h["symbol"] for h in portfolio["holdings"] if h["symbol"] in returns.columns]
    avg_corr = average_pairwise_correlation(returns[held]) if held else 0.0

    from autohedge.risk.factors import compute_factor_exposures

    factors = compute_factor_exposures(portfolio, returns)

    return {
        "annualized_volatility": vol,
        "var_95": historical_var(port, confidence),
        "cvar_95": historical_cvar(port, confidence),
        "max_drawdown": _max_drawdown(wealth),
        "sharpe_proxy": float(sharpe),
        "concentration_hhi": _herfindahl(weights),
        "top_weight": float(max(weights) if weights else 0.0),
        "avg_correlation": avg_corr,
        "equity_exposure": float(equity_like),
        "beta_proxy": beta,
        "crypto_factor": float(factors["crypto_factor"]),
        "market_factor": float(factors["market_factor"]),
        "tech_factor": float(factors["tech_factor"]),
        "rates_factor": float(factors["rates_factor"]),
        "commodity_factor": float(factors["commodity_factor"]),
        "crypto_factor_contribution": float(factors["contribution"]["crypto"]),
        "factor_exposures": factors,
        "engine": "python",
    }


def detect_risk_signals(
    metrics: dict[str, Any],
    portfolio: dict[str, Any],
    thresholds: dict[str, Any],
) -> list[dict[str, Any]]:
    """Map quantitative metrics to human-readable risk signals."""
    signals: list[dict[str, Any]] = []

    def add(code: str, severity: str, message: str, evidence: dict[str, Any]) -> None:
        signals.append(
            {
                "code": code,
                "severity": severity,
                "message": message,
                "evidence": evidence,
            }
        )

    vol = float(metrics["annualized_volatility"])
    if vol >= float(thresholds.get("volatility_alert", 0.25)):
        add(
            "HIGH_VOLATILITY",
            "high",
            f"Annualized volatility {vol:.1%} exceeds alert threshold.",
            {"annualized_volatility": vol, "threshold": thresholds.get("volatility_alert")},
        )

    mdd = float(metrics["max_drawdown"])
    if mdd >= float(thresholds.get("max_drawdown_alert", 0.12)):
        add(
            "DEEP_DRAWDOWN",
            "high",
            f"Max drawdown {mdd:.1%} indicates material path risk.",
            {"max_drawdown": mdd, "threshold": thresholds.get("max_drawdown_alert")},
        )

    top_w = float(metrics["top_weight"])
    if top_w >= float(thresholds.get("concentration_alert", 0.35)):
        add(
            "CONCENTRATION",
            "medium",
            f"Largest position weight {top_w:.1%} is highly concentrated.",
            {"top_weight": top_w},
        )

    corr = float(metrics["avg_correlation"])
    if corr >= float(thresholds.get("correlation_alert", 0.75)):
        add(
            "CORRELATION_SPIKE",
            "medium",
            f"Average pairwise correlation {corr:.2f} reduces diversification.",
            {"avg_correlation": corr},
        )

    beta = float(metrics["beta_proxy"])
    if beta >= float(thresholds.get("beta_alert", 1.30)):
        add(
            "HIGH_BETA",
            "medium",
            f"Portfolio beta proxy {beta:.2f} amplifies market moves.",
            {"beta_proxy": beta},
        )

    equity = float(metrics["equity_exposure"])
    if equity >= 0.80:
        add(
            "EQUITY_HEAVY",
            "medium",
            f"Equity/ETF exposure {equity:.1%} leaves limited defensive ballast.",
            {"equity_exposure": equity},
        )

    crypto = sum(
        float(h["weight"])
        for h in portfolio["holdings"]
        if h.get("asset_class") == "crypto" or h.get("sector") == "crypto"
    )
    if crypto >= 0.20:
        add(
            "CRYPTO_HEAVY",
            "high" if crypto >= 0.35 else "medium",
            f"Crypto sleeve weight {crypto:.1%} increases allocation concentration in digital assets.",
            {"crypto_exposure": crypto},
        )

    # Systematic Crypto factor (beta/contribution), distinct from sleeve weight.
    from autohedge.risk.factors import detect_factor_signals

    for sig in detect_factor_signals(
        metrics.get("factor_exposures")
        or {
            "crypto_factor": metrics.get("crypto_factor", 0.0),
            "tech_factor": metrics.get("tech_factor", 0.0),
            "rates_factor": metrics.get("rates_factor", 0.0),
            "contribution": {
                "crypto": metrics.get("crypto_factor_contribution", 0.0),
            },
        },
        crypto_beta_alert=float(thresholds.get("crypto_factor_alert", 0.35)),
        crypto_contrib_alert=float(thresholds.get("crypto_factor_contrib_alert", 0.22)),
    ):
        add(sig["code"], sig["severity"], sig["message"], sig.get("evidence", {}))

    sectors: dict[str, float] = {}
    for h in portfolio["holdings"]:
        sectors[h.get("sector", "unknown")] = sectors.get(h.get("sector", "unknown"), 0.0) + float(
            h["weight"]
        )
    for sector, w in sectors.items():
        if w >= 0.45:
            add(
                "SECTOR_CONCENTRATION",
                "medium",
                f"Sector '{sector}' aggregates to {w:.1%} of portfolio.",
                {"sector": sector, "weight": w},
            )

    if not signals:
        add(
            "STABLE",
            "low",
            "No threshold breaches detected; continue monitoring.",
            {"status": "ok"},
        )
    return signals
