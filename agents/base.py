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

    def _call_llm(self, prompt: str, round_num: int, phase: str, max_tokens: int = 1024) -> AgentOutput:
        import anthropic
        import config
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=config.MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        return AgentOutput(
            agent_role=self.role,
            phase=phase,
            round=round_num,
            content=raw,
        )
