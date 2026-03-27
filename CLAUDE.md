# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Demesne is an LLM-powered simulation of the "Fantasy Settlement Creation Game" — a tabletop-style worldbuilding game where AI-controlled factions compete to shape a settlement's culture. Each faction is an LLM agent (via the Anthropic API) with a distinct ideology, goals, and voice. A deterministic Arbiter manages game rules, token economy, and state while LLM agents provide narrative and strategic decisions.

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run a simulation (requires ANTHROPIC_API_KEY in .env or environment)
python main.py --eras 3 --settlement-name "Ashford"

# CLI options
python main.py --eras <N> --settlement-name <name> --output-dir <dir> --memory-window <N>
```

The simulation is interactive — it pauses between phases for Space/Enter to continue or Esc to quit. Output goes to `./output/` by default (JSON summaries, narrative text files, JSONL action log).

## Architecture

**Arbiter (`arbiter.py`)** — The central game loop controller. Manages era flow, dispatches agents per phase, enforces all game rules (token costs, prerequisites, victory conditions), and handles the token economy. No LLM calls happen here; all dice rolls and state mutations are deterministic.

**Agents (`agents/`)** — LLM-powered agents that call the Anthropic API:
- `BaseAgent` — ABC with shared prompt building and `_extract_state_patch()` for JSON-in-output parsing
- `FactionAgent` — One per faction. Has phase-specific methods: `run_strategy()`, `run_investment()`, `run_challenge()`, plus narrative methods (`run_strategy_narrative()`, `run_challenge_narrative()`, `run_rename_strategy()`). Each method builds a detailed prompt and parses structured output from XML-tagged JSON blocks (`<strategy_choice>`, `<investment_choice>`, etc.)
- `GMAgent` — Game Master narrator. Chronicls challenges, end-of-era summaries, and culture purchase events

**State (`state/`)** — `SettlementState` holds all mutable game state in a single `_data` dict: factions, cultures, tokens, landmarks, initiative order, challenge difficulty. `MemoryContext` builds the context dict passed to agent prompts from current state + recent action log.

**Mechanics (`mechanics/`)** — Pure game logic, no LLM calls:
- `cultures.py` — Culture tree definition (8 categories x 3 levels, opposing options, token costs)
- `strategies.py` — Payout tables (base/L1/L2/L3), Make exchange logic, strategic stances, challenge categories
- `scoring.py` — VP calculation against faction goals
- `ideologies.py` — 16 ideology definitions with goals, worldview, cooperation/betrayal patterns
- `dice.py` — Simple d20 roller

**Phases (`phases/`)** — `PhaseConfig` dataclasses defining the 4 era phases: Strategy, Investment, Challenge, End of Era. `PhaseEngine` iterates over them.

**Flow**: `main.py` → builds factions + state → `Arbiter.run()` loops eras → each era runs 4 phases → Arbiter dispatches faction/GM agents per phase → agents call Anthropic API → Arbiter validates and applies results to `SettlementState`.

## Key Design Patterns

- **LLM outputs are always validated**: Faction agents return structured JSON in XML tags; the Arbiter checks prerequisites, token affordability, and option validity before applying any state change. Invalid LLM choices are silently skipped.
- **Narrative is post-hoc**: Strategy decisions are resolved mechanically first (dice + payout tables), then the LLM provides in-character flavor text. The LLM does not control game outcomes.
- **Initiative order**: Factions act in d20 initiative order (rolled once at game start). The highest roller becomes the initial Leading Faction.
- **Reconsideration**: When culture purchases or leadership changes occur, all factions get `needs_reconsideration = True`, triggering an LLM call next Strategy Phase to potentially change their stance.
- **Cooperative purchases**: After individual investment, the Arbiter checks if pooled tokens across all factions can afford upgrades no single faction could.
- **Token colors** map to culture categories: red=spirituality, blue=mindset/social_order, green=values, orange=politics/property, pink=production/natural_affinity.

## Configuration

`config.py` loads from `.env`. Key settings: `MODEL` (default: claude-opus-4-6), `MEMORY_WINDOW` (5), `MAX_ERAS` (10), `WIN_VP_THRESHOLD` (80).
