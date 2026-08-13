#!/usr/bin/env python
"""Generate sample outputs for the repository."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autohedge.cli import main


def run() -> None:
    samples = ROOT / "outputs" / "samples"
    portfolios = [
        ("growth_tech.yaml", "tech_drawdown"),
        ("balanced.yaml", "risk_off"),
        ("defensive.yaml", "inflation_spike"),
        ("crypto_growth.yaml", "crypto_stress"),
    ]
    for pf, scenario in portfolios:
        code = main(
            [
                "analyze",
                "--portfolio",
                str(ROOT / "configs" / "portfolios" / pf),
                "--scenario",
                scenario,
                "--seed",
                "42",
                "--out-dir",
                str(samples),
            ]
        )
        if code != 0:
            raise SystemExit(code)
    print(f"Sample outputs written to {samples}")


if __name__ == "__main__":
    run()
