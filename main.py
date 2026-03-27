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
from phases.engine import PhaseEngine
from logger import ActionLogger
from arbiter import Arbiter
from mechanics.ideologies import IDEOLOGIES
from mechanics.strategies import STRATEGIC_STANCES
from mechanics.worldbuilding import LOCATIONS, TERRAINS, DND5_RACES


def _empty_tokens() -> dict:
    return {"red": 0, "blue": 0, "green": 0, "orange": 0, "pink": 0}


def build_faction_data(ideology_name: str, faction_index: int) -> dict:
    """Create a faction data dict for a given ideology."""
    id_ = IDEOLOGIES[ideology_name]
    return {
        "name": f"{ideology_name} Faction",
        "ideology": ideology_name,
        "species": "Human",          # overridden by race roll during initiative
        "organization_type": "Guild",  # overridden by faction introduction
        "tokens": _empty_tokens(),
        "victory_points": 0,
        "goals": {
            "primary": id_["primary"],
            "secondary": id_["secondary"],
            "tertiary": id_["tertiary"],
        },
        "needs_reconsideration": False,
        "culture_preferences": id_.get("culture_preferences", {}),
    }


def write_final_summary(output_dir: str, state: SettlementState, all_actions: list[dict], all_events: list[dict]) -> None:
    final_state_path = os.path.join(output_dir, "final_state.json")
    with open(final_state_path, "w", encoding="utf-8") as f:
        json.dump({"state": state.to_dict(), "events": all_events}, f, indent=2)

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
    parser.add_argument(
        "--factions", type=int, default=0,
        help=f"Number of factions ({config.MIN_FACTIONS}-{config.MAX_FACTIONS}, random if not set)"
    )
    args = parser.parse_args()

    if not config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set. Create a .env file or export the variable.")
        sys.exit(1)

    # Select random ideologies
    num_factions = args.factions or random.randint(config.MIN_FACTIONS, config.MAX_FACTIONS)
    num_factions = max(config.MIN_FACTIONS, min(num_factions, len(IDEOLOGIES)))
    chosen_ideologies = random.sample(list(IDEOLOGIES.keys()), num_factions)

    print(f"Demesne simulation starting...")
    print(f"  Settlement : {args.settlement_name}")
    print(f"  Eras       : {args.eras}")
    print(f"  Output dir : {args.output_dir}")
    print(f"  Model      : {config.MODEL}")
    print(f"  Factions   : {num_factions} — {', '.join(chosen_ideologies)}")

    # Initialize logger early so pre-game events are captured
    logger = ActionLogger(args.output_dir)

    # Build state and factions
    state = SettlementState(name=args.settlement_name)
    faction_agents = []
    for i, ideology_name in enumerate(chosen_ideologies):
        faction_data = build_faction_data(ideology_name, i)
        faction_data["current_stance"] = random.choice(list(STRATEGIC_STANCES.keys()))
        state.add_faction(faction_data)
        faction_agents.append(FactionAgent(faction_data))
        # Keep faction_data and FactionAgent in sync via shared reference through state
        faction_agents[-1].faction_data = state.get_faction(faction_data["name"])

    # ── Location & Terrain ────────────────────────────────────────────────────
    location = random.choice(LOCATIONS)
    terrain = random.choice(TERRAINS)
    state.set_location(location)
    state.set_terrain(terrain)
    print(f"\n  [GEOGRAPHY]")
    print(f"    Location : {location}")
    print(f"    Terrain  : {terrain}")
    logger.log_event("geography", era=0, location=location, terrain=terrain)

    # ── Initiative rolls & species ───────────────────────────────────────────
    print("\n  [INITIATIVE ROLLS]")
    initiative_rolls: dict[str, int] = {}
    for agent in faction_agents:
        fname = agent.faction_data["name"]
        r = roll(20)
        initiative_rolls[fname] = r
        species = random.choice(DND5_RACES)
        faction = state.get_faction(fname)
        faction["species"] = species
        agent.faction_data = faction
        print(f"    {fname}: rolled {r} — {species}")
        logger.log_event("species_roll", era=0, faction=fname, species=species)

    initiative_order = sorted(initiative_rolls, key=lambda n: initiative_rolls[n], reverse=True)
    state.set_initiative_order(initiative_order)
    for agent in faction_agents:
        agent.faction_data = state.get_faction(agent.faction_data["name"])
    print(f"\n  Leading faction: {initiative_order[0]}")
    print(f"  Initiative order: {', '.join(initiative_order)}")
    logger.log_event("initiative", era=0, rolls=initiative_rolls, order=initiative_order, leader=initiative_order[0])
    pause("  ── Initiative set. Press Space/Enter to continue or Esc to quit ──")

    # ── Faction introductions (LLM) ──────────────────────────────────────────
    print("\n  [FACTION INTRODUCTIONS]")
    all_faction_data = [state.get_faction(a.faction_data["name"]) for a in faction_agents]
    for agent in faction_agents:
        fname = agent.faction_data["name"]
        neighbors = [f for f in all_faction_data if f["name"] != fname]
        print(f"\n    → {fname} introducing themselves...", end="", flush=True)
        intro_output = agent.introduce_faction(location, terrain, neighbors)
        print(" done.\n")
        intro = agent.parse_faction_intro(intro_output)
        if intro:
            new_name = intro.get("faction_name", fname)
            org_type = intro.get("organization_type", "Guild")
            description = intro.get("description", "")
            # Update faction data in state
            faction = state.get_faction(fname)
            faction["name"] = new_name
            faction["organization_type"] = org_type
            faction["description"] = description
            agent.faction_data = faction
            # Update initiative order with new name
            initiative_order = [new_name if n == fname else n for n in state.initiative_order]
            state._data["initiative_order"] = initiative_order
            if state._data["leading_faction"] == fname:
                state._data["leading_faction"] = new_name
            agent.role = f"faction_{new_name.lower().replace(' ', '_')}"
            print(f"  {new_name} ({agent.faction_data['species']} {org_type})")
            if description:
                print(f"    {description}")
            logger.log_event("faction_intro", era=0,
                old_name=fname, new_name=new_name, species=agent.faction_data["species"],
                ideology=agent.faction_data["ideology"], organization_type=org_type,
                description=description)
        pause(f"  ── {agent.faction_data['name']} introduced. Press Space/Enter to continue or Esc to quit ──")

    # ── Settlement naming (leading faction, LLM) ─────────────────────────────
    leader_agent = next(a for a in faction_agents if a.faction_data["name"] == state.leading_faction)
    print(f"\n    → {state.leading_faction} naming the settlement...", end="", flush=True)
    naming_output = leader_agent.name_settlement(location, terrain)
    print(" done.\n")
    naming_choice = leader_agent.parse_settlement_name(naming_output)
    settlement_name = naming_choice.get("name") or args.settlement_name
    landmark_desc = naming_choice.get("description", "")
    state._data["name"] = settlement_name
    if landmark_desc:
        state.set_landmark_description(landmark_desc)
    print(f"  Settlement named: {settlement_name}")
    if landmark_desc:
        print(f"  Landmarks: {landmark_desc}")
    logger.log_event("settlement_named", era=0, name=settlement_name, landmark_description=landmark_desc, named_by=state.leading_faction)

    pause("  ── Settlement established. Press Space/Enter to continue or Esc to quit ──")

    gm_agent = GMAgent()
    phase_engine = PhaseEngine()

    arbiter = Arbiter(
        phase_engine=phase_engine,
        faction_agents=faction_agents,
        gm_agent=gm_agent,
        logger=logger,
        memory_window=args.memory_window,
    )

    final_state = arbiter.run(state, max_eras=args.eras, output_dir=args.output_dir)
    write_final_summary(args.output_dir, final_state, logger.all_actions, logger.all_events)

    # Print final scores
    print("\nFinal Victory Points:")
    for f in final_state.factions:
        print(f"  {f['name']}: {f['victory_points']} VP")
    if final_state._data["winner"]:
        print(f"\nWinner: {final_state._data['winner']}")

    print("\nSimulation complete.")


if __name__ == "__main__":
    main()
