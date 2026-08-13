"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg_path = Path(path) if path else ROOT / "configs" / "default.yaml"
    cfg = load_yaml(cfg_path)
    cfg["_config_path"] = str(cfg_path)
    cfg["_root"] = str(ROOT)
    return cfg


def load_portfolio(path: str | Path) -> dict[str, Any]:
    data = load_yaml(path)
    required = ("name", "holdings")
    for key in required:
        if key not in data:
            raise ValueError(f"Portfolio file missing '{key}': {path}")
    data.setdefault("currency", "USD")
    data.setdefault("cash_weight", 0.0)
    return data


def resolve_path(root: str | Path, maybe_relative: str | Path) -> Path:
    p = Path(maybe_relative)
    if p.is_absolute():
        return p
    return Path(root) / p
