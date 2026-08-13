"""Command-line interface for AutoHedge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from autohedge.agents.orchestrator import AgentOrchestrator
from autohedge.aws import maybe_upload
from autohedge.config import ROOT, load_config, load_portfolio
from autohedge.explainability import render_markdown_report
from autohedge.utils.io import ensure_dir, write_json
from autohedge.utils.logging import setup_logging


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="autohedge",
        description="AutoHedge — AI-powered portfolio risk analysis assistant",
    )
    sub = p.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("analyze", help="Run simulation + agent hedge workflow")
    run_p.add_argument(
        "--portfolio",
        default=str(ROOT / "configs" / "portfolios" / "growth_tech.yaml"),
        help="Path to portfolio YAML",
    )
    run_p.add_argument(
        "--config",
        default=str(ROOT / "configs" / "default.yaml"),
        help="Path to config YAML",
    )
    run_p.add_argument(
        "--scenario",
        default="baseline",
        choices=["baseline", "risk_off", "tech_drawdown", "inflation_spike", "crypto_stress"],
        help="Market simulation scenario",
    )
    run_p.add_argument("--seed", type=int, default=None, help="Override simulation seed")
    run_p.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (default: configs output.dir)",
    )

    train_p = sub.add_parser("train", help="Train ML models on synthetic portfolios")
    train_p.add_argument(
        "--config",
        default=str(ROOT / "configs" / "default.yaml"),
    )

    list_p = sub.add_parser("list-portfolios", help="List bundled sample portfolios")
    list_p.add_argument(
        "--config",
        default=str(ROOT / "configs" / "default.yaml"),
    )

    serve_p = sub.add_parser("serve", help="Launch the AutoHedge web dashboard")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)
    return p


def cmd_analyze(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    log_cfg = config.get("logging", {})
    logger = setup_logging(log_cfg.get("level", "INFO"), log_cfg.get("file"))
    portfolio = load_portfolio(args.portfolio)

    orch = AgentOrchestrator(config)
    orch.maybe_load_models()
    result = orch.run(portfolio, scenario=args.scenario, seed=args.seed)

    out_root = Path(args.out_dir) if args.out_dir else Path(config["_root"]) / config.get(
        "output", {}
    ).get("dir", "outputs")
    run_name = f"{portfolio.get('name', 'portfolio').lower().replace(' ', '_')}_{args.scenario}"
    out_dir = ensure_dir(out_root / run_name)
    json_path = write_json(out_dir / "analysis.json", result)
    from autohedge.presentation import present_analysis

    portfolio_id = Path(args.portfolio).stem
    dashboard = present_analysis(
        result,
        portfolio_id=portfolio_id,
        portfolio_version=str(portfolio.get("version", "1.0")),
    )
    dash_path = write_json(out_dir / "dashboard.json", dashboard)
    md = render_markdown_report(result)
    md_path = out_dir / "report.md"
    md_path.write_text(md, encoding="utf-8")

    uploaded = maybe_upload(config, out_dir)
    logger.info("Wrote %s", json_path)
    logger.info("Wrote %s", dash_path)
    logger.info("Wrote %s", md_path)
    if uploaded:
        logger.info("Uploaded %d object(s) to S3", len(uploaded))
    try:
        print(md)
    except UnicodeEncodeError:
        print(md.encode("ascii", errors="replace").decode("ascii"))
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    from autohedge.ml.risk_scorer import RiskScorer
    from autohedge.ml.volatility_model import VolatilityAnalyzer
    from autohedge.simulation.portfolio_sim import portfolio_return_series, simulate_portfolio_market

    config = load_config(args.config)
    logger = setup_logging(config.get("logging", {}).get("level", "INFO"))
    portfolios_dir = Path(config["_root"]) / "configs" / "portfolios"
    portfolios = [load_portfolio(p) for p in sorted(portfolios_dir.glob("*.yaml"))]

    scorer = RiskScorer(
        n_estimators=int(config.get("ml", {}).get("n_estimators", 100)),
        random_state=int(config.get("ml", {}).get("random_state", 42)),
    )
    stats = scorer.fit_synthetic(portfolios)
    model_dir = ensure_dir(Path(config["_root"]) / config.get("ml", {}).get("model_dir", "models"))
    scorer.save(model_dir / "risk_scorer.joblib")

    # Fit vol model on balanced portfolio baseline path.
    _, returns = simulate_portfolio_market(portfolios[0], seed=int(config.get("simulation", {}).get("seed", 42)))
    vol = VolatilityAnalyzer()
    vol.fit(portfolio_return_series(portfolios[0], returns))
    vol.save(model_dir / "volatility_analyzer.joblib")

    logger.info("Training complete: %s", stats)
    print(f"Saved models to {model_dir}")
    print(stats)
    return 0


def cmd_list_portfolios(_: argparse.Namespace) -> int:
    portfolios_dir = ROOT / "configs" / "portfolios"
    for path in sorted(portfolios_dir.glob("*.yaml")):
        pf = load_portfolio(path)
        print(f"- {path.name}: {pf.get('name')} ({len(pf.get('holdings', []))} holdings)")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "Missing web dependencies. Run: pip install 'fastapi' 'uvicorn[standard]'"
        ) from exc
    from autohedge.api.app import app

    print(f"AutoHedge dashboard: http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return cmd_analyze(args)
    if args.command == "train":
        return cmd_train(args)
    if args.command == "list-portfolios":
        return cmd_list_portfolios(args)
    if args.command == "serve":
        return cmd_serve(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
