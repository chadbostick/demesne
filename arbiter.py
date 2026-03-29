from __future__ import annotations
import json
import os
import random
from typing import TYPE_CHECKING

import config
from utils import pause
from mechanics.dice import roll
from mechanics.cultures import CULTURE_TREE, can_purchase, get_cost
from mechanics.strategies import (
    BASE_STRATEGIES, award_tokens, lookup_payout,
    apply_make_exchange, BASE_MAKE_OPTIONS,
    CULTURE_STRATEGY_COLOR,
    roll_strategy_dice, resolve_strategy_rolls, make_receive_for_level,
)
from mechanics.worldbuilding import CHALLENGE_EVENTS, BOON_TABLE
from mechanics.cultures import CULTURE_TREE
from mechanics.scoring import score_all_factions
from mechanics.ideologies import IDEOLOGIES
from mechanics.token_economy import (
    pick_best_strategy, should_make_instead, pick_make_receive_distribution,
    pick_bonus_colors, can_afford, deduct_tokens, affordable_upgrades,
    apply_culture_economy, find_make_option_by_color,
    CULTURE_ECONOMY_EFFECTS,
)
from mechanics.cooperation import (
    cooperative_upgrades, score_coop_option, faction_benefits_from,
    pick_preferred_option,
)
from state.memory import MemoryContext

if TYPE_CHECKING:
    from state.settlement import SettlementState
    from agents.faction import FactionAgent
    from agents.gm import GMAgent
    from phases.engine import PhaseEngine
    from logger import ActionLogger



# Economic effects of culture options

