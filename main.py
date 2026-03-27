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
import re
import sys
from datetime import datetime

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


def _vprint(*args, **kwargs):
    """Print only if verbose mode is on."""
    if config.VERBOSE:
        print(*args, **kwargs)


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
        "influence": 0,
    }


def _build_game_chronicle(state: SettlementState, all_events: list[dict], max_era: int) -> dict:
    """Build a comprehensive game chronicle organized by era."""
    state_data = state.to_dict()

    # Organize events by era
    eras: dict[int, list[dict]] = {}
    for e in all_events:
        era = e.get("era", 0)
        eras.setdefault(era, []).append(e)

    era_summaries = []
    for era_num in range(0, max_era + 1):
        era_events = eras.get(era_num, [])
        era_entry: dict = {"era": era_num, "events": era_events}

        if era_num == 0:
            era_entry["label"] = "Pre-Game Setup"
        else:
            era_entry["label"] = f"Age {era_num}"

        # Extract key data per era
        era_entry["challenges"] = [e for e in era_events if e["event_type"] == "challenge_drawn"]
        era_entry["challenge_results"] = [e for e in era_events if e["event_type"] == "challenge_resolved"]
        era_entry["culture_purchases"] = [e for e in era_events if e["event_type"] == "culture_purchase"]
        era_entry["places_founded"] = [e for e in era_events if e["event_type"] == "place_founded"]
        era_entry["structures_built"] = [e for e in era_events if e["event_type"] == "structure_built"]
        era_entry["boons"] = [e for e in era_events if e["event_type"] == "boon_awarded"]
        era_entry["leadership_shifts"] = [e for e in era_events if e["event_type"] == "leadership_shift"]
        era_entry["eliminations"] = [e for e in era_events if e["event_type"] == "faction_eliminated"]
        era_entry["vp_updates"] = [e for e in era_events if e["event_type"] == "vp_update"]

        era_summaries.append(era_entry)

    chronicle = {
        "settlement": {
            "name": state_data["name"],
            "location": state_data.get("location"),
            "terrain": state_data.get("terrain"),
            "landmark_description": state_data.get("landmark_description"),
            "stage": state.settlement_stage(),
            "total_eras": max_era,
            "winner": state_data.get("winner"),
            "game_over": state_data.get("game_over", False),
        },
        "factions": [
            {
                "name": f["name"],
                "ideology": f["ideology"],
                "species": f["species"],
                "organization_type": f["organization_type"],
                "description": f.get("description", ""),
                "influence": f.get("influence", 0),
                "victory_points": f["victory_points"],
                "tokens": f["tokens"],
                "goals": f["goals"],
            }
            for f in state_data["factions"]
        ],
        "eliminated_factions": [
            e for e in all_events if e["event_type"] == "faction_eliminated"
        ],
        "cultures": state_data["cultures"],
        "places": state_data.get("places", []),
        "landmarks": state_data.get("landmarks", []),
        "boons": state_data.get("boons", []),
        "eras": era_summaries,
    }
    return chronicle


