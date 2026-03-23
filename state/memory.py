from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from state.settlement import SettlementState
    from logger import ActionLogger


class MemoryContext:
    """Builds the context dict passed to each agent's prompt."""

    @staticmethod
    def build(
        state: "SettlementState",
        logger: "ActionLogger",
        n: int,
        faction_name: str | None = None,
    ) -> dict:
        """
        Returns a dict with:
          state_summary       – compact text summary of current settlement
          culture_summary     – current culture levels and chosen options
          faction_summary     – all factions, their tokens and VP
          own_tokens          – token dict for the requesting faction (if given)
          recent_actions      – list of last n action dicts
        """
        recent = logger.get_recent(n)

        own_tokens = None
        if faction_name:
            try:
                f = state.get_faction(faction_name)
                own_tokens = f["tokens"]
            except KeyError:
                pass

        return {
            "state_summary": state.summary(),
            "culture_summary": state.culture_summary(),
            "faction_summary": state.faction_summary(),
            "own_tokens": own_tokens,
            "recent_actions": [
                {
                    "era": a["round"],   # stored as "round" in AgentOutput for compatibility
                    "phase": a["phase"],
                    "agent": a["agent_role"],
                    "content": a["content"],
                }
                for a in recent
            ],
        }
