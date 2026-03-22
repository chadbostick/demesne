#!/usr/bin/env python3
"""
Demesne — Turn-based worldbuilding simulation engine.

Usage:
    python main.py --rounds 3 --settlement-name "Ashford"
    python main.py --rounds 1 --output-dir ./my_output
"""
import argparse
import json
import os
import sys

import config
from state.settlement import SettlementState
from agents.registry import AgentRegistry
from agents.creative import (
    HistorianAgent,
    ProphetAgent,
    CartographerAgent,
    RumormongerAgent,
)
from phases.engine import PhaseEngine
from logger import ActionLogger
from arbiter import Arbiter


def build_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(HistorianAgent())
    registry.register(ProphetAgent())
    registry.register(CartographerAgent())
    registry.register(RumormongerAgent())
    return registry


def write_final_summary(output_dir: str, state: SettlementState, all_actions: list[dict]) -> None:
    # Final state JSON
    final_state_path = os.path.join(output_dir, "final_state.json")
    with open(final_state_path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)

    # Full narrative text
    narrative_path = os.path.join(output_dir, "narrative_summary.txt")
    with open(narrative_path, "w", encoding="utf-8") as f:
        f.write(f"DEMESNE SIMULATION — {state._data['name']}\n")
        f.write("=" * 60 + "\n\n")
        current_round = 0
        for action in all_actions:
            if action["round"] != current_round:
                current_round = action["round"]
                f.write(f"\n{'='*60}\nROUND {current_round}\n{'='*60}\n\n")
            f.write(f"[{action['phase'].upper()} / {action['agent_role'].upper()}]\n")
            f.write(action["content"].strip())
            f.write("\n\n" + "-" * 40 + "\n\n")
        f.write("\n\nFINAL STATE\n" + "=" * 60 + "\n")
        f.write(state.to_json())

    print(f"\nFinal state written to:   {final_state_path}")
    print(f"Narrative summary at:     {narrative_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Demesne worldbuilding simulation")
    parser.add_argument("--rounds", type=int, default=1, help="Number of rounds to simulate")
    parser.add_argument("--settlement-name", default="The Settlement", help="Name of the settlement")
    parser.add_argument("--output-dir", default=config.OUTPUT_DIR, help="Directory for output files")
    parser.add_argument("--memory-window", type=int, default=config.MEMORY_WINDOW,
                        help="Number of recent actions to include in agent context")
    args = parser.parse_args()

    if not config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set. Create a .env file or export the variable.")
        sys.exit(1)

    print(f"Demesne starting up...")
    print(f"  Settlement : {args.settlement_name}")
    print(f"  Rounds     : {args.rounds}")
    print(f"  Output dir : {args.output_dir}")
    print(f"  Model      : {config.MODEL}")
    print(f"  Memory     : last {args.memory_window} actions")

    state = SettlementState(name=args.settlement_name)
    registry = build_registry()
    phase_engine = PhaseEngine()
    logger = ActionLogger(args.output_dir)

    arbiter = Arbiter(
        phase_engine=phase_engine,
        agent_registry=registry,
        logger=logger,
        memory_window=args.memory_window,
    )

    final_state = arbiter.run(state, rounds=args.rounds, output_dir=args.output_dir)
    write_final_summary(args.output_dir, final_state, logger.all_actions)

    print("\nSimulation complete.")


if __name__ == "__main__":
    main()
