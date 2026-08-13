"""FastAPI application for the AutoHedge product dashboard."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from autohedge.agents.orchestrator import AgentOrchestrator
from autohedge.config import ROOT, load_config, load_portfolio
from autohedge.market import build_market_insights
from autohedge.presentation import present_analysis
from autohedge.simulation.market_simulator import SCENARIOS
from autohedge.utils.logging import setup_logging

STATIC_DIR = ROOT / "web" / "dist"


def _portfolio_catalog() -> list[dict[str, Any]]:
    portfolios_dir = ROOT / "configs" / "portfolios"
    items = []
    for path in sorted(portfolios_dir.glob("*.yaml")):
        pf = load_portfolio(path)
        items.append(
            {
                "id": path.stem,
                "name": pf.get("name"),
                "description": pf.get("description", ""),
                "version": str(pf.get("version", "1.0")),
                "holdingCount": len(pf.get("holdings", [])),
                "hasCrypto": any(
                    h.get("asset_class") == "crypto" or h.get("sector") == "crypto"
                    for h in pf.get("holdings", [])
                ),
            }
        )
    return items


class AnalyzeRequest(BaseModel):
    portfolioId: str = Field(default="balanced")
    scenario: str = Field(default="baseline")
    seed: int | None = Field(default=None)
    includeMarket: bool = Field(default=True)


def create_app() -> FastAPI:
    config = load_config()
    setup_logging(config.get("logging", {}).get("level", "INFO"))
    orch = AgentOrchestrator(config)
    orch.maybe_load_models()
    prefer_live = bool(config.get("market", {}).get("prefer_live", True))

    app = FastAPI(title="AutoHedge", version="1.0.0", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/portfolios")
    def list_portfolios() -> dict[str, Any]:
        return {"portfolios": _portfolio_catalog()}

    @app.get("/api/scenarios")
    def list_scenarios() -> dict[str, Any]:
        return {
            "scenarios": [
                {
                    "id": s.name,
                    "label": s.label,
                    "description": s.description,
                }
                for s in SCENARIOS.values()
            ]
        }

    @app.get("/api/market")
    def market_insights(
        scenario: str = Query(default="baseline"),
        live: bool | None = Query(default=None),
    ) -> dict[str, Any]:
        """Whole-market pulse + tips across equities, rates, commodities, crypto, etc."""
        use_live = prefer_live if live is None else live
        if scenario not in SCENARIOS:
            scenario = "baseline"
        return build_market_insights(prefer_live=use_live, scenario=scenario)

    @app.post("/api/analyze")
    def analyze(body: AnalyzeRequest) -> dict[str, Any]:
        portfolio_path = ROOT / "configs" / "portfolios" / f"{body.portfolioId}.yaml"
        if not portfolio_path.exists():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if body.scenario not in SCENARIOS:
            raise HTTPException(status_code=400, detail="Unknown scenario")

        portfolio = load_portfolio(portfolio_path)
        raw = orch.run(portfolio, scenario=body.scenario, seed=body.seed)

        if body.includeMarket:
            raw["marketInsights"] = build_market_insights(
                prefer_live=prefer_live,
                scenario=body.scenario,
                portfolio=portfolio,
                factor_exposures=raw.get("metrics", {}).get("factor_exposures"),
            )

        return present_analysis(
            raw,
            portfolio_id=body.portfolioId,
            portfolio_version=str(portfolio.get("version", "1.0")),
        )

    if STATIC_DIR.exists():
        assets = STATIC_DIR / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(STATIC_DIR / "index.html")

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str) -> FileResponse:
            candidate = STATIC_DIR / full_path
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404)
            if candidate.exists() and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
