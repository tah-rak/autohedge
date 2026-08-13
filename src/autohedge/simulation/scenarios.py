"""Named stress scenarios for demos and regression tests."""

from __future__ import annotations

from autohedge.simulation.market_simulator import SCENARIOS


def list_scenarios() -> list[dict]:
    return [
        {"name": s.name, "label": s.label, "description": s.description}
        for s in SCENARIOS.values()
    ]
