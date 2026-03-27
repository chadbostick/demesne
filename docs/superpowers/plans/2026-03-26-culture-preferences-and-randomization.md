# Culture Preferences & Faction Randomization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic culture preference tables for all 16 ideologies, randomize 2-5 factions per game, and integrate preferences into strategy/investment prompts.

**Architecture:** New `mechanics/culture_preferences.py` contains preference tables (must-have/preferred/indifferent/antithesis per culture option per ideology) and a validation function. Preferences are merged into `IDEOLOGIES` at import time. `main.py` randomly selects 2-5 ideologies and passes preference data through to faction agents. `FactionAgent` renders preferences into prompts for reconsideration and investment.

**Tech Stack:** Python, existing Anthropic SDK integration

---

### Task 1: Create culture preferences data file

**Files:**
- Create: `mechanics/culture_preferences.py`

This is the largest task — 768 preference labels across 16 ideologies. Each ideology needs preferences for 8 categories x 3 levels x 2 options. The labels are authored based on each ideology's goals, worldview, and thematic alignment.

Rules for authoring:
- Goal options at their goal level → `must-have`, opposing option → `antithesis`
- Prerequisite levels on goal path → `must-have` for the thematically aligned option, `antithesis` for the opposing
- Categories in secondary/tertiary goals → same logic
- Categories not in any goal → `preferred`/`indifferent` based on worldview alignment
- Enemy options from goals → `antithesis`

Reference: Game.md ideology goals, `CULTURE_TREE` in `mechanics/cultures.py`

- [ ] **Step 1: Create `mechanics/culture_preferences.py` with the `CULTURE_PREFERENCES` dict**

The dict maps ideology name → category → level → {option: label}. All 16 ideologies, all 48 option pairs each.

Ideologies and their goals (Primary L3 / Secondary1 L2 / Secondary2 L2 / Tertiary category):
- Progressionist: Democracy / Emotional / Air / Production
- Conqueror: Empire / Tribal / Raiding / Values
- Investor: Banking / Rational / Trading / Social Order
- Tyrant: Taxes / Monotheism / Fire / Mindset
- Empiricist: Science / Rational / Skill / Natural Affinity
- Mystic: Mysticism / Emotional / Air / Values
- Influencer: Diplomatic / Talent / Trading / Politics
- Survivalist: Isolationist / Monotheism / Monarchy / Production
- Noble: Class / Republic / Talent / Spirituality
- Champion: Meritocracy / Currency / Raiding / Mindset
- Competitor: Prestige / Barter / Hierarchical / Natural Affinity
- Warlord: Power / Monarchy / Polytheism / Property
- Industrialist: Manufacturing / Fire / Skill / Property
- Exploitationist: Mining / Barter / Hierarchical / Natural Affinity
- Illuminator: Light / Republic / Tribal / Spirituality
- Deceiver: Dark / Currency / Polytheism / Politics

- [ ] **Step 2: Add `validate_culture_preferences()` function**

Takes `ideology_names` (list of str) as parameter to avoid importing `IDEOLOGIES` (prevents circular import). Validates:
- Every name in `ideology_names` has a key in `CULTURE_PREFERENCES`
- Every category from `CULTURE_TREE` is present
- Every level 1-3 present per category
- Both option names match `CULTURE_TREE` exactly (case-sensitive)
- Every label is one of: `must-have`, `preferred`, `indifferent`, `antithesis`
- Raises `ValueError` on mismatch

- [ ] **Step 3: Add `merge_preferences(ideologies_dict)` function**

Takes `IDEOLOGIES` dict as parameter (avoids circular import). Validates then mutates entries in place: `ideologies_dict[name]["culture_preferences"] = CULTURE_PREFERENCES[name]`

- [ ] **Step 4: Run validation**

```bash
python -c "from mechanics.culture_preferences import CULTURE_PREFERENCES; print(f'{len(CULTURE_PREFERENCES)} ideologies validated')"
```
Expected: `16 ideologies validated`

- [ ] **Step 5: Commit**

```bash
git add mechanics/culture_preferences.py
git commit -m "Add culture preference tables for all 16 ideologies"
```

---

### Task 2: Merge preferences into ideologies and add config

**Files:**
- Modify: `mechanics/ideologies.py` (add import + merge call at bottom)
- Modify: `config.py` (add `CULTURE_PREFERENCE_MODE`)

- [ ] **Step 1: Add merge import to `mechanics/ideologies.py`**

At the bottom of the file, after `PROTOTYPE_IDEOLOGIES`:
```python
from mechanics.culture_preferences import merge_preferences
merge_preferences(IDEOLOGIES)
```

- [ ] **Step 2: Add config setting**

In `config.py`:
```python
CULTURE_PREFERENCE_MODE = "deterministic"  # "deterministic" | "llm"
```

- [ ] **Step 3: Verify merge works**

```bash
python -c "from mechanics.ideologies import IDEOLOGIES; print(IDEOLOGIES['Progressionist']['culture_preferences']['politics'])"
```
Expected: `{1: {'Anarchy': 'must-have', 'Authoritarian': 'antithesis'}, ...}`

