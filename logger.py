from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base import AgentOutput


class ActionLogger:
    """
    Logs every AgentOutput to an in-memory list and to a JSONL file.
    """

    def __init__(self, output_dir: str) -> None:
        self._log: list[dict] = []
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._jsonl_path = os.path.join(output_dir, "actions.jsonl")

    def log(self, output: "AgentOutput") -> None:
        record = output.to_dict()
        self._log.append(record)
        with open(self._jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def get_recent(self, n: int) -> list[dict]:
        return self._log[-n:] if n > 0 else []

    @property
    def all_actions(self) -> list[dict]:
        return list(self._log)
