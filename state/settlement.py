import json
from copy import deepcopy
from typing import Any


class SettlementState:
    """JSON-backed settlement state. All mutation goes through explicit methods."""

    def __init__(self, name: str = "Unnamed Settlement"):
        self._data: dict = {
            "name": name,
            "round": 0,
            "population": 0,
            "resources": {},
            "factions": [],
            "landmarks": [],
            "current_event": None,
            "notes": [],
        }

    # ── Mutation ──────────────────────────────────────────────────────────────

    def update(self, key: str, value: Any) -> None:
        """Set a top-level field."""
        self._data[key] = value

    def append_to(self, key: str, item: Any) -> None:
        """Append to a list field; creates the list if missing."""
        if key not in self._data:
            self._data[key] = []
        if not isinstance(self._data[key], list):
            raise ValueError(f"Field '{key}' is not a list")
        self._data[key].append(item)

    def apply_patch(self, patch: dict) -> None:
        """
        Apply a state patch dict.  Values under list keys are appended;
        all other values overwrite the existing field.
        """
        for key, value in patch.items():
            if isinstance(value, list) and isinstance(self._data.get(key), list):
                for item in value:
                    self.append_to(key, item)
            else:
                self.update(key, value)

    def increment_round(self) -> None:
        self._data["round"] = self._data.get("round", 0) + 1

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> bool:
        required = {"name", "round", "population", "resources",
                    "factions", "landmarks", "current_event", "notes"}
        return required.issubset(self._data.keys())

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return deepcopy(self._data)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self._data, indent=indent)

    def summary(self) -> str:
        """Compact human-readable summary for use in agent prompts."""
        d = self._data
        lines = [
            f"Settlement: {d['name']} (Round {d['round']})",
            f"Population: {d['population']}",
            f"Resources: {d['resources'] or 'none'}",
            f"Factions: {', '.join(d['factions']) if d['factions'] else 'none'}",
            f"Landmarks: {', '.join(d['landmarks']) if d['landmarks'] else 'none'}",
            f"Current Event: {d['current_event'] or 'none'}",
        ]
        if d["notes"]:
            lines.append(f"Notes: {'; '.join(d['notes'][-3:])}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<SettlementState name={self._data['name']!r} round={self._data['round']}>"