- [ ] **Step 4: Commit**

```bash
git add mechanics/ideologies.py config.py
git commit -m "Merge culture preferences into ideologies at import, add config toggle"
```

---

### Task 3: Add preferences to faction initialization

**Files:**
- Modify: `main.py` (copy preferences into faction_data during init)

- [ ] **Step 1: In `build_faction_data()`, copy preferences from ideology**

After the `goals` assignment, add:
```python
"culture_preferences": id_.get("culture_preferences", {}),
```

> **Deferred: LLM mode.** The spec defines a `generate_culture_preferences()` LLM method with XML parsing and fallback to deterministic. This is deferred — the `CULTURE_PREFERENCE_MODE` config exists but only `"deterministic"` is implemented. LLM mode can be added later without changing the data structure.

- [ ] **Step 2: Verify**

```bash
python -c "from main import build_faction_data; d = build_faction_data('Progressionist', 0); print(d['culture_preferences']['politics'])"
```

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "Copy culture preferences into faction data at init"
```

---

### Task 4: Add preference rendering to FactionAgent

**Files:**
- Modify: `agents/faction.py` (add `_culture_preferences_block()`, update `run_strategy()` and `run_investment()`)

- [ ] **Step 1: Add `_culture_preferences_block(self, cultures: dict)` method**

Label mapping: `must-have` → "want", `preferred` → "lean toward", `indifferent` → "indifferent to", `antithesis` → "oppose"

Only shows unpurchased levels (where `cultures[cat]["level"] < level`).

- [ ] **Step 2: Add `cultures` parameter to `run_strategy()`**

Update signature to accept `cultures: dict | None = None`. Include `_culture_preferences_block(cultures)` in the prompt when cultures is provided.

- [ ] **Step 3: Include preferences in `run_investment()` prompt**

Already receives `cultures`. Add `_culture_preferences_block(cultures)` to the prompt.

- [ ] **Step 4: Update arbiter to pass `cultures` to `run_strategy()`**

In `arbiter.py`, the reconsideration call to `agent.run_strategy()` needs to pass `state.cultures`.

- [ ] **Step 5: Verify**

```bash
python -c "from mechanics.ideologies import IDEOLOGIES; from agents.faction import FactionAgent; a = FactionAgent({'name':'Test','ideology':'Progressionist','species':'Human','organization_type':'Guild','tokens':{},'victory_points':0,'goals':IDEOLOGIES['Progressionist'],'culture_preferences':IDEOLOGIES['Progressionist']['culture_preferences']}); print(a._culture_preferences_block({cat: {'level': 0, 'options_chosen': []} for cat in ['politics','property','spirituality','mindset','social_order','values','production','natural_affinity']}))"
```

- [ ] **Step 6: Commit**

```bash
git add agents/faction.py arbiter.py
git commit -m "Render culture preferences in strategy and investment prompts"
```

---

### Task 5: Randomize faction count and ideology selection

**Files:**
- Modify: `main.py` (replace `PROTOTYPE_IDEOLOGIES` with random selection)
- Modify: `config.py` (add faction count config)

- [ ] **Step 1: Add config for faction count range**

In `config.py`:
```python
MIN_FACTIONS = 2
MAX_FACTIONS = 5
```

- [ ] **Step 2: Add `--factions` CLI arg to main.py**

Optional override: `--factions N`. If not provided, random between MIN_FACTIONS and MAX_FACTIONS.

- [ ] **Step 3: Replace `PROTOTYPE_IDEOLOGIES` usage with random selection**

```python
num_factions = args.factions or random.randint(config.MIN_FACTIONS, config.MAX_FACTIONS)
all_ideologies = list(IDEOLOGIES.keys())
chosen_ideologies = random.sample(all_ideologies, num_factions)
```

Replace the `for i, ideology_name in enumerate(PROTOTYPE_IDEOLOGIES)` loop to use `chosen_ideologies`.

- [ ] **Step 4: Remove `PROTOTYPE_IDEOLOGIES` from `mechanics/ideologies.py`**

Delete the line and remove its import from `main.py`.

- [ ] **Step 5: Update startup print to show chosen ideologies**

Replace `print(f"  Factions   : {', '.join(PROTOTYPE_IDEOLOGIES)}")` with:
```python
print(f"  Factions   : {num_factions} — {', '.join(chosen_ideologies)}")
```

- [ ] **Step 6: Verify**

```bash
python main.py --eras 1 --factions 3 2>&1 | head -20
```
Expected: 3 randomly chosen ideologies

- [ ] **Step 7: Commit**

```bash
git add main.py config.py mechanics/ideologies.py
git commit -m "Randomize 2-5 factions from all 16 ideologies"
```

---

### Task 6: Integration test and push

- [ ] **Step 1: Full import check**

```bash
python -c "from main import main; print('all imports ok')"
```

- [ ] **Step 2: Run a quick 1-era simulation**

```bash
python main.py --eras 1 2>&1 | tail -30
```
Verify: random faction count, preferences visible in reconsideration prompts, VP totals correct.

- [ ] **Step 3: Push all commits**

```bash
git push
```