class Arbiter:
    """
    Deterministic process controller for the Fantasy Settlement Creation Game.
    No LLM calls — manages era flow, agent dispatch, token economy, and state updates.
    """

    def __init__(
        self,
        phase_engine: "PhaseEngine",
        faction_agents: list["FactionAgent"],
        gm_agent: "GMAgent",
        logger: "ActionLogger",
        memory_window: int | None = None,
    ) -> None:
        self._phases = phase_engine
        self._factions = faction_agents
        self._gm = gm_agent
        self._logger = logger
        self._verbose = config.VERBOSE
        self._memory_window = memory_window or config.MEMORY_WINDOW
        self._era_chronicle: list[str] = []  # short summary per completed era
        self._era_names: list[str] = []       # era period names used so far
        self._last_faction_narratives: dict[str, str] = {}  # faction_name → last narrative
        self._previous_challenges: list[str] = []  # challenge events from past eras

    def _try_add_faction(self, state: "SettlementState", trigger: str, culture_level: int = 0) -> None:
        """Attempt to add a new faction if the trigger is in the configured modes."""
        if trigger not in config.ADD_FACTIONS_MODES:
            return
        # perLevel: only trigger on FIRST time settlement reaches L1, L2, or L3
        if trigger == "perLevel":
            milestones = state._data.setdefault("_level_milestones_triggered", [])
            if culture_level in milestones or culture_level < 1:
                return
            milestones.append(culture_level)
        ideology = state.pop_available_ideology()
        if not ideology:
            return
        self._add_new_faction(state, ideology)

    def _try_remove_faction(
        self, state: "SettlementState", trigger: str,
        scapegoat_name: str | None = None,
        beneficiaries: list[str] | None = None,
        culture_level: int = 0,
    ) -> None:
        """Attempt to remove a faction based on the trigger mode."""
        if trigger not in config.REMOVE_FACTIONS_MODES:
            return
        if len(state.factions) <= 2:
            return  # never go below 2 factions

        if trigger == "noInfluence":
            # Remove all factions below 0 — tokens to faction needing colors most
            eliminated = [f for f in state.factions if f.get("influence", 0) < 0]
            for f in eliminated:
                best_recipient = self._faction_needing_colors_most(state, f["tokens"], exclude=f["name"])
                self._eliminate_and_redistribute(state, f["name"], best_recipient)

        elif trigger == "perFail":
            if not scapegoat_name:
                return
            # Tokens go to factions that did NOT contribute (beneficiaries)
            self._eliminate_and_redistribute(state, scapegoat_name, beneficiaries)

        elif trigger == "perLeaderChange":
            if not scapegoat_name:
                return
            # Tokens go to the new leader (beneficiaries[0])
            recipient = beneficiaries[0] if beneficiaries else None
            self._eliminate_and_redistribute(state, scapegoat_name, recipient)

        elif trigger == "perLevel":
            milestones = state._data.setdefault("_level_milestones_removed", [])
            if culture_level in milestones or culture_level < 1:
                return
            milestones.append(culture_level)
            # Weakest faction eliminated, tokens to the purchaser
            weakest = min(state.factions, key=lambda f: f.get("influence", 0))
            purchaser = beneficiaries[0] if beneficiaries else None
            if weakest["name"] != purchaser:
                self._eliminate_and_redistribute(state, weakest["name"], purchaser)

    def _eliminate_and_redistribute(
        self, state: "SettlementState", victim_name: str,
        recipients: str | list[str] | None,
    ) -> None:
        """Remove a faction and redistribute their tokens."""
        if len(state.factions) <= 2:
            return
        try:
            victim = state.get_faction(victim_name)
        except KeyError:
            return
        victim_tokens = dict(victim.get("tokens", {}))
        total_tokens = sum(victim_tokens.values())

        # Normalize recipients to a list
        if isinstance(recipients, str):
            recipients = [recipients]
        if not recipients:
            recipients = [f["name"] for f in state.factions if f["name"] != victim_name]
        recipients = [r for r in recipients if r != victim_name]
        if not recipients:
            return

        # Distribute tokens
        if len(recipients) == 1:
            # All tokens to single recipient
            r = state.get_faction(recipients[0])
            for c, n in victim_tokens.items():
                r["tokens"][c] = r["tokens"].get(c, 0) + n
            state.update_faction_tokens(recipients[0], r["tokens"])
            self._vprint(f"    [{recipients[0]} absorbs {total_tokens} tokens from {victim_name}]")
        else:
            # Split evenly across recipients, remainder to first
            per_recipient: dict[str, dict[str, int]] = {r: {} for r in recipients}
            for c, n in victim_tokens.items():
                if n <= 0:
                    continue
                share = n // len(recipients)
                remainder = n % len(recipients)
                for i, r in enumerate(recipients):
                    amount = share + (1 if i < remainder else 0)
                    if amount > 0:
                        per_recipient[r][c] = amount
            for r_name, r_tokens in per_recipient.items():
                if r_tokens:
                    f = state.get_faction(r_name)
                    for c, n in r_tokens.items():
                        f["tokens"][c] = f["tokens"].get(c, 0) + n
                    state.update_faction_tokens(r_name, f["tokens"])
            self._vprint(f"    [{victim_name}'s {total_tokens} tokens distributed to {', '.join(recipients)}]")

        # Eliminate
        print(f"\n    *** {victim_name} has been scattered — their people absorbed by the settlement ***")
        state.eliminate_faction(victim_name)
        self._factions = [a for a in self._factions if a.faction_data["name"] != victim_name]
        self._logger.log_event("faction_eliminated", era=state.era, faction=victim_name,
            trigger="removal", tokens_redistributed=victim_tokens, recipients=recipients)

    def _faction_needing_colors_most(self, state: "SettlementState", tokens: dict, exclude: str = "") -> str:
        """Find the faction with the largest total shortfall that could use these token colors."""
        best_name = None
        best_match = 0
        for f in state.factions:
            if f["name"] == exclude:
                continue
            # How many of the victim's tokens match this faction's shortfalls?
            goal_costs = f.get("goal_costs", {})
            aggregate = goal_costs.get("aggregate", {})
            match = 0
            for c, n in tokens.items():
                need = max(0, aggregate.get(c, 0) - f["tokens"].get(c, 0))
                match += min(n, need)
            if match > best_match:
                best_match = match
                best_name = f["name"]
        return best_name or (state.factions[0]["name"] if state.factions else "")

    def _add_new_faction(self, state: "SettlementState", ideology: str) -> None:
        """Add a new faction mid-game."""
        from mechanics.faction_utils import build_faction_data, compute_coalitions, compute_goal_costs
        from agents.faction import FactionAgent
        from mechanics.worldbuilding import DND5_RACES
        from mechanics.strategies import STRATEGIC_STANCES

        # Build faction data
        faction_data = build_faction_data(ideology, len(state.factions))
        faction_data["current_stance"] = random.choice(list(STRATEGIC_STANCES.keys()))
        species = random.choice(DND5_RACES)
        faction_data["species"] = species

        # Roll initiative → starting influence
        init_roll = roll(20)
        faction_data["influence"] = init_roll

        # Starting token bonus: 1d3-1 per era elapsed, distributed toward goal needs
        bonus_per_era = max(0, roll(3) - 1)
        total_bonus = bonus_per_era * state.era
        if total_bonus > 0:
            # Compute which colors this faction actually needs
            from mechanics.faction_utils import compute_goal_costs
            goal_costs = compute_goal_costs(faction_data["goals"], state.cultures)
            needed_colors: dict[str, int] = {}
            for goal_key in ["primary", "secondary_0", "secondary_1", "tertiary"]:
                gd = goal_costs.get(goal_key, {})
                for c, n in gd.get("total_cost", {}).items():
                    needed_colors[c] = needed_colors.get(c, 0) + n
            # Distribute tokens weighted toward needed colors
            if needed_colors:
                # Build weighted pool: each needed color appears proportionally
                weighted_pool = []
                for c, n in needed_colors.items():
                    weighted_pool.extend([c] * max(1, n))
                for _ in range(total_bonus):
                    c = random.choice(weighted_pool)
                    faction_data["tokens"][c] = faction_data["tokens"].get(c, 0) + 1
            else:
                _all_colors = ["red", "blue", "green", "orange", "pink"]
                for _ in range(total_bonus):
                    c = random.choice(_all_colors)
                    faction_data["tokens"][c] = faction_data["tokens"].get(c, 0) + 1
            self._vprint(f"    [Starting bonus: {total_bonus} tokens ({bonus_per_era}/era × {state.era} eras)]")

        # Add to state
        state.add_faction(faction_data)
        faction = state.get_faction(faction_data["name"])

        # Create agent
        agent = FactionAgent(faction_data)
        agent.faction_data = faction
        self._factions.append(agent)

        # LLM introduction
        location = state._data.get("location", "")
        terrain = state._data.get("terrain", "")
        neighbors = [f for f in state.factions if f["name"] != faction_data["name"]]
        print(f"\n  ── A New Faction Arrives ──")
        intro_output = agent.introduce_faction(
            location, terrain, neighbors,
            arriving=True,
            settlement_context=state.summary()[:500],
        )
        intro = agent.parse_faction_intro(intro_output)
        if intro:
            old_name = faction_data["name"]
            new_name = intro.get("faction_name", old_name)
            org_type = intro.get("organization_type", "Guild")
            description = intro.get("description", "")
            faction["name"] = new_name
            faction["organization_type"] = org_type
            faction["description"] = description
            agent.faction_data = faction
            agent.role = f"faction_{new_name.lower().replace(' ', '_')}"
            state.register_name(new_name)

            founding_leader = intro.get("founding_leader", "")
            if founding_leader:
                state.add_historical_figure({
                    "name": founding_leader, "role": "founder",
                    "faction": new_name, "era": state.era,
                    "deed": f"Led {new_name} to settle in {state._data['name']}",
                    "status": "legendary",
                })
                state.register_name(founding_leader)

            print(f"\n  **{new_name} ({ideology} {species})**")
            if founding_leader:
                print(f"  Led by {founding_leader}")
            if description:
                print(f"  {description}")
        else:
            new_name = faction_data["name"]
            print(f"\n  **{new_name} ({ideology} {species})**")

        # Update initiative order by influence
        new_order = sorted(
            [f["name"] for f in state.factions],
            key=lambda n: state.get_faction(n).get("influence", 0),
            reverse=True,
        )
        state._data["initiative_order"] = new_order
        for a in self._factions:
            a.faction_data = state.get_faction(a.faction_data["name"])

        # Recompute coalitions for ALL factions
        coalition_map = compute_coalitions(state.factions)
        for f in state.factions:
            f["coalition_plan"] = coalition_map.get(f["name"], {})
        for a in self._factions:
            a.faction_data = state.get_faction(a.faction_data["name"])

        # Score VP immediately (existing cultures may satisfy goals)
        from mechanics.scoring import score_faction
        vp = score_faction(faction, state.cultures)
        faction["victory_points"] = vp
        if vp > 0:
            self._vprint(f"    [{new_name} arrives with {vp} VP from existing cultures]")

        self._logger.log_event("faction_arrived", era=state.era,
            faction=new_name, ideology=ideology, species=species,
            influence=init_roll, starting_tokens=dict(faction["tokens"]),
            starting_vp=vp)
        self._vprint(f"    [{new_name} joins with influence {init_roll}, {sum(faction['tokens'].values())} tokens, {vp} VP]")

    def _vprint(self, *args, **kwargs):
        """Print only if verbose mode is on."""
        if self._verbose:
            print(*args, **kwargs)

    def _faction_label(self, faction: dict) -> str:
        """Format faction name with ideology and species for display."""
        ideology = faction.get("ideology", "")
        species = faction.get("species", "")
        name = faction.get("name", "")
        if ideology and species:
            return f"{name} ({ideology} {species})"
        return name

    # ── Public API ────────────────────────────────────────────────────────────

    def run(
        self,
        state: "SettlementState",
        max_eras: int,
        output_dir: str,
    ) -> "SettlementState":
        os.makedirs(output_dir, exist_ok=True)
        while not state.game_over and state.era < max_eras:
            state.increment_era()
            # Add new faction if perEra mode (skip era 1 — initial factions already exist)
            if state.era > 1:
                self._try_add_faction(state, "perEra")
            # Grab this era's inspiration seed (seeds 2-6 for eras 1-5)
            self._era_inspiration = state.get_next_seed(used_in=f"era_{state.era}")
            stage = state.settlement_stage()
            print(f"\n{'='*60}\n  Age {state.era} — {state._data['name']} ({stage})\n{'='*60}")
            era_outputs = self.run_era(state)
            self._write_era_files(output_dir, state, era_outputs)
            self.check_victory(state)
        return state

    def run_era(self, state: "SettlementState") -> list[dict]:
        era_outputs: list[dict] = []
        for phase in self._phases:
            outputs = self._dispatch_phase(phase, state)
            era_outputs.extend(outputs)
        return era_outputs

    # ── Phase dispatch ────────────────────────────────────────────────────────

    def _dispatch_phase(self, phase, state: "SettlementState") -> list[dict]:
        if phase.name == "strategy":
            outputs = self._run_strategy_phase(state)
        elif phase.name == "investment":
            outputs = self._run_investment_phase(state)
        elif phase.name == "challenge":
            outputs = self._run_challenge_phase(state)
        elif phase.name == "end_of_era":
            outputs = self._run_end_of_era_phase(state)
        else:
            return []
        return outputs

    # ── Strategy Phase ────────────────────────────────────────────────────────

    def _run_strategy_phase(self, state: "SettlementState") -> list[dict]:
        print(f"\n  ── The People Take Action ──")
        outputs = []
        _all_colors = ["red", "blue", "green", "orange", "pink"]
        _faction_summaries: list[dict] = []
        _faction_narratives: list[str] = []

        for agent in self._factions_in_initiative_order(state):
            fname = agent.faction_data["name"]
            faction = state.get_faction(fname)
            tokens = dict(faction["tokens"])

            # ── Decide strategy ────────────────────────────────────────────
            # 1. Pick target goal (determines which purchase we're working toward)
            strategy, color, pursuit_reason = pick_best_strategy(faction, state)

            # 2. Check if make exchange enables that goal's next purchase
            make_override = should_make_instead(faction, state)
            if make_override:
                stance = "make"
                color = make_override["exchange_color"]
                strategy = "make"
                _make_receive_color = make_override["receive_color"]
                _make_give = make_override["give"]
                faction["needs_reconsideration"] = False
                self._vprint(f"    [{fname} → MAKE: {make_override['reason']}]")
            else:
                stance = f"pursuing_{color}"
                _make_receive_color = None
                _make_give = None
                self._vprint(f"    [{fname} → {strategy} ({color}): {pursuit_reason}]")

            color_level = state.get_color_level(color)
            cu = state.color_upgrades[color]
            custom_strategy_name = cu["strategy_name"]
            custom_make_name = cu["make_name"]

            # Make stance: attempt exchange first, fall back to normal if insufficient
            if stance == "make":
                make_opt = find_make_option_by_color(color)
                if make_opt:
                    give = _make_give or tokens.get(color, 0)  # use calculated amount, or all if no override
                    receive = make_receive_for_level(color_level, give)
                    if give >= 1:
                        receive_colors = pick_make_receive_distribution(
                            faction, tokens, color, receive, state
                        )
                        tokens = apply_make_exchange(tokens, color, give, receive, receive_colors)
                        tok_str = ", ".join(f"{c}:{n}" for c, n in tokens.items())
                        from collections import Counter
                        recv_counts = Counter(receive_colors)
                        recv_str = ", ".join(f"{n} {c}" for c, n in recv_counts.items())
                        self._vprint(
                            f"    {fname} [{custom_make_name}] gave {give} {color},"
                            f" received {recv_str}"
                        )
                        self._vprint(f"      [Tokens now: {tok_str}]")
                        state.update_faction_tokens(fname, tokens)

                        # Influence gain: net tokens earned if 2x+ return
                        if receive >= give * 2:
                            make_influence = receive - give
                            faction["influence"] = faction.get("influence", 0) + make_influence
                            self._vprint(f"      [Influence: {faction['influence']} (+{make_influence} from make)]")

                        self._logger.log_event("make_exchange", era=state.era,
                            faction=fname, give_color=color, give_amount=give,
                            receive_colors=dict(Counter(receive_colors)), receive_amount=receive,
                            tokens_after=dict(tokens), influence=faction.get("influence", 0))

                        # LLM describes the structure
                        self._vprint(f"    → {fname} describing their construction...", end="", flush=True)
                        make_out = agent.run_make_narrative(
                            era=state.era,
                            make_type=custom_make_name,
                            location=state._data.get("location", ""),
                            terrain=state._data.get("terrain", ""),
                            settlement_stage=state.settlement_stage(),
                            cultures=state.cultures,
                            existing_landmarks=state._data.get("landmarks", []),
                        )
                        self._vprint(" done.\n")
                        structure = agent.parse_make_structure(make_out)
                        if structure:
                            s_name = structure.get("name", custom_make_name)
                            s_loc = structure.get("location", "")
                            s_desc = structure.get("description", "")
                            s_purpose = structure.get("purpose", "")
                        else:
                            s_name = custom_make_name
                            s_loc = ""
                            s_desc = ""
                            s_purpose = ""

                        state.add_landmark(s_name, f"{s_desc} {s_purpose}".strip(), fname)
                        self._logger.log_event("structure_built", era=state.era,
                            faction=fname, name=s_name, location=s_loc,
                            description=s_desc, purpose=s_purpose)
                        print(f"\n  **{self._faction_label(faction)} builds {s_name}**")
                        if s_loc:
                            print(f"  {s_loc}")
                        if s_desc:
                            print(f"  {s_desc}")
                        if s_purpose:
                            print(f"  {s_purpose}")
                        self._logger.log(make_out)
                        outputs.append(make_out.to_dict())
                        narrative_text = f"{s_desc} {s_purpose}".strip() or s_name
                        _faction_summaries.append({"name": fname, "activity": f"building ({s_name})", "tokens_earned": 0})
                        _faction_narratives.append(narrative_text)
                        pause(f"  ── {fname} done. Press Space/Enter to continue or Esc to quit ──", era=state.era)
                        continue
                # Fall through to normal execution if make not possible

            all_rolls = roll_strategy_dice(color_level)
            base_count, bonus_count = resolve_strategy_rolls(all_rolls)
            dice_display = (
                str(all_rolls[0]) if len(all_rolls) == 1
                else f"{len(all_rolls)}d20 {all_rolls}"
            )
            if bonus_count > 0:
                bonus_colors = pick_bonus_colors(faction, tokens, color, bonus_count, state)
                tokens = award_tokens(tokens, color, base_count, bonus_count, bonus_colors)
                bonus_note = f" + {bonus_count} " + ", ".join(bonus_colors)
            else:
                tokens = award_tokens(tokens, color, base_count, 0)
                bonus_note = ""
            tokens_earned = base_count + bonus_count
            self._vprint(f"    {fname} [{stance}→{custom_strategy_name}] rolled {dice_display} → +{base_count} {color}{bonus_note}")

            tok_str = ", ".join(f"{c}:{n}" for c, n in tokens.items())
            self._vprint(f"      [Tokens now: {tok_str}]")
            state.update_faction_tokens(fname, tokens)
            # Add net tokens earned to influence
            faction["influence"] = faction.get("influence", 0) + tokens_earned
            self._vprint(f"      [Influence: {faction['influence']} (+{tokens_earned})]")

            self._logger.log_event("strategy_roll", era=state.era,
                faction=fname, stance=stance, strategy=custom_strategy_name,
                color=color, rolls=all_rolls, base_earned=base_count,
                bonus_earned=bonus_count,
                bonus_colors=bonus_colors if bonus_count > 0 else [],
                tokens_after=dict(tokens), influence=faction["influence"])

            _STRATEGY_ACTIVITY = {
                "pray": "prayer and devotion", "discuss": "discourse and debate",
                "lead": "leadership and rallying", "organize": "planning and coordination",
                "forage": "scouting and gathering",
            }
            _faction_summaries.append({
                "name": fname,
                "label": self._faction_label(faction),
                "activity": _STRATEGY_ACTIVITY.get(strategy, strategy),
                "tokens_earned": tokens_earned,
            })

        # ── Batched strategy narration (1 LLM call for all factions) ──────────
        if _faction_summaries:
            self._vprint(f"\n    → GM chronicling the era's efforts...", end="", flush=True)
            gm_output = self._gm.narrate_strategy_phase(
                round_num=state.era,
                state_summary=state.summary(),
                faction_summaries=_faction_summaries,
                mode="summary",
            )
            self._vprint(" done.\n")
            print(gm_output.content)
            self._logger.log(gm_output)
            outputs.append(gm_output.to_dict())
            self._last_strategy_summary = gm_output.content[:400]

        return outputs

    def _extract_historical_figure(self, text: str, faction: str, era: int, role: str) -> dict | None:
        """Extract a historical figure from narration text containing 'HISTORICAL FIGURE: name — deed'."""
        import re
        match = re.search(r"HISTORICAL FIGURE:\s*(.+?)\s*[—–-]\s*(.+)", text)
        if match:
            figure = {
                "name": match.group(1).strip(),
                "deed": match.group(2).strip(),
                "faction": faction,
                "era": era,
                "role": role,
                "status": "legendary",
            }
            return figure
        return None

    def _run_investment_phase(self, state: "SettlementState") -> list[dict]:
        print(f"\n  ── Growth and Development ──")
        outputs = []
        any_purchase_made = False
        for agent in self._factions_in_initiative_order(state):
            fname = agent.faction_data["name"]
            faction = state.get_faction(fname)
            tokens = dict(faction["tokens"])

            affordable = affordable_upgrades(tokens, state.cultures)
            if not affordable:
                self._vprint(f"\n    [SKIP: {fname} cannot afford any upgrade]")
                continue

            context = MemoryContext.build(state, self._logger, self._memory_window, fname)
            self._vprint(f"\n    → {fname} deciding investments...", end="", flush=True)
            output = agent.run_investment(context, state.era, state.cultures)
            self._vprint(" done.\n")

            choice = agent.parse_investment_choice(output)
            purchased_any = False

            for purchase in choice.get("purchases", []):
                cat = purchase.get("category", "").lower().replace(" ", "_")
                lvl = purchase.get("level")
                option = purchase.get("option", "")

                if cat not in CULTURE_TREE:
                    self._vprint(f"      [SKIP: unknown category '{cat}']")
                    continue
                if not can_purchase(cat, lvl, state.cultures):
                    self._vprint(f"      [SKIP: prerequisite not met for {cat} L{lvl}]")
                    continue

                cost = get_cost(cat, lvl)
                if not can_afford(tokens, cost):
                    self._vprint(f"      [SKIP: cannot afford {cat} L{lvl}]")
                    continue

                valid_opts = [o.lower() for o in CULTURE_TREE[cat]["levels"][lvl]["options"]]
                if option.lower() not in valid_opts:
                    self._vprint(f"      [SKIP: '{option}' not valid for {cat} L{lvl}]")
                    continue

                tokens = deduct_tokens(tokens, cost)
                state.apply_culture_upgrade(cat, lvl, option)
                apply_culture_economy(state, option)
                self._vprint(f"      [UNLOCKED: {cat} L{lvl} — {option}]")
                purchased_any = True
                any_purchase_made = True
                self._logger.log_event("culture_purchase", era=state.era,
                    faction=fname, category=cat, level=lvl, option=option,
                    cost=cost, tokens_after=dict(tokens), cooperative=False)
                self._try_add_faction(state, "perLevel", culture_level=lvl)
                self._try_remove_faction(state, "perLevel", culture_level=lvl, beneficiaries=[fname])

                new_strat = f"{cat}_strategy"
                new_make = f"{cat}_make"
                state.unlock_strategy(new_strat)
                state.unlock_make_option(new_make)

                # GM chronicles this cultural shift (includes historical figure)
                self._vprint(f"\n    → GM chronicling cultural shift...", end="", flush=True)
                culture_narrative = self._gm.narrate_culture_purchase(
                    state.era, cat, option, fname, state._data["name"]
                )
                self._vprint(" done.\n")

                # Extract historical figure from narration
                figure = self._extract_historical_figure(culture_narrative.content, fname, state.era, "reformer")
                if figure:
                    state.add_historical_figure(figure)
                    state.register_name(figure["name"])
                    self._vprint(f"      [Historical figure: {figure['name']} — {figure['deed']}]")
                    self._logger.log_event("historical_figure", **figure)
                print(culture_narrative.content)
                self._logger.log(culture_narrative)
                outputs.append(culture_narrative.to_dict())

                # Found a new place (village/town/city-state)
                self._found_place(state, lvl, cat, option, agent, [fname], outputs)

                # Check if this purchase raised a color's level → rename
                color = CULTURE_TREE[cat]["unlocks_color"]
                self._check_color_level_up(state, color, cat, option, agent, outputs)

            if purchased_any:
                self._vprint(output.content)
                self._logger.log(output)
                outputs.append(output.to_dict())
                tok_str = ", ".join(f"{c}:{n}" for c, n in tokens.items())
                self._vprint(f"      [Tokens now: {tok_str}]")
                state.update_faction_tokens(fname, tokens)
                pause(f"  ── {fname} done. Press Space/Enter to continue or Esc to quit ──", era=state.era)
            else:
                tok_str = ", ".join(f"{c}:{n}" for c, n in tokens.items())
                self._vprint(f"      [No purchases made. Tokens: {tok_str}]")
                state.update_faction_tokens(fname, tokens)

        # Reconsideration trigger
        if any_purchase_made:
            for f in state.factions:
                f["needs_reconsideration"] = True
            self._vprint("\n    [Reconsideration triggered: culture purchase this era]")

        # Cooperative purchase round
        coop_purchased = self._attempt_cooperative_purchases(state)
        if coop_purchased:
            any_purchase_made = True
            # Re-trigger reconsideration if not already set
            for f in state.factions:
                f["needs_reconsideration"] = True
            self._vprint("\n    [Reconsideration triggered: cooperative purchase this era]")

        # Recalculate VP for all factions
        from mechanics.scoring import option_is_unlocked
        scores = score_all_factions(state.factions, state.cultures)
        self._vprint("\n    VP totals:")
        for faction in state.factions:
            fname = faction["name"]
            vp = scores[fname]
            state.update_faction_vp(fname, vp)
            goals = faction.get("goals", {})
            notes = []
            # Primary goal progress
            p = goals.get("primary", {})
            p_cat = p.get("category", "")
            p_lvl = p.get("level", 0)
            p_opt = p.get("option", "")
            if p_cat and p_lvl:
                if option_is_unlocked(state.cultures, p_cat, p_lvl, p_opt):
                    notes.append(f"primary ✓ {p_opt} (+30 VP)")
                else:
                    cur_lvl = state.cultures.get(p_cat, {}).get("level", 0)
                    notes.append(f"primary needs {p_cat} L{p_lvl} '{p_opt}' (currently L{cur_lvl})")
            # Secondary goal progress
            for i, s in enumerate(goals.get("secondary", []), 1):
                s_cat = s.get("category", "")
                s_lvl = s.get("level", 0)
                s_opt = s.get("option", "")
                if s_cat and s_lvl:
                    if option_is_unlocked(state.cultures, s_cat, s_lvl, s_opt):
                        notes.append(f"secondary{i} ✓ {s_opt} (+15 VP)")
                    else:
                        cur_lvl = state.cultures.get(s_cat, {}).get("level", 0)
                        notes.append(f"secondary{i} needs {s_cat} L{s_lvl} '{s_opt}' (L{cur_lvl})")
            # Tertiary progress
            t = goals.get("tertiary", {})
            t_cat = t.get("category", "")
            if t_cat:
                t_lvl = state.cultures.get(t_cat, {}).get("level", 0)
                if t_lvl > 0:
                    notes.append(f"tertiary {t_cat} L{t_lvl} (+{t_lvl * 10} VP)")
                else:
                    notes.append(f"tertiary {t_cat} (L0, no VP yet)")
            note_str = f"  [{'; '.join(notes)}]" if notes else ""
            self._vprint(f"      {fname}: {vp} VP{note_str}")

        self._logger.log_event("vp_update", era=state.era, scores=scores,
            cultures=state.to_dict()["cultures"],
            factions=[{"name": f["name"], "tokens": f["tokens"], "vp": f["victory_points"]} for f in state.factions])

        return outputs

    def _found_place(
        self,
        state: "SettlementState",
        level: int,
        category: str,
        option: str,
        founder_agent: "FactionAgent",
        founder_names: list[str],
        outputs: list[dict],
    ) -> None:
        """After a culture purchase, found a new place (village/town/city-state)."""
        from state.settlement import SettlementState
        tier = SettlementState.TIER_FOR_LEVEL.get(level, "village")
        existing_places = state._data.get("places", [])

        # Build tier context
        count = state.count_places_by_tier(tier)
        if level == 1:
            if count == 0:
                tier_context = (
                    "The scattered camps are coalescing. For the first time, people are building "
                    "something permanent — the first village. This is the moment the settlement "
                    "stops being a collection of survivors and becomes a community."
                )
            else:
                tier_context = (
                    f"A new village springs up alongside the {count} existing one{'s' if count > 1 else ''}. "
                    "The settlement's footprint is growing as people spread across the land."
                )
        elif level == 2:
            if count == 0:
                tier_context = (
                    "One of the villages has grown beyond its boundaries. What was once a cluster "
                    "of homes is now a large town — the center of trade and organization for the "
                    "surrounding communities. Roads converge here. Markets form."
                )
            else:
                tier_context = (
                    f"The settlement continues to urbanize. A village grows into a town, or an "
                    f"existing town gains a new borough or absorbs nearby farmsteads. "
                    f"There are now {count + 1} major population centers."
                )
        elif level == 3:
            if count == 0:
                tier_context = (
                    "The largest town has become a city-state — a sovereign power with walls, "
                    "institutions, and influence that extends far beyond the original 10km territory. "
                    "This is no longer a frontier settlement. It is a nation being born."
                )
            else:
                tier_context = (
                    f"The city-state's power grows. New vassal territories, conquered lands, or "
                    f"allied regions expand its reach. With {count + 1} major centers of power, "
                    f"this civilization is becoming one of the largest forces in the known world."
                )
        else:
            tier_context = ""

        culture_trigger = {"category": category, "level": level, "option": option}
        co_founders = [n for n in founder_names if n != founder_agent.faction_data["name"]]

        # Faction names the place
        self._vprint(f"\n    → {founder_agent.faction_data['name']} founding a {tier}...", end="", flush=True)
        name_output = founder_agent.name_place(
            era=state.era,
            tier=tier,
            tier_context=tier_context,
            culture_trigger=culture_trigger,
            location=state._data.get("location", ""),
            terrain=state._data.get("terrain", ""),
            existing_places=existing_places,
            co_founders=co_founders or None,
        )
        self._vprint(" done.\n")
        place_data = founder_agent.parse_place_name(name_output)
        place_name = place_data.get("name", f"Unnamed {tier.title()}")
        faction_details = place_data.get("details", "")
        self._vprint(f"    [{tier.upper()}: {place_name}]")
        if faction_details:
            print(f"      {faction_details}")
        self._logger.log(name_output)
        outputs.append(name_output.to_dict())

        # GM describes how it fits into the landscape
        self._vprint(f"\n    → GM mapping the new {tier}...", end="", flush=True)
        gm_output = self._gm.narrate_place_founding(
            round_num=state.era,
            place_name=place_name,
            tier=tier,
            tier_context=tier_context,
            faction_details=faction_details,
            culture_trigger=culture_trigger,
            state_summary=state.summary(),
            existing_places=existing_places,
        )
        self._vprint(" done.\n")
        gm_description = gm_output.content
        print(gm_description)
        self._logger.log(gm_output)
        outputs.append(gm_output.to_dict())

        # Store the place
        place = {
            "name": place_name,
            "tier": tier,
            "founded_era": state.era,
            "founded_by": founder_names,
            "culture_trigger": culture_trigger,
            "faction_details": faction_details,
            "gm_description": gm_description,
        }
        state.add_place(place)
        state.register_name(place_name)
        self._logger.log_event("place_founded", era=state.era, **place)

    def _check_color_level_up(
        self,
        state: "SettlementState",
        color: str,
        category: str,
        option: str,
        buyer_agent: "FactionAgent",
        outputs: list[dict],
    ) -> None:
        """
        After a culture purchase, check if the color's max level increased.
        If yes, fire the rename LLM and persist new names.
        """
        if not state.advance_color_level(color):
            return

        new_level = state.get_color_level(color)
        cu = state.color_upgrades[color]
        old_strategy = cu["strategy_name"]
        old_make = cu["make_name"]

        self._vprint(
            f"\n    → {buyer_agent.faction_data['name']} naming the new {color} strategy "
            f"(L{new_level} culture)...",
            end="", flush=True,
        )
        rename_out = buyer_agent.run_rename_strategy(
            state.era, color, category, option, old_strategy, old_make
        )
        self._vprint(" done.")

        choice = buyer_agent.parse_rename_choice(rename_out)
        new_strat = choice.get("strategy_name", "").strip() or old_strategy
        new_make_n = choice.get("make_name", "").strip() or old_make

        state.set_color_names(color, new_strat, new_make_n)
        self._vprint(
            f"      [{color.upper()} L{new_level}] Strategy renamed: {old_strategy!r} → {new_strat!r}"
        )
        self._vprint(
            f"      [{color.upper()} L{new_level}] Make renamed: {old_make!r} → {new_make_n!r}"
            f"  (exchange formula: spend N → receive N*{new_level + 1})"
        )
        self._logger.log(rename_out)
        outputs.append(rename_out.to_dict())

    def _factions_in_initiative_order(self, state: "SettlementState") -> list["FactionAgent"]:
        """Return faction agents sorted by initiative order (highest roll first)."""
        order = state.initiative_order
        if not order:
            return self._factions
        rank = {name: i for i, name in enumerate(order)}
        return sorted(self._factions, key=lambda a: rank.get(a.faction_data["name"], len(order)))

    def _attempt_cooperative_purchases(self, state: "SettlementState") -> bool:
        """
        After individual investments, attempt to pool tokens across all factions for
        upgrades no single faction could afford alone.
        Returns True if any cooperative purchase was made.
        """
        self._vprint(f"\n  [COOPERATIVE INVESTMENT]")
        made_any = False

        while True:
            coop = cooperative_upgrades(state.factions, state.cultures)
            if not coop:
                if not made_any:
                    self._vprint(f"    No cooperative opportunities this era.")
                break

            # Show all cooperative opportunities found
            self._vprint(f"\n    Opportunities found: {len(coop)}")
            for item in coop:
                cost_str = " + ".join(f"{n} {c}" for c, n in item["cost"].items())
                self._vprint(f"      {item['category']} L{item['level']} — {item['option']} (costs {cost_str})")

            # Show combined token pool
            combined: dict = {}
            for f in state.factions:
                for c, n in f["tokens"].items():
                    combined[c] = combined.get(c, 0) + n
            combined_str = ", ".join(f"{c}:{n}" for c, n in combined.items() if n > 0)
            self._vprint(f"    Combined token pool: [{combined_str}]")

            # Deduplicate: one attempt per category+level, pick the option with more faction support
            seen: set = set()
            unique_opps = []
            for item in coop:
                key = (item["category"], item["level"])
                if key in seen:
                    continue
                seen.add(key)
                # Find both options for this category+level
                options_at_level = [i for i in coop if i["category"] == item["category"] and i["level"] == item["level"]]
                if len(options_at_level) == 2:
                    best = pick_preferred_option(options_at_level, state.factions)
                    unique_opps.append(best)
                else:
                    unique_opps.append(item)

            # Sort by faction goal alignment — highest score first
            unique_opps.sort(
                key=lambda o: score_coop_option(o, state.factions), reverse=True
            )
            self._vprint(f"    Attempting {len(unique_opps)} unique category/level combinations (highest alignment first):")

            bought_one = False
            for opp in unique_opps:
                cat, lvl, option, cost = opp["category"], opp["level"], opp["option"], opp["cost"]
                cost_str = " + ".join(f"{n} {c}" for c, n in cost.items())
                other_option = next(
                    (o for o in CULTURE_TREE[cat]["levels"][lvl]["options"] if o != option), "?"
                )
                score = score_coop_option(opp, state.factions)
                other_score = score_coop_option(
                    {"category": cat, "level": lvl, "option": other_option}, state.factions
                )
                self._vprint(f"\n    Evaluating: {cat} L{lvl} — {option} (costs {cost_str})")
                self._vprint(f"      [Score: {option}={score}, {other_option}={other_score}]")

                # Show per-faction token state and willingness
                # A faction is willing if:
                # 1. The category is in their goals AND
                # 2. They can't afford the purchase solo (that's already filtered) AND
                # 3. Contributing tokens doesn't cost them more than buying solo would
                willing_factions = []
                for f in state.factions:
                    tok_str = ", ".join(f"{c}:{n}" for c, n in f["tokens"].items() if n > 0) or "none"
                    benefits = faction_benefits_from(f, cat)
                    if not benefits:
                        status = "unwilling (not their goal)"
                        self._vprint(f"      {f['name']}: [{tok_str}] — {status}")
                        continue

                    # Check culture preference for this specific option
                    prefs = f.get("culture_preferences", {}).get(cat, {}).get(lvl, {})
                    option_pref = prefs.get(option, "indifferent")
                    if option_pref == "antithesis":
                        status = f"REFUSES (antithesis to {option})"
                        self._vprint(f"      {f['name']}: [{tok_str}] — {status}")
                        continue

                    # Check if their contribution is less than what they'd pay solo
                    f_contribution = sum(
                        min(f["tokens"].get(c, 0), n) for c, n in cost.items()
                    )
                    solo_cost = sum(cost.values())
                    if f_contribution <= solo_cost:
                        pref_label = f", pref={option_pref}" if option_pref != "indifferent" else ""
                        status = f"willing (contributes {f_contribution}/{solo_cost}{pref_label})"
                        willing_factions.append(f)
                    else:
                        status = "unwilling (cheaper solo)"
                    self._vprint(f"      {f['name']}: [{tok_str}] — {status}")

                if not willing_factions:
                    self._vprint(f"    → SKIPPED — no faction has {cat} in their goals")
                    continue

                # Try to pool: only from willing factions, richest first
                pool: dict[str, dict[str, int]] = {}
                short_colors: list[str] = []

                for color, needed in cost.items():
                    remaining = needed
                    for f in sorted(willing_factions, key=lambda f: f["tokens"].get(color, 0), reverse=True):
                        available = f["tokens"].get(color, 0)
                        take = min(available, remaining)
                        if take > 0:
                            fname = f["name"]
                            contrib = pool.setdefault(fname, {})
                            contrib[color] = contrib.get(color, 0) + take
                            remaining -= take
                        if remaining == 0:
                            break
                    if remaining > 0:
                        short_colors.append(f"{remaining} {color}")

                if short_colors:
                    self._vprint(f"    → NOT PURCHASED — combined tokens still short: {', '.join(short_colors)}")
                    continue

                # Deduct pooled tokens
                for fname, contributions in pool.items():
                    faction = state.get_faction(fname)
                    tokens = dict(faction["tokens"])
                    for color, amount in contributions.items():
                        tokens[color] -= amount
                    state.update_faction_tokens(fname, tokens)

                state.apply_culture_upgrade(cat, lvl, option)
                apply_culture_economy(state, option)
                state.unlock_strategy(f"{cat}_strategy")
                state.unlock_make_option(f"{cat}_make")
                made_any = True
                bought_one = True
                self._try_add_faction(state, "perLevel", culture_level=lvl)
                # perLevel removal: top contributor absorbs weakest
                top_contrib = max(pool, key=lambda fn: sum(pool[fn].values())) if pool else None
                self._try_remove_faction(state, "perLevel", culture_level=lvl, beneficiaries=[top_contrib] if top_contrib else None)

                contribs = "; ".join(
                    f"{fn}: " + ", ".join(f"{n} {c}" for c, n in cols.items())
                    for fn, cols in pool.items()
                )
                self._vprint(f"    → PURCHASED: {cat} L{lvl} — {option}")
                self._vprint(f"      Contributors: {contribs}")
                self._logger.log_event("culture_purchase", era=state.era,
                    category=cat, level=lvl, option=option, cost=cost,
                    cooperative=True, contributors=pool)

                # GM chronicles this cultural shift
                self._vprint(f"\n    → GM chronicling cultural shift...", end="", flush=True)
                purchaser_str = " + ".join(pool.keys())
                culture_narrative = self._gm.narrate_culture_purchase(
                    state.era, cat, option, purchaser_str, state._data["name"]
                )
                self._vprint(" done.\n")
                print(culture_narrative.content)
                self._logger.log(culture_narrative)

                # Found a new place — largest contributor names it
                top_contributor = max(pool, key=lambda fn: sum(pool[fn].values()))
                top_agent = next(
                    (a for a in self._factions if a.faction_data["name"] == top_contributor),
                    self._factions[0],
                )
                self._found_place(state, lvl, cat, option, top_agent, list(pool.keys()), [])

                # Check if this purchase raised a color's level → rename
                color = CULTURE_TREE[cat]["unlocks_color"]
                self._check_color_level_up(state, color, cat, option, top_agent, [])

                pause("  ── Cooperative purchase made. Press Space/Enter to continue or Esc to quit ──", era=state.era)
                break  # restart outer while-loop with updated state

            if not bought_one:
                break

        return made_any

    def _run_challenge_phase(self, state: "SettlementState") -> list[dict]:
        print(f"\n  ── A Challenge Arises ──")
        outputs = []

        # Track leader before challenge for reconsideration trigger in end-of-era
        self._leader_before_challenge = state.leading_faction

        # Draw challenge event — offer GM a choice between random event and inspiration seed
        challenge_event = random.choice(CHALLENGE_EVENTS)
        era_seed = getattr(self, "_era_inspiration", None)
        difficulty = state.challenge_difficulty
        self._vprint(f"    Challenge event: {challenge_event}")
        if era_seed:
            self._vprint(f"    Inspiration alt: {era_seed[:60]}...")
        self._vprint(f"    Difficulty: {difficulty}")

        # GM narrates the challenge — picks the most compelling option
        self._vprint(f"\n    → GM describing the challenge...", end="", flush=True)
        prev_chron = self._era_chronicle[-1] if self._era_chronicle else None
        strat_sum = getattr(self, "_last_strategy_summary", None)
        gm_challenge = self._gm.narrate_challenge(
            context={},
            round_num=state.era,
            challenge_text=challenge_event,
            state_summary=state.summary(),
            previous_chronicle=prev_chron,
            strategy_summary=strat_sum,
            previous_challenges=list(self._previous_challenges) if self._previous_challenges else None,
            inspiration=era_seed,
        )
        self._vprint(" done.\n")
        challenge_text = gm_challenge.content
        print(challenge_text)
        self._logger.log(gm_challenge)
        outputs.append(gm_challenge.to_dict())
        self._previous_challenges.append(challenge_event)

        state.set_challenge(challenge_text)
        self._logger.log_event("challenge_drawn", era=state.era,
            event=challenge_event, difficulty=difficulty,
            leader=state.leading_faction)

        leading_name = state.leading_faction
        leader_faction = state.get_faction(leading_name)
        leader_agent = next(
            (a for a in self._factions if a.faction_data["name"] == leading_name), None
        )
        leader_vp = leader_faction["victory_points"]
        leader_vp_bonus = leader_vp // 10

        # ── Leader narrates their plan (before the roll) ──────────────────────
        leader_plan_text = ""
        if leader_agent:
            self._vprint(f"\n    → {leading_name} declaring their plan...", end="", flush=True)
            plan_output = leader_agent.run_challenge_plan(
                state.era, challenge_text, cultures=state.cultures
            )
            self._vprint(" done.\n")
            leader_plan_text = plan_output.content
            print(leader_plan_text)
            self._logger.log(plan_output)
            outputs.append(plan_output.to_dict())

        # ── Step 1: Leader donates (no LLM) ──────────────────────────────────
        # Early game: leaders are stingy (risk it with fewer tokens).
        # As settlement grows, leaders become more conservative (donate more).
        places_count = len(state._data.get("places", []))
        if places_count == 0:
            # Scattered camps: donate nothing unless absolutely necessary
            willingness = 0  # only donate if roll alone can't win
        elif places_count <= 2:
            # Early villages: donate minimally
            willingness = 1
        else:
            # Established settlement: donate what's needed
            willingness = 2

        needed = max(0, difficulty - 10 - leader_vp_bonus)
        leader_tokens = dict(leader_faction["tokens"])
        leader_total = sum(leader_tokens.values())

        if willingness == 0:
            # Scattered camps: only donate if difficulty is very high
            leader_donation = min(leader_total, max(0, needed - 5)) if needed > 5 else 0
        elif willingness == 1:
            # Early villages: donate at most 1
            leader_donation = min(leader_total, min(1, needed)) if needed > 0 else 0
        else:
            # Established: donate what's needed
            leader_donation = min(leader_total, max(1, needed)) if leader_total > 0 else 0

        can_solicit = leader_donation >= 1
        can_compel = leader_donation >= 2 and needed > leader_donation

        # Deduct from leader: drain largest color first
        if leader_donation > 0:
            sorted_colors = sorted(leader_tokens, key=lambda c: leader_tokens[c], reverse=True)
            remaining = leader_donation
            for c in sorted_colors:
                take = min(leader_tokens[c], remaining)
                leader_tokens[c] -= take
                remaining -= take
                if remaining == 0:
                    break
            state.update_faction_tokens(leading_name, leader_tokens)

        token_pool = leader_donation
        self._vprint(f"\n    [LEADER DONATION: {leading_name} donates {leader_donation} token(s)]")
        self._vprint(f"    [can_solicit={can_solicit}, can_compel={can_compel}]")

        donation_parts = [f"{leading_name} (leader): {leader_donation}"]

        # Build initiative rank map: rank 0 = highest initiative (leader), 1, 2, ...
        initiative_order = state.initiative_order
        rank_map = {name: i for i, name in enumerate(initiative_order)}
        last_rank = len(initiative_order) - 1
        non_leaders = [a for a in self._factions if a.faction_data["name"] != leading_name]

        # ── Step 2a: Compel ───────────────────────────────────────────────────
        if can_compel:
            self._vprint(f"\n    [COMPEL]")
            targets_sorted = sorted(
                non_leaders,
                key=lambda a: sum(state.get_faction(a.faction_data["name"])["tokens"].values()),
                reverse=True,
            )
            gap = needed - leader_donation
            compelled_pool = 0

            for target_agent in targets_sorted:
                if compelled_pool >= gap:
                    break
                tname = target_agent.faction_data["name"]
                target_rank = rank_map.get(tname, last_rank)

                leader_roll = roll(20)
                target_roll_raw = roll(20)
                target_roll_adj = target_roll_raw - target_rank

                tfaction = state.get_faction(tname)
                t_tokens = dict(tfaction["tokens"])
                t_total = sum(t_tokens.values())

                if target_roll_adj < leader_roll and t_total > 0:
                    # Force 1 token from largest color
                    for c in sorted(t_tokens, key=lambda c: t_tokens[c], reverse=True):
                        if t_tokens[c] > 0:
                            t_tokens[c] -= 1
                            break
                    state.update_faction_tokens(tname, t_tokens)
                    token_pool += 1
                    compelled_pool += 1
                    result_str = "forced"
                    donation_parts.append(f"{tname}: 1 (compelled)")
                else:
                    result_str = "refused"
                    donation_parts.append(f"{tname}: 0 (compel refused)")

                self._vprint(
                    f"      [COMPEL: {tname} rolled {target_roll_raw}-{target_rank}={target_roll_adj},"
                    f" leader rolled {leader_roll} → {result_str}]"
                )

        # ── Step 2b: Solicit ──────────────────────────────────────────────────
        elif can_solicit:
            self._vprint(f"\n    [SOLICIT]")
            leader_primary_option = leader_faction.get("goals", {}).get("primary", {}).get("option", "")

            for target_agent in non_leaders:
                tname = target_agent.faction_data["name"]
                tfaction = state.get_faction(tname)
                t_tokens = dict(tfaction["tokens"])
                t_total = sum(t_tokens.values())

                ideology = IDEOLOGIES.get(tfaction.get("ideology", ""), {})
                coop_mod = ideology.get("coop_modifier", 0)

                faction_enemy_option = tfaction.get("goals", {}).get("primary", {}).get("enemy_option", "")
                alignment_bonus = -1 if (faction_enemy_option and faction_enemy_option == leader_primary_option) else 0

                solicit_roll = roll(20) + coop_mod + alignment_bonus

                if solicit_roll >= 11 and t_total > 0:
                    for c in sorted(t_tokens, key=lambda c: t_tokens[c], reverse=True):
                        if t_tokens[c] > 0:
                            t_tokens[c] -= 1
                            break
                    state.update_faction_tokens(tname, t_tokens)
                    token_pool += 1
                    result_str = "gives"
                    donation_parts.append(f"{tname}: 1 (solicited)")
                else:
                    result_str = "refuses"
                    donation_parts.append(f"{tname}: 0 (solicited, refused)")

                self._vprint(f"      [SOLICIT: {tname} → {result_str} (roll {solicit_roll})]")

        else:
            self._vprint(f"    [Leader cannot solicit or compel — proceeding to resolution]")
            for a in non_leaders:
                donation_parts.append(f"{a.faction_data['name']}: 0 (no solicitation)")

        # ── Step 3: Resolve ───────────────────────────────────────────────────
        d20 = roll(20)
        total = d20 + token_pool + leader_vp_bonus
        success = total >= difficulty

        self._vprint(
            f"\n    [Roll: {d20} + {token_pool} tokens + {leader_vp_bonus} VP bonus = {total}"
            f" vs difficulty {difficulty} → {'SUCCESS' if success else 'FAILURE'}]"
        )

        self._logger.log_event("challenge_resolved", era=state.era,
            roll=d20, token_pool=token_pool, vp_bonus=leader_vp_bonus,
            total=total, difficulty=difficulty, success=success,
            donations=donation_parts)

        # Track which factions contributed tokens
        contributing_factions = set()
        for part in donation_parts:
            for f in state.factions:
                if f["name"] in part and ": 0" not in part:
                    contributing_factions.add(f["name"])

        if success:
            boons = self._roll_boons()
            for boon in boons:
                state.add_boon(boon)
            boon_str = " + ".join(boons)
            print(f"    [Boon: {boon_str}]")

            # Add new faction on success if perSuccess mode
            self._try_add_faction(state, "perSuccess")

            # Influence: leader +1d10, contributing factions each +1d6
            leader_inf_roll = roll(10)
            leader_faction["influence"] = leader_faction.get("influence", 0) + leader_inf_roll
            self._vprint(f"    [Influence: {leading_name} +{leader_inf_roll} (d10) → {leader_faction['influence']}]")
            for fname in contributing_factions:
                if fname == leading_name:
                    continue
                contrib_roll = roll(6)
                f = state.get_faction(fname)
                f["influence"] = f.get("influence", 0) + contrib_roll
                self._vprint(f"    [Influence: {fname} +{contrib_roll} (d6) → {f['influence']}]")

            # Token rewards on success: leader rolls 2d20, contributors roll 1d20
            _all_colors = ["red", "blue", "green", "orange", "pink"]
            self._vprint(f"\n    [VICTORY SPOILS]")

            # Leader: 2d20 → 1-2 tokens of any combination
            leader_tokens_dict = dict(leader_faction["tokens"])
            for i in range(2):
                r = roll(20)
                base, bonus = lookup_payout(r)
                earned = base + bonus
                if earned > 0:
                    reward_color = pick_bonus_colors(leader_faction, leader_tokens_dict, "", 1, state)[0]
                    leader_tokens_dict[reward_color] = leader_tokens_dict.get(reward_color, 0) + earned
                    self._vprint(f"    [{leading_name} rolled {r} → +{earned} {reward_color}]")
            state.update_faction_tokens(leading_name, leader_tokens_dict)
            leader_faction["influence"] = leader_faction.get("influence", 0) + sum(
                leader_tokens_dict[c] - leader_faction["tokens"].get(c, 0) for c in _all_colors
            )

            # Contributing factions: 1d20 → tokens of any color
            for fname in contributing_factions:
                if fname == leading_name:
                    continue
                f = state.get_faction(fname)
                f_tokens = dict(f["tokens"])
                r = roll(20)
                base, bonus = lookup_payout(r)
                earned = base + bonus
                if earned > 0:
                    reward_color = pick_bonus_colors(f, f_tokens, "", 1, state)[0]
                    f_tokens[reward_color] = f_tokens.get(reward_color, 0) + earned
                    self._vprint(f"    [{fname} rolled {r} → +{earned} {reward_color}]")
                    state.update_faction_tokens(fname, f_tokens)
                    f["influence"] = f.get("influence", 0) + earned

            challenge_result = {"success": True, "roll": d20, "total": total, "boons": boons}
        else:
            # Influence shift: leader -1d20, collaborators -1d6, non-collaborators +1d6
            self._vprint(f"\n    [INFLUENCE SHIFT — LEADERSHIP CRISIS]")
            leader_loss = roll(20)
            leader_faction["influence"] = leader_faction.get("influence", 0) - leader_loss
            self._vprint(f"    [Influence: {leading_name} -{leader_loss} (d20) → {leader_faction['influence']}]")

            for agent in self._factions:
                fname = agent.faction_data["name"]
                if fname == leading_name:
                    continue
                f = state.get_faction(fname)
                if fname in contributing_factions:
                    loss = roll(6)
                    f["influence"] = f.get("influence", 0) - loss
                    self._vprint(f"    [Influence: {fname} -{loss} (d6, collaborated) → {f['influence']}]")
                else:
                    gain = roll(6)
                    f["influence"] = f.get("influence", 0) + gain
                    self._vprint(f"    [Influence: {fname} +{gain} (d6, withheld) → {f['influence']}]")

            # Check for faction elimination
            # noInfluence: any faction below 0
            self._try_remove_faction(state, "noInfluence")

            # perFail: scapegoat = biggest contributor, or the leader if nobody contributed
            contributor_totals = {}
            for part in donation_parts:
                for f in state.factions:
                    if f["name"] in part and ": 0" not in part:
                        import re as _re
                        match = _re.search(r": (\d+)", part)
                        if match and f["name"] in part:
                            contributor_totals[f["name"]] = contributor_totals.get(f["name"], 0) + int(match.group(1))
            if contributor_totals:
                scapegoat = max(contributor_totals, key=contributor_totals.get)
            else:
                # Nobody contributed — the leader bears the blame
                scapegoat = leading_name
            non_contributors = [f["name"] for f in state.factions
                                if f["name"] not in contributing_factions and f["name"] != scapegoat]
            self._try_remove_faction(state, "perFail",
                scapegoat_name=scapegoat,
                beneficiaries=non_contributors if non_contributors else None)

            # New leader = highest influence
            if state.factions:
                new_leader_f = max(state.factions, key=lambda f: f.get("influence", 0))
                new_leader = new_leader_f["name"]
                state.set_leading_faction(new_leader)
                # Re-sort initiative order by influence
                new_order = sorted(
                    [f["name"] for f in state.factions],
                    key=lambda n: state.get_faction(n).get("influence", 0),
                    reverse=True,
                )
                state._data["initiative_order"] = new_order
                # Re-sync
                for agent in self._factions:
                    agent.faction_data = state.get_faction(agent.faction_data["name"])
                self._vprint(f"    [New leader: {new_leader} (influence {new_leader_f['influence']})]")
                inf_display = ", ".join(f"{n}({state.get_faction(n)['influence']})" for n in new_order)
                self._vprint(f"    [Influence order: {inf_display}]")
                self._logger.log_event("leadership_shift", era=state.era,
                    new_leader=new_leader, influence_order={n: state.get_faction(n)["influence"] for n in new_order})

                # perLeaderChange: outgoing leader eliminated, tokens to new leader
                if new_leader != leading_name:
                    self._try_remove_faction(state, "perLeaderChange",
                        scapegoat_name=leading_name,
                        beneficiaries=[new_leader])
            else:
                new_leader = "none"

            challenge_result = {"success": False, "roll": d20, "total": total, "new_leader": new_leader}

        state.advance_difficulty(failed=not success)
        self._vprint(f"    [Next difficulty: {state.challenge_difficulty}]")

        # ── Step 4: GM narrates the outcome ──────────────────────────────────
        donation_summary = "; ".join(donation_parts)
        self._vprint(f"\n    → GM chronicling the outcome...", end="", flush=True)
        outcome_output = self._gm.narrate_challenge_outcome(
            round_num=state.era,
            challenge_text=challenge_text,
            leader_plan=leader_plan_text,
            donation_summary=donation_summary,
            result=challenge_result,
            state_summary=state.summary(),
        )
        self._vprint(" done.\n")
        print(outcome_output.content)
        self._logger.log(outcome_output)
        outputs.append(outcome_output.to_dict())

        # Extract historical figure from outcome narration
        role = "crisis_leader" if success else "fallen_leader"
        figure = self._extract_historical_figure(outcome_output.content, leading_name, state.era, role)
        if figure:
            if not success:
                figure["status"] = "cautionary"
            state.add_historical_figure(figure)
            state.register_name(figure["name"])
            self._vprint(f"    [Historical figure: {figure['name']} — {figure['deed']}]")
            self._logger.log_event("historical_figure", **figure)

        # ── Step 5: GM narrates the boon(s) if success ─────────────────────────
        if success and boons:
            self._vprint(f"\n    → GM chronicling the boon...", end="", flush=True)
            boon_output = self._gm.narrate_boon(
                round_num=state.era,
                boons=boons,
                challenge_text=challenge_text,
                state_summary=state.summary(),
            )
            self._vprint(" done.\n")
            print(boon_output.content)
            self._logger.log(boon_output)
            outputs.append(boon_output.to_dict())
            self._logger.log_event("boon_awarded", era=state.era, boons=boons)

        pause("  ── Challenge resolved. Press Space/Enter to continue or Esc to quit ──", era=state.era)
        self._last_challenge_result = challenge_result
        return outputs

    def _roll_boons(self) -> list[str]:
        """Roll on the boon table. Handle 'TWO boons!' by re-rolling twice."""
        non_double = [b for b in BOON_TABLE if b != "TWO boons! (reroll twice)"]
        result = random.choice(BOON_TABLE)
        if result == "TWO boons! (reroll twice)":
            self._vprint(f"    [TWO BOONS!]")
            return [random.choice(non_double), random.choice(non_double)]
        return [result]

    # ── End of Era Phase ──────────────────────────────────────────────────────

    def _run_end_of_era_phase(self, state: "SettlementState") -> list[dict]:
        print(f"\n  ── The Chronicle Closes ──")
        era_outputs_so_far = self._logger.get_recent(self._memory_window * 4)
        self._vprint(f"    → GM writing era summary...", end="", flush=True)
        gm_output = self._gm.narrate_end_of_era(
            {}, state.era, era_outputs_so_far, state.summary(),
            getattr(self, "_last_challenge_result", {}),
            previous_era_names=list(self._era_names),
            previous_chronicles=list(self._era_chronicle),
        )
        self._vprint(" done.\n")
        print(gm_output.content)
        self._logger.log(gm_output)
        state.append_era_log(gm_output.content[:500])

        # Store chronicle excerpt and extract era name for future prompts
        content = gm_output.content.strip()
        self._era_chronicle.append(content[:300])
        # Try to extract the era name from the first line/title
        first_line = content.split("\n")[0].strip().strip("#").strip()
        if first_line:
            self._era_names.append(first_line)

        # Reconsideration trigger: leader changed during this era
        leader_before = getattr(self, "_leader_before_challenge", None)
        if leader_before is not None and leader_before != state.leading_faction:
            for f in state.factions:
                f["needs_reconsideration"] = True
            self._vprint("    [Reconsideration triggered: leading faction changed this era]")

        pause("  ── End of era. Press Space/Enter to continue or Esc to quit ──", era=state.era, end_of_era=True)
        return [gm_output.to_dict()]

    # ── Victory check ─────────────────────────────────────────────────────────

    def check_victory(self, state: "SettlementState") -> None:
        for f in state.factions:
            if f["victory_points"] >= config.WIN_VP_THRESHOLD:
                state.set_game_over(f["name"])
                print(f"\n  *** {f['name']} has won with {f['victory_points']} VP! ***")
                return
        if state.era >= config.MAX_ERAS:
            # Highest VP wins
            winner = max(state.factions, key=lambda f: f["victory_points"])
            state.set_game_over(winner["name"])
            print(f"\n  *** Game over after {config.MAX_ERAS} eras. Winner: {winner['name']} ({winner['victory_points']} VP) ***")

    # ── File output ───────────────────────────────────────────────────────────

    def _write_era_files(
        self,
        output_dir: str,
        state: "SettlementState",
        era_outputs: list[dict],
    ) -> None:
        prefix = os.path.join(output_dir, f"era_{state.era:02d}")

        summary = {
            "era": state.era,
            "state": state.to_dict(),
            "events": self._logger.events_for_era(state.era),
            "outputs": era_outputs,
        }
        with open(f"{prefix}_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        with open(f"{prefix}_narrative.txt", "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\nERA {state.era} — {state._data['name']}\n{'='*60}\n\n")
            for output in era_outputs:
                f.write(f"[{output['phase'].upper()} / {output['agent_role'].upper()}]\n")
                f.write(output["content"].strip())
                f.write("\n\n" + "-" * 40 + "\n\n")