def write_final_summary(output_dir: str, state: SettlementState, all_actions: list[dict], all_events: list[dict], max_era: int) -> None:
    final_state_path = os.path.join(output_dir, "final_state.json")
    with open(final_state_path, "w", encoding="utf-8") as f:
        json.dump({"state": state.to_dict(), "events": all_events}, f, indent=2)

    # Phases to exclude from narrative (mechanical, not story)
    _MECHANICAL_PHASES = {"strategy", "investment", "rename_strategy", "historical_figure"}

    def _clean_narrative(text: str) -> str:
        """Strip XML tags and JSON blocks from LLM output for narrative file."""
        import re as _re
        # Remove XML-tagged JSON blocks
        text = _re.sub(r"<\w+>\s*\{[^}]*\}\s*</\w+>", "", text, flags=_re.DOTALL)
        # Remove any remaining XML tags
        text = _re.sub(r"</?[\w_]+>", "", text)
        return text.strip()

    narrative_path = os.path.join(output_dir, "narrative_summary.txt")
    with open(narrative_path, "w", encoding="utf-8") as f:
        f.write(f"DEMESNE SIMULATION — {state._data['name']}\n")
        f.write("=" * 60 + "\n\n")
        current_era = 0
        for action in all_actions:
            phase = action.get("phase", "")
            if phase in _MECHANICAL_PHASES:
                continue
            era = action.get("round", 0)
            if era != current_era:
                current_era = era
                f.write(f"\n{'='*60}\nAge {current_era}\n{'='*60}\n\n")
            content = _clean_narrative(action["content"])
            if not content:
                continue
            f.write(content)
            f.write("\n\n" + "-" * 40 + "\n\n")

        f.write("\n\nFINAL STATE\n" + "=" * 60 + "\n")
        f.write(state.to_json())

    # Comprehensive chronicle
    chronicle = _build_game_chronicle(state, all_events, max_era)
    chronicle_path = os.path.join(output_dir, "game_chronicle.json")
    with open(chronicle_path, "w", encoding="utf-8") as f:
        json.dump(chronicle, f, indent=2)

    _vprint(f"\nFinal state:       {final_state_path}")
    _vprint(f"Narrative summary: {narrative_path}")
    print(f"\nGame chronicle:    {chronicle_path}")

    # Print chronicle to console in verbose mode
    if config.VERBOSE:
        print(f"\n{'='*60}")
        print("COMPREHENSIVE GAME CHRONICLE")
        print(f"{'='*60}\n")
        print(json.dumps(chronicle, indent=2))


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
    parser.add_argument(
        "--difficulty", type=int, default=10,
        help="Starting challenge difficulty (default: 10)"
    )
    parser.add_argument(
        "--verbose", action="store_true", default=config.VERBOSE,
        help="Show metagame info (tokens, dice rolls, decision trees)"
    )
    parser.add_argument(
        "--pauses", action="store_true", default=config.ALL_PAUSES,
        help="Pause at every phase (default: only end of era)"
    )
    args = parser.parse_args()

    # Set global display modes
    config.VERBOSE = args.verbose
    config.ALL_PAUSES = args.pauses

    if not config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set. Create a .env file or export the variable.")
        sys.exit(1)

    # Select random ideologies
    num_factions = args.factions or random.randint(config.MIN_FACTIONS, config.MAX_FACTIONS)
    num_factions = max(config.MIN_FACTIONS, min(num_factions, len(IDEOLOGIES)))
    chosen_ideologies = random.sample(list(IDEOLOGIES.keys()), num_factions)

    # Create timestamped run subfolder
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    run_dir = os.path.join(args.output_dir, f"Settlement {timestamp}")
    os.makedirs(run_dir, exist_ok=True)

    print(f"Demesne simulation starting...")
    _vprint(f"  Settlement : {args.settlement_name}")
    _vprint(f"  Eras       : {args.eras}")
    _vprint(f"  Output dir : {run_dir}")
    _vprint(f"  Model      : {config.MODEL}")
    _vprint(f"  Factions   : {num_factions} — {', '.join(chosen_ideologies)}")

    # Initialize logger early so pre-game events are captured
    logger = ActionLogger(run_dir)

    # Build state and factions
    state = SettlementState(name=args.settlement_name)
    state._data["challenge_difficulty"] = args.difficulty
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
    _vprint(f"\n  [GEOGRAPHY]")
    _vprint(f"    Location : {location}")
    _vprint(f"    Terrain  : {terrain}")
    logger.log_event("geography", era=0, location=location, terrain=terrain)

    # Seed economy based on geography
    _TERRAIN_PRODUCTION = {
        "Mountains": ["stone", "ore", "mountain herbs"],
        "Forest": ["timber", "game", "wild herbs", "mushrooms"],
        "Plains": ["grain", "livestock", "hay"],
        "Desert": ["salt", "gemstones", "cactus fiber"],
        "Tundra": ["furs", "bone", "seal oil"],
        "Hills": ["clay", "sheep", "root vegetables"],
        "Valley": ["fruit", "grain", "freshwater fish"],
        "Plateau": ["wind-dried meat", "hardy grains", "stone"],
        "Swamp": ["peat", "reeds", "swamp herbs", "fish"],
        "Marsh": ["waterfowl", "rushes", "shellfish", "bog iron"],
    }
    _TERRAIN_SCARCITY = {
        "Mountains": ["grain", "timber"],
        "Forest": ["stone", "open grazing land"],
        "Plains": ["timber", "stone", "metal ore"],
        "Desert": ["water", "timber", "grain"],
        "Tundra": ["grain", "timber", "fresh vegetables"],
        "Hills": ["timber", "fish"],
        "Valley": ["stone", "metal ore"],
        "Plateau": ["water", "timber"],
        "Swamp": ["stone", "dry land", "grain"],
        "Marsh": ["stone", "timber", "dry land"],
    }
    for item in _TERRAIN_PRODUCTION.get(terrain, ["foraged food"]):
        state.add_production(item)
    for item in _TERRAIN_SCARCITY.get(terrain, []):
        state.add_scarcity(item)

    # ── Initiative rolls & species ───────────────────────────────────────────
    _vprint("\n  [INITIATIVE ROLLS]")
    initiative_rolls: dict[str, int] = {}
    for agent in faction_agents:
        fname = agent.faction_data["name"]
        r = roll(20)
        initiative_rolls[fname] = r
        species = random.choice(DND5_RACES)
        faction = state.get_faction(fname)
        faction["species"] = species
        agent.faction_data = faction
        _vprint(f"    {fname}: rolled {r} — {species}")
        logger.log_event("species_roll", era=0, faction=fname, species=species)

    initiative_order = sorted(initiative_rolls, key=lambda n: initiative_rolls[n], reverse=True)
    state.set_initiative_order(initiative_order)
    # Set initial influence from initiative rolls
    for agent in faction_agents:
        fname = agent.faction_data["name"]
        faction = state.get_faction(fname)
        faction["influence"] = initiative_rolls[fname]
        agent.faction_data = faction
    _vprint(f"\n  Leading faction: {initiative_order[0]}")
    _vprint(f"  Initiative order: {', '.join(initiative_order)}")
    logger.log_event("initiative", era=0, rolls=initiative_rolls, order=initiative_order, leader=initiative_order[0])
    pause("  ── Initiative set. Press Space/Enter to continue or Esc to quit ──")

    # ── Faction introductions (LLM) ──────────────────────────────────────────
    print("\n  ── The Settlers Arrive ──")
    all_faction_data = [state.get_faction(a.faction_data["name"]) for a in faction_agents]
    for agent in faction_agents:
        fname = agent.faction_data["name"]
        neighbors = [f for f in all_faction_data if f["name"] != fname]
        _vprint(f"\n    → {fname} introducing themselves...", end="", flush=True)
        intro_output = agent.introduce_faction(location, terrain, neighbors)
        _vprint(" done.\n")
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
            # Store founding leader as historical figure
            founding_leader = intro.get("founding_leader", "")
            if founding_leader:
                state.add_historical_figure({
                    "name": founding_leader,
                    "role": "founder",
                    "faction": new_name,
                    "era": 0,
                    "deed": f"Founded {new_name} and led the initial settlement",
                    "status": "legendary",
                })

            print(f"\n  **{new_name} ({agent.faction_data['ideology']} {agent.faction_data['species']})**")
            if founding_leader:
                print(f"  Founded by {founding_leader}")
            if description:
                print(f"  {description}")
            logger.log_event("faction_intro", era=0,
                old_name=fname, new_name=new_name, species=agent.faction_data["species"],
                ideology=agent.faction_data["ideology"], organization_type=org_type,
                description=description)
        pause(f"  ── {agent.faction_data['name']} introduced. Press Space/Enter to continue or Esc to quit ──")

    # ── Settlement naming (leading faction, LLM) ─────────────────────────────
    leader_agent = next(a for a in faction_agents if a.faction_data["name"] == state.leading_faction)
    _vprint(f"\n    → {state.leading_faction} naming the settlement...", end="", flush=True)
    naming_output = leader_agent.name_settlement(location, terrain)
    _vprint(" done.\n")
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

    final_state = arbiter.run(state, max_eras=args.eras, output_dir=run_dir)
    write_final_summary(run_dir, final_state, logger.all_actions, logger.all_events, final_state.era)

    # Rename run folder to settlement name
    settlement_name_clean = re.sub(r'[^\w\s\-]', '', final_state._data["name"]).strip()
    if settlement_name_clean:
        final_dir = os.path.join(args.output_dir, f"{settlement_name_clean} {timestamp}")
        if not os.path.exists(final_dir):
            os.rename(run_dir, final_dir)
            run_dir = final_dir
            _vprint(f"  Output renamed to: {run_dir}")

    # Print final scores
    print("\nFinal Victory Points:")
    for f in final_state.factions:
        print(f"  {f['name']}: {f['victory_points']} VP")
    if final_state._data["winner"]:
        print(f"\nWinner: {final_state._data['winner']}")

    print("\nSimulation complete.")


if __name__ == "__main__":
    main()
