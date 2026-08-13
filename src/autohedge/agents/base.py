"""Shared agent primitives for transparent reasoning traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentMessage:
    agent: str
    role: str
    content: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Recommendation:
    action: str
    instrument: str
    rationale: str
    trigger_signals: list[str]
    expected_effect: str
    confidence: float
    priority: int
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "instrument": self.instrument,
            "rationale": self.rationale,
            "trigger_signals": self.trigger_signals,
            "expected_effect": self.expected_effect,
            "confidence": self.confidence,
            "priority": self.priority,
            "details": self.details,
        }


class BaseAgent:
    name = "base"

    def run(self, context: dict[str, Any]) -> AgentMessage:
        raise NotImplementedError
