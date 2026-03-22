from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base import BaseAgent


class AgentRegistry:
    """Maps role names to agent instances."""

    def __init__(self) -> None:
        self._agents: dict[str, "BaseAgent"] = {}

    def register(self, agent: "BaseAgent") -> None:
        self._agents[agent.role] = agent

    def get(self, role: str) -> "BaseAgent":
        if role not in self._agents:
            raise KeyError(f"No agent registered for role '{role}'")
        return self._agents[role]

    def all_roles(self) -> list[str]:
        return list(self._agents.keys())
