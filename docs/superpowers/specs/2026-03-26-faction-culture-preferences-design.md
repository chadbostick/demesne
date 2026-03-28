# Faction Culture Preferences

> **Status: IMPLEMENTED** (deterministic mode). LLM mode deferred. See `mechanics/culture_preferences.py` for the 768 preference labels across 16 ideologies, and `agents/faction.py` for `_culture_preferences_block()` integration into strategy and investment prompts.

## Problem

Factions targeting L3 goals need L1 and L2 prerequisites unlocked first, but currently have no opinion about *which* option at each prerequisite level they prefer. This flattens storytelling — a Progressionist chasing Democracy should prefer Anarchy over Authoritarian at L1, Republic over Monarchy at L2. Factions should pursue options that fit their ideology, even when either option would satisfy the mechanical prerequisite.

## Design

### Config Toggle

New setting in `config.py`:

```python
CULTURE_PREFERENCE_MODE = "deterministic"  # "deterministic" | "llm"
```

- **deterministic** (default): Preferences are read from a hardcoded table in each ideology definition. No API cost.
- **llm**: An LLM call at faction creation generates the preference map based on the ideology's personality.

### Preference Labels

Every culture option at every level gets one of four labels from the faction's perspective:

- **must-have**: Goal option or strongly preferred prerequisite on their goal path
- **preferred**: Aligns with worldview, would buy if affordable
- **indifferent**: No strong opinion
- **antithesis**: Opposes ideology, would block if possible

### Data Structure

Each ideology gets a new `culture_preferences` dict. Option names must exactly match the casing and spelling from `CULTURE_TREE` in `mechanics/cultures.py`. A startup validation function checks all 16 ideologies for completeness (all 8 categories, all 3 levels, both options per level) and valid labels.

```python
"culture_preferences": {
    "politics": {
        1: {"Anarchy": "must-have", "Authoritarian": "antithesis"},
        2: {"Republic": "must-have", "Monarchy": "antithesis"},
        3: {"Democracy": "must-have", "Empire": "antithesis"},
    },
    "mindset": { ... },
    # all 8 categories, all 3 levels
}
```

Because `mechanics/ideologies.py` is already large (~14k tokens), the preference tables go in a new file `mechanics/culture_preferences.py` and are merged into the ideology dicts at import time.

This must be authored for all 16 ideologies (8 categories x 3 levels x 2 options = 48 preference labels per ideology, 768 total).

### Validation

A `validate_culture_preferences()` function in `mechanics/culture_preferences.py` runs at import time and checks:
- Every ideology has a `culture_preferences` key
- Every category from `CULTURE_TREE` is present
- Every level (1-3) is present per category
- Both option names at each level match `CULTURE_TREE` exactly
- Every label is one of: `must-have`, `preferred`, `indifferent`, `antithesis`

Raises `ValueError` on any mismatch, failing fast at startup rather than silently producing wrong behavior.

### Faction Initialization

In `main.py`, after `FactionAgent` is instantiated:

- If `deterministic`: copy `culture_preferences` from the ideology definition into `faction_data["culture_preferences"]`
- If `llm`: call a new `FactionAgent.generate_culture_preferences()` method that prompts the LLM with the ideology and culture tree, parses the result in a `<culture_preferences>` XML tag, and stores it in `faction_data["culture_preferences"]`. On parse failure or invalid labels, fall back to the deterministic table for that ideology.

### Prompt Integration

New method `FactionAgent._culture_preferences_block()` renders the preference map as a prompt block. Only includes levels that haven't been purchased yet (already-purchased levels are settled and irrelevant).

Label-to-prompt-language mapping:
- `must-have` → "want"
- `preferred` → "lean toward"
- `indifferent` → "indifferent to"
- `antithesis` → "oppose"

Example output:
```
YOUR CULTURE PREFERENCES (unpurchased levels only):
  politics L1: want Anarchy, oppose Authoritarian
  politics L2: want Republic, oppose Monarchy
  politics L3: want Democracy, oppose Empire
  mindset L1: lean toward Impulsive, indifferent to Cautious
  ...
```

This block is included in prompts for:
- `run_strategy()` — during reconsideration, so the faction can choose a stance informed by which cultures they still want. `run_strategy()` gains a `cultures` parameter (like `run_investment()` already has) so the method can filter already-purchased levels.
- `run_investment()` — so the faction knows which options to buy or block (already receives `cultures`)

Not included in `run_challenge()` or narrative prompts. Challenge donations are about tokens and tactical positioning, not culture preferences. Narrative prompts are post-hoc flavor and shouldn't be driven by preference metadata.

Preferences are private to each faction — other factions do not see them.

### Files Changed

1. **`config.py`** — add `CULTURE_PREFERENCE_MODE` setting
2. **`mechanics/culture_preferences.py`** — new file with preference tables for all 16 ideologies, validation function, and merge logic
3. **`mechanics/ideologies.py`** — import `culture_preferences.py` and mutate `IDEOLOGIES` dict entries in place (e.g., `IDEOLOGIES["Progressionist"]["culture_preferences"] = ...`) at module load time
4. **`main.py`** — read or generate preferences at faction creation
5. **`agents/faction.py`** — add `_culture_preferences_block()`, add `generate_culture_preferences()` for LLM mode, include preferences block in `run_strategy()` and `run_investment()` prompts
