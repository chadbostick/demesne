from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from state.settlement import SettlementState
    from logger import ActionLogger


class MemoryContext:
    """Builds the context dict passed to each agent's prompt."""

    @staticmethod
    def build(state: "SettlementState", logger: "ActionLogger", n: int) -> dict:
        """
        Returns a dict with:
          - state_summary: compact text summary of current settlement
          - recent_actions: list of the last n action dicts (role, phase, content)
        """
        recent = logger.get_recent(n)
        return {
            "state_summary": state.summary(),
            "recent_actions": [
                {
                    "round": a["round"],
                    "phase": a["phase"],
                    "agent": a["agent_role"],
                    "content": a["content"],
                }
                for a in recent
            ],
        }
