from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING

import config
from state.memory import MemoryContext
from riffing.director import RiffingDirector
from agents.base import AgentOutput

if TYPE_CHECKING:
    from state.settlement import SettlementState
    from agents.registry import AgentRegistry
    from phases.engine import PhaseEngine
    from logger import ActionLogger


class Arbiter:
    """
    Deterministic process controller.  No LLM calls — manages phase flow,
    agent dispatch, riffing injection, and state updates.
    """

    def __init__(
        self,
        phase_engine: "PhaseEngine",
        agent_registry: "AgentRegistry",
        logger: "ActionLogger",
        memory_window: int | None = None,
    ) -> None:
        self._phases = phase_engine
        self._agents = agent_registry
        self._logger = logger
        self._memory_window = memory_window or config.MEMORY_WINDOW
        self._riffing = RiffingDirector()

    # ── Public API ────────────────────────────────────────────────────────────

    def run(
        self,
        state: "SettlementState",
        rounds: int,
        output_dir: str,
    ) -> "SettlementState":
        os.makedirs(output_dir, exist_ok=True)

        for round_num in range(1, rounds + 1):
            print(f"\n{'='*60}")
            print(f"  ROUND {round_num}")
            print(f"{'='*60}")

            state.increment_round()
            round_outputs: list[AgentOutput] = []

            for phase in self._phases:
                phase_outputs = self._run_phase(phase, state, round_num)
                round_outputs.extend(phase_outputs)

                # Consequence phase: no agents run, just apply collected patches
                if phase.name == "consequence":
                    self._apply_all_patches(round_outputs, state)

            self._write_round_files(output_dir, round_num, state, round_outputs)

        return state

    # ── Phase execution ───────────────────────────────────────────────────────

    def _run_phase(
        self,
        phase,
        state: "SettlementState",
        round_num: int,
    ) -> list[AgentOutput]:
        if not phase.agent_roles:
            print(f"\n  [Phase: {phase.name.upper()}] — Arbiter applying consequences...")
            return []

        print(f"\n  [Phase: {phase.name.upper()}] {phase.description}")

        outputs: list[AgentOutput] = []
        # Track outputs produced within this phase for intra-phase riffing
        phase_outputs_by_role: dict[str, AgentOutput] = {}

        for role in phase.agent_roles:
            agent = self._agents.get(role)

            # Build memory context
            context = MemoryContext.build(state, self._logger, self._memory_window)

            # Resolve riffing injections
            injected = self._riffing.resolve(
                phase, role, phase_outputs_by_role, round_num
            )

            print(f"    → {role.title()} is thinking...", end="", flush=True)
            output = agent.run(context, round_num, phase.name, injected)
            print(" done.")

            self._logger.log(output)
            outputs.append(output)
            phase_outputs_by_role[role] = output

        return outputs

    # ── State mutation ────────────────────────────────────────────────────────

    def _apply_all_patches(
        self,
        round_outputs: list[AgentOutput],
        state: "SettlementState",
    ) -> None:
        for output in round_outputs:
            if output.state_patch:
                print(
                    f"    Applying patch from {output.agent_role}: "
                    f"{list(output.state_patch.keys())}"
                )
                state.apply_patch(output.state_patch)

    # ── File output ───────────────────────────────────────────────────────────

    def _write_round_files(
        self,
        output_dir: str,
        round_num: int,
        state: "SettlementState",
        outputs: list[AgentOutput],
    ) -> None:
        prefix = os.path.join(output_dir, f"round_{round_num:02d}")

        # JSON summary
        summary = {
            "round": round_num,
            "state": state.to_dict(),
            "outputs": [o.to_dict() for o in outputs],
        }
        with open(f"{prefix}_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # Readable narrative
        with open(f"{prefix}_narrative.txt", "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n")
            f.write(f"ROUND {round_num} — {state._data['name']}\n")
            f.write(f"{'='*60}\n\n")
            for output in outputs:
                f.write(f"[{output.phase.upper()} / {output.agent_role.upper()}]\n")
                f.write(output.content.strip())
                f.write("\n\n" + "-" * 40 + "\n\n")
