"""Unit tests for risk metrics, crypto, presentation, and agents."""

from __future__ import annotations

from autohedge.agents.orchestrator import AgentOrchestrator
from autohedge.config import load_config, load_portfolio
from autohedge.ml.features import build_feature_vector, features_to_array
from autohedge.ml.risk_scorer import RiskScorer
from autohedge.presentation import present_analysis
from autohedge.risk.metrics import compute_risk_metrics, detect_risk_signals
from autohedge.simulation.portfolio_sim import simulate_portfolio_market


def test_portfolio_weights_and_simulation():
    cfg = load_config()
    portfolio = load_portfolio(f"{cfg['_root']}/configs/portfolios/balanced.yaml")
    prices, returns = simulate_portfolio_market(portfolio, trading_days=120, seed=1)
    assert len(prices) == 120
    assert returns.shape[0] == 119
    assert "BTC" in prices.columns
    metrics = compute_risk_metrics(portfolio, returns)
    assert metrics["annualized_volatility"] >= 0
    assert 0 <= metrics["max_drawdown"] <= 1
    assert metrics["engine"] == "python"


def test_crypto_factor_is_first_class():
    cfg = load_config()
    portfolio = load_portfolio(f"{cfg['_root']}/configs/portfolios/crypto_growth.yaml")
    _, returns = simulate_portfolio_market(
        portfolio, trading_days=100, seed=3, scenario="crypto_stress"
    )
    metrics = compute_risk_metrics(portfolio, returns)
    assert "crypto_factor" in metrics
    assert "factor_exposures" in metrics
    factor_ids = {f["id"] for f in metrics["factor_exposures"]["factors"]}
    assert factor_ids == {"market", "tech", "rates", "crypto", "commodity"}
    signals = detect_risk_signals(metrics, portfolio, cfg["risk"])
    codes = {s["code"] for s in signals}
    assert "CRYPTO_FACTOR" in codes or "CRYPTO_HEAVY" in codes


def test_risk_signals_detect_concentration():
    portfolio = {
        "name": "Concentrated",
        "cash_weight": 0.0,
        "holdings": [
            {"symbol": "NVDA", "asset_class": "equity", "sector": "technology", "weight": 0.6},
            {"symbol": "AAPL", "asset_class": "equity", "sector": "technology", "weight": 0.4},
        ],
    }
    metrics = {
        "annualized_volatility": 0.35,
        "var_95": 0.03,
        "cvar_95": 0.04,
        "max_drawdown": 0.2,
        "sharpe_proxy": 0.1,
        "concentration_hhi": 0.52,
        "top_weight": 0.6,
        "avg_correlation": 0.8,
        "equity_exposure": 1.0,
        "beta_proxy": 1.5,
        "crypto_factor": 0.1,
        "crypto_factor_contribution": 0.05,
    }
    signals = detect_risk_signals(
        metrics,
        portfolio,
        {
            "volatility_alert": 0.25,
            "max_drawdown_alert": 0.12,
            "concentration_alert": 0.35,
            "correlation_alert": 0.75,
            "beta_alert": 1.3,
        },
    )
    codes = {s["code"] for s in signals}
    assert "HIGH_VOLATILITY" in codes
    assert "CONCENTRATION" in codes
    assert "SECTOR_CONCENTRATION" in codes


def test_feature_vector_shape():
    cfg = load_config()
    portfolio = load_portfolio(f"{cfg['_root']}/configs/portfolios/defensive.yaml")
    _, returns = simulate_portfolio_market(portfolio, trading_days=80, seed=2)
    metrics = compute_risk_metrics(portfolio, returns)
    feats = build_feature_vector(portfolio, returns, metrics)
    arr = features_to_array(feats)
    assert arr.shape == (17,)
    assert "crypto_factor" in feats


def test_risk_scorer_rule_labels():
    metrics = {
        "annualized_volatility": 0.1,
        "max_drawdown": 0.02,
        "avg_correlation": 0.2,
        "beta_proxy": 0.8,
        "concentration_hhi": 0.05,
    }
    assert RiskScorer.label_from_metrics(metrics) == "low"


def test_orchestrator_and_presentation_are_product_facing():
    cfg = load_config()
    cfg["ml"]["retrain_on_run"] = False
    portfolio = load_portfolio(f"{cfg['_root']}/configs/portfolios/crypto_growth.yaml")
    orch = AgentOrchestrator(cfg)
    result = orch.run(portfolio, scenario="crypto_stress", seed=7)
    assert result["recommendations"]
    assert "engine" not in result["metrics"]
    assert "method" not in result["risk_score"]

    from autohedge.market import build_market_insights

    result["marketInsights"] = build_market_insights(
        prefer_live=False,
        seed=7,
        scenario="baseline",
        portfolio=portfolio,
        factor_exposures=result["metrics"].get("factor_exposures"),
    )
    dashboard = present_analysis(result, portfolio_id="crypto_growth", portfolio_version="1.0")
    blob = str(dashboard).lower()
    assert "ocaml" not in blob
    assert "backend connected" not in blob
    assert dashboard["title"] == "Portfolio Risk Analysis"
    assert dashboard["hedgeRecommendations"]
    assert dashboard["exposureBreakdown"]["holdings"]
    assert dashboard["factorExposures"]["factors"]
    labels = {f["label"] for f in dashboard["factorExposures"]["factors"]}
    assert "Crypto" in labels
    assert "Market" in labels
    assert dashboard["marketInsights"]["sleeves"]
    sleeve_labels = {s["label"] for s in dashboard["marketInsights"]["sleeves"]}
    assert "US Equities" in sleeve_labels
    assert "Crypto" in sleeve_labels
    assert dashboard["marketInsights"]["suggestions"]


def test_whole_market_insights_cover_more_than_crypto():
    from autohedge.market import build_market_insights

    insights = build_market_insights(prefer_live=False, seed=11, scenario="risk_off")
    assert insights["regime"]
    assert len(insights["sleeves"]) >= 8
    cats = {s["category"] for s in insights["sleeves"]}
    assert "Equities" in cats
    assert "Fixed Income" in cats
    assert "Crypto" in cats
    assert insights["tips"]
    tip_cats = {t["category"] for t in insights["tips"]}
    assert "Market" in tip_cats or "Equities" in tip_cats or "Rates" in tip_cats
