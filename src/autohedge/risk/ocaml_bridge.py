"""Optional bridge to the OCaml risk CLI."""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from autohedge.risk.metrics import compute_risk_metrics

logger = logging.getLogger("autohedge.risk.ocaml")


def _request_payload(
    portfolio: dict[str, Any],
    returns: pd.DataFrame,
    confidence: float = 0.95,
    annualization: float = 252.0,
) -> dict[str, Any]:
    held = [h["symbol"] for h in portfolio["holdings"] if h["symbol"] in returns.columns]
    returns_by_symbol = {s: returns[s].astype(float).tolist() for s in held}
    benchmark = (
        returns["SPY"].astype(float).tolist()
        if "SPY" in returns.columns
        else returns[held[0]].astype(float).tolist()
    )
    return {
        "portfolio": portfolio,
        "returns_by_symbol": returns_by_symbol,
        "benchmark_returns": benchmark,
        "annualization": annualization,
        "confidence": confidence,
    }


def compute_with_ocaml(
    portfolio: dict[str, Any],
    returns: pd.DataFrame,
    binary: str | Path,
    *,
    confidence: float = 0.95,
    annualization: float = 252.0,
    simulate: bool = False,
) -> dict[str, Any] | None:
    binary = Path(binary)
    if not binary.exists():
        logger.info("OCaml binary not found at %s; using Python risk engine.", binary)
        return None

    payload = _request_payload(portfolio, returns, confidence, annualization)
    with tempfile.TemporaryDirectory() as tmp:
        in_path = Path(tmp) / "request.json"
        out_path = Path(tmp) / "metrics.json"
        in_path.write_text(json.dumps(payload), encoding="utf-8")
        cmd = [str(binary), "--input", str(in_path), "--output", str(out_path)]
        if simulate:
            cmd.append("--simulate")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except OSError as exc:
            logger.warning("Failed to execute OCaml binary: %s", exc)
            return None
        if proc.returncode != 0:
            logger.warning("OCaml risk engine failed: %s", proc.stderr.strip())
            return None
        return json.loads(out_path.read_text(encoding="utf-8"))


def compute_risk(
    portfolio: dict[str, Any],
    returns: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Prefer OCaml when available and configured; otherwise Python."""
    risk_cfg = config.get("risk", {})
    ocaml_cfg = config.get("ocaml", {})
    prefer = bool(ocaml_cfg.get("prefer_ocaml", True))
    binary = ocaml_cfg.get("binary", "ocaml/_build/default/bin/main.exe")
    root = Path(config.get("_root", "."))
    binary_path = Path(binary) if Path(binary).is_absolute() else root / binary

    if prefer:
        metrics = compute_with_ocaml(
            portfolio,
            returns,
            binary_path,
            confidence=float(risk_cfg.get("var_confidence", 0.95)),
            annualization=float(config.get("simulation", {}).get("annualization_factor", 252)),
        )
        if metrics is not None:
            from autohedge.risk.factors import compute_factor_exposures

            factors = compute_factor_exposures(portfolio, returns)
            metrics = {
                **metrics,
                "crypto_factor": float(factors["crypto_factor"]),
                "market_factor": float(factors["market_factor"]),
                "tech_factor": float(factors["tech_factor"]),
                "rates_factor": float(factors["rates_factor"]),
                "commodity_factor": float(factors["commodity_factor"]),
                "crypto_factor_contribution": float(factors["contribution"]["crypto"]),
                "factor_exposures": factors,
            }
            return metrics

    return compute_risk_metrics(
        portfolio,
        returns,
        annualization=float(config.get("simulation", {}).get("annualization_factor", 252)),
        confidence=float(risk_cfg.get("var_confidence", 0.95)),
    )
