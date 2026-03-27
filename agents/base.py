from __future__ import annotations
import json
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AgentOutput:
    agent_role: str
    phase: str
    round: int
    content: str
    state_patch: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "agent_role": self.agent_role,
            "phase": self.phase,
            "round": self.round,
            "content": self.content,
            "state_patch": self.state_patch,
            "timestamp": self.timestamp,
        }


class BaseAgent(ABC):
    """
    Abstract base for all creative agents.

    Subclasses must define:
      role              – short identifier (e.g. "gm", "faction_investor")
      constraints       – list of rule strings appended to every prompt
    """

    role: str = "base"
    constraints: list[str] = []
