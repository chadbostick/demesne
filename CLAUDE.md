# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Demesne is an LLM-powered simulation of the "Fantasy Settlement Creation Game" — a tabletop-style worldbuilding game where AI-controlled factions compete to shape a settlement's culture over decades or centuries. Each faction has a distinct ideology, goals, and species. A deterministic Arbiter manages game rules, token economy, and state while LLM agents (via the Anthropic API) provide narrative. The output is a generational history suitable for D&D campaign worldbuilding.

## Running

```bash
pip install -r requirements.txt

# Basic run (requires ANTHROPIC_API_KEY in .env or environment)
python main.py --eras 5

# All options
python main.py --eras <N> --factions <N> --difficulty <N> --settlement-name <name> \
               --output-dir <dir> --memory-window <N> --verbose --pauses
```

| Flag | Default | Description |
|---|---|---|
| `--eras` | 3 | Number of ages to simulate |
| `--factions` | random 2-5 | Number of factions (from 16 ideologies) |
| `--difficulty` | 10 | Starting challenge difficulty |
| `--settlement-name` | "The Settlement" | Fallback name (overridden by LLM) |
| `--output-dir` | `./output` | Base output directory |
| `--memory-window` | 5 | Recent actions in agent LLM context |
| `--verbose` | off | Show metagame info (tokens, dice, decisions) |
| `--pauses` | off | Pause for user input (default: runs unattended) |

Output goes to `./output/YYYYMMDD-HHMM SettlementName/` with era summaries, narrative text, event logs, and a comprehensive `game_chronicle.json`.

## Architecture

**Arbiter (`arbiter.py`)** — Central game loop controller. Manages era flow, dispatches agents, enforces rules (token costs, prerequisites, victory conditions), handles the token/influence economy, and makes all strategic decisions deterministically. Contains the smart goal planner, coalition-aware strategy selection, and make exchange logic.

**Agents (`agents/`)** — LLM-powered narration agents:
- `BaseAgent` — Minimal ABC with `role` and `constraints`
- `FactionAgent` — One per faction. Methods for investment decisions (`run_investment`), challenge plans (`run_challenge_plan`), structure descriptions (`run_make_narrative`), place naming (`name_place`), faction introductions (`introduce_faction`), and settlement naming (`name_settlement`). Parses structured output from XML-tagged JSON blocks.
- `GMAgent` — Faction-agnostic chronicler. Narrates challenges, outcomes, boons, culture purchases, place foundings, strategy summaries, and end-of-era chronicles with traveler descriptions.

**State (`state/`)** — `SettlementState` holds all mutable game state: factions (tokens, influence, goals, coalition plans), cultures, places (villages/towns/city-states), landmarks, historical figures, economy (production/trade goods/scarcity/trade partners), and challenge difficulty. `MemoryContext` builds context dicts for agent prompts.

**Mechanics (`mechanics/`)** — Pure game logic, no LLM calls:
- `cultures.py` — Culture tree (8 categories x 3 levels, opposing options, token costs)
- `strategies.py` — Payout table, Make exchange logic (N tokens → N*(level+1) of any color distribution), strategic stances
- `scoring.py` — VP calculation against faction goals
- `ideologies.py` — 16 ideology definitions with goals, worldview, cooperation/betrayal patterns
- `culture_preferences.py` — Per-ideology preference tables (must-have/preferred/indifferent/antithesis for all 48 culture options)
- `worldbuilding.py` — Location/terrain/species tables, 399 challenge events, 100 boon types
- `dice.py` — Simple die roller

**Phases (`phases/`)** — `PhaseConfig` dataclasses defining the 4 era phases: Strategy, Investment, Challenge, End of Era.

## Game Flow

