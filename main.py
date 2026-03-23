#!/usr/bin/env python3
"""
Demesne — Fantasy Settlement Creation Game simulation engine.

Usage:
    python main.py --eras 3 --settlement-name "Ashford"
    python main.py --eras 1
"""
import argparse
import json
import os
import sys

import random
import config
from utils import pause
from mechanics.dice import roll
from state.settlement import SettlementState
from agents.faction import FactionAgent
from agents.gm import GMAgent
from agents.registry import AgentRegistry
from phases.engine import PhaseEngine
from logger import ActionLogger
from arbiter import Arbiter
from mechanics.ideologies import IDEOLOGIES, PROTOTYPE_IDEOLOGIES
from mechanics.scoring import score_all_factions
from mechanics.strategies import STRATEGIC_STANCES


def _empty_tokens() -> dict:
    return {"red": 0, "blue": 0, "green": 0, "orange": 0, "pink": 0}


def build_faction_data(ideology_name: str, faction_index: int) -> dict:
    """Create a faction data dict for a given ideology."""
    id_ = IDEOLOGIES[ideology_name]
    return {
        "name": f"{ideology_name} Faction",
        "ideology": ideology_name,
        "species": "Human",          # placeholder — can be overridden
        "organization_type": "Guild",  # placeholder
        "tokens": _empty_tokens(),
        "victory_points": 0,
        "goals": {
            "primary": id_["primary"],
            "secondary": id_["secondary"],
            "tertiary": id_["tertiary"],
        },
        "needs_reconsideration": False,
    }


def build_factions(ideology_names: list[str]) -> tuple[list[FactionAgent], SettlementState]:
    """Build faction agents and register them in the settlement state."""
    state = SettlementState.__new__(SettlementState)
    state.__init__("placeholder")  # will be overwritten by caller

    agents = []
    for i, name in enumerate(ideology_names):
        faction_data = build_faction_data(name, i)
        agents.append(FactionAgent(faction_data))

    return agents, [build_faction_data(n, i) for i, n in enumerate(ideology_names)]


def write_final_summary(output_dir: str, state: SettlementState, all_actions: list[dict]) -> None:
    final_state_path = os.path.join(output_dir, "final_state.json")
    with open(final_state_path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)

    narrative_path = os.path.join(output_dir, "narrative_summary.txt")
    with open(narrative_path, "w", encoding="utf-8") as f:
        f.write(f"DEMESNE SIMULATION — {state._data['name']}\n")
        f.write("=" * 60 + "\n\n")
        current_era = 0
        for action in all_actions:
            era = action.get("round", 0)
            if era != current_era:
                current_era = era
                f.write(f"\n{'='*60}\nERA {current_era}\n{'='*60}\n\n")
            f.write(f"[{action['phase'].upper()} / {action['agent_role'].upper()}]\n")
            f.write(action["content"].strip())
            f.write("\n\n" + "-" * 40 + "\n\n")

        f.write("\n\nFINAL STATE\n" + "=" * 60 + "\n")
        f.write(state.to_json())

    print(f"\nFinal state:       {final_state_path}")
    print(f"Narrative summary: {narrative_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Demesne simulation engine")
    parser.add_argument("--eras", type=int, default=3, help="Number of eras to simulate")
    parser.add_argument("--settlement-name", default="The Settlement", help="Settlement name")
    parser.add_argument("--output-dir", default=config.OUTPUT_DIR, help="Output directory")
    parser.add_argument(
        "--memory-window", type=int, default=config.MEMORY_WINDOW,
        help="Recent actions in agent context"
    )
    args = parser.parse_args()

    if not config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set. Create a .env file or export the variable.")
        sys.exit(1)

    print(f"Demesne simulation starting...")
    print(f"  Settlement : {args.settlement_name}")
    print(f"  Eras       : {args.eras}")
    print(f"  Output dir : {args.output_dir}")
    print(f"  Model      : {config.MODEL}")
    print(f"  Factions   : {', '.join(PROTOTYPE_IDEOLOGIES)}")

    # Build state and factions
    state = SettlementState(name=args.settlement_name)
    faction_agents = []
    for i, ideology_name in enumerate(PROTOTYPE_IDEOLOGIES):
        faction_data = build_faction_data(ideology_name, i)
        faction_data["current_stance"] = random.choice(list(STRATEGIC_STANCES.keys()))
        state.add_faction(faction_data)
        faction_agents.append(FactionAgent(faction_data))
        # Keep faction_data and FactionAgent in sync via shared reference through state
        faction_agents[-1].faction_data = state.get_faction(faction_data["name"])

    # ── Initiative rolls ──────────────────────────────────────────────────────
    print("\n  [INITIATIVE ROLLS]")
    initiative_rolls: dict[str, int] = {}
    for agent in faction_agents:
        fname = agent.faction_data["name"]
        r = roll(20)
        initiative_rolls[fname] = r
        print(f"    {fname}: rolled {r}")

    initiative_order = sorted(initiative_rolls, key=lambda n: initiative_rolls[n], reverse=True)
    state.set_initiative_order(initiative_order)
    # Re-sync faction_data references after set_initiative_order changes leading_faction
    for agent in faction_agents:
        agent.faction_data = state.get_faction(agent.faction_data["name"])
    print(f"\n  Leading faction: {initiative_order[0]}")
    print(f"  Initiative order: {', '.join(initiative_order)}")
    pause("  ── Initiative set. Press Space/Enter to continue or Esc to quit ──")

    gm_agent = GMAgent()
    phase_engine = PhaseEngine()
    logger = ActionLogger(args.output_dir)

    arbiter = Arbiter(
        phase_engine=phase_engine,
        faction_agents=faction_agents,
        gm_agent=gm_agent,
        logger=logger,
        memory_window=args.memory_window,
    )

    final_state = arbiter.run(state, max_eras=args.eras, output_dir=args.output_dir)
    write_final_summary(args.output_dir, final_state, logger.all_actions)

    # Print final scores
    print("\nFinal Victory Points:")
    for f in final_state.factions:
        print(f"  {f['name']}: {f['victory_points']} VP")
    if final_state._data["winner"]:
        print(f"\nWinner: {final_state._data['winner']}")

    print("\nSimulation complete.")


if __name__ == "__main__":
    main()
