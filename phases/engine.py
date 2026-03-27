from __future__ import annotations
from typing import Iterator
from phases.definitions import PhaseConfig, DEFAULT_PHASES


class PhaseEngine:
    """Holds the ordered phase sequence for a round and iterates over it."""

    def __init__(self, phases: list[PhaseConfig] | None = None) -> None:
        self._phases = phases if phases is not None else list(DEFAULT_PHASES)

    def __iter__(self) -> Iterator[PhaseConfig]:
        return iter(self._phases)