```
main.py startup:
  Roll geography (location + terrain) → seed economy
  Roll initiative + species per faction → set influence
  Parallel LLM: faction introductions (name, leader, description)
  Compute coalition heuristics (allies, rivals, priority order)
  LLM: leading faction names settlement + landmarks

Per era (Arbiter.run):
  Strategy Phase:
    Per faction: smart goal planner picks target color (sticky across eras)
    Check make override (exchange surplus for shortfall, distributed colors)
    Roll strategy dice (color_level+1 d20s, each checked independently)
    Batched GM narration (1 LLM call for all factions)

  Investment Phase:
    Per faction: LLM decides culture purchases
    Arbiter validates, applies, updates economy
    GM narrates each culture purchase + extracts historical figure
    Place founding: faction names village/town/city-state, GM maps it
    Cooperative purchases: willing factions pool, scored by goal alignment

  Challenge Phase:
    Roll challenge event (399 options)
    GM narrates crisis (connected to previous eras, established cultures)
    Leader declares plan (LLM)
    Token donations (scaled by settlement maturity)
    Resolution: d20 + tokens + VP bonus vs difficulty
    Success: boons + influence + token rewards
    Failure: influence shift (leader -d20, collaborators -d6, others +d6)
    GM narrates outcome + extracts historical figure

  End of Era Phase:
    GM chronicles the age + traveler arrival description
    Store era chronicle for narrative continuity
```

## Key Systems

**Influence** — Initial d20 roll becomes starting influence. Grows from tokens earned, challenge success (+d10 leader, +d6 contributors), and make exchanges. Challenge failure: leader -d20, collaborators -d6, non-collaborators +d6. Below 0 = faction eliminated. Leader = highest influence, only changes on challenge failure.

**Culture Preferences** — Each ideology has hardcoded opinions (must-have/preferred/indifferent/antithesis) about every culture option. Stored in `culture_preferences.py`, merged into ideologies at import time. Included in investment prompts.

**Coalition Heuristics** — Computed once at init from goal overlaps. Each faction knows which categories have allies (shared interests), solo targets, and conflicts (opposing options). Strategy planner prioritizes coalition categories (discounted shortfall).

**Smart Goal Planner** — Each era, evaluates all goals' next-level shortfalls, applies coalition bonus, picks the color with the biggest gap. **Sticky**: stays on a color until shortfall is covered, only switches if another goal is >3 tokens closer.

**Make Exchanges** — Give N tokens of one color, receive N*(level+1) tokens distributed across any colors (filling shortfalls). Triggers when faction has genuine excess (2+ at L0, 1+ at L1+) beyond target purchase needs.

**Settlement Growth** — L0: scattered camps. L1 purchase: village founded. L2: village grows to town. L3: city-state. Each place is named by the purchasing faction and spatially described by the GM.

**Economy** — Production, trade goods, scarcity, and trade partners tracked on state. Seeded from geography, updated by culture purchases (Farming removes grain scarcity, Mining adds refined ore, etc.).

**Historical Figures** — Named individuals extracted from GM narrations at culture purchases and challenge outcomes. Stored on state, visible in future prompts.

**Narrative Rules** — Established cultures (L1+) define community identity and must be visible in narration. L0 categories are absent from community character — only individual factions may practice them. GM writes as faction-agnostic chronicler describing the collective. Each era spans decades or centuries.

## Configuration

`config.py` loads from `.env`. Key settings:

| Setting | Default | Description |
|---|---|---|
| `MODEL` | claude-haiku-4-5-20251001 | LLM model for all API calls |
| `MEMORY_WINDOW` | 5 | Recent actions in agent context |
| `OUTPUT_DIR` | ./output | Base output directory |
| `MAX_ERAS` | 10 | Game ends after this many eras |
| `WIN_VP_THRESHOLD` | 80 | VP needed to win immediately |
| `MIN_FACTIONS` / `MAX_FACTIONS` | 2 / 5 | Random faction count range |
| `STRATEGY_NARRATION_MODE` | summary | Strategy GM narration mode |
| `CULTURE_PREFERENCE_MODE` | deterministic | Culture preference source |
| `VERBOSE` | False | Show metagame output |
| `ALL_PAUSES` | False | Enable interactive pauses |

**Token colors** map to culture categories: red=spirituality, blue=mindset/social_order, green=values, orange=politics/property, pink=production/natural_affinity.
