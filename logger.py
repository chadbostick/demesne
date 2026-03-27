from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base import AgentOutput


class ActionLogger:
    """
    Logs every AgentOutput and structured game events to disk.
    - actions.jsonl: LLM agent outputs (narrative)
    - events.jsonl: structured mechanical events (auditable game history)
    """

    def __init__(self, output_dir: str) -> None:
        self._log: list[dict] = []
        self._events: list[dict] = []
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._jsonl_path = os.path.join(output_dir, "actions.jsonl")
        self._events_path = os.path.join(output_dir, "events.jsonl")

    def log(self, output: "AgentOutput") -> None:
        record = output.to_dict()
        self._log.append(record)
        with open(self._jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def log_event(self, event_type: str, era: int, **data) -> None:
        """Log a structured game event with arbitrary data."""
        event = {
            "event_type": event_type,
            "era": era,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        self._events.append(event)
        with open(self._events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def get_recent(self, n: int) -> list[dict]:
        return self._log[-n:] if n > 0 else []

    @property
    def all_actions(self) -> list[dict]:
        return list(self._log)

    @property
    def all_events(self) -> list[dict]:
        return list(self._events)

    def events_for_era(self, era: int) -> list[dict]:
        return [e for e in self._events if e["era"] == era]
