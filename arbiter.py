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
    BASE_STRATEGIES, award_tokens,
    apply_make_exchange, BASE_MAKE_OPTIONS,
    CULTURE_STRATEGY_COLOR,
    CHALLENGE_CATEGORIES,
    roll_strategy_dice, resolve_strategy_rolls, make_receive_for_level,
)
from mechanics.cultures import CULTURE_TREE
from mechanics.scoring import score_all_factions
from mechanics.ideologies import IDEOLOGIES
from state.memory import MemoryContext

if TYPE_CHECKING:
    from state.settlement import SettlementState
    from agents.faction import FactionAgent
    from agents.gm import GMAgent
    from phases.engine import PhaseEngine
    from logger import ActionLogger


PLACEHOLDER_BOONS = [
    "A hidden spring is discovered, securing the settlement's water for a generation.",
    "A skilled artisan joins the settlement, bringing new techniques that boost production.",
    "A diplomatic agreement opens a lucrative trade route to the east.",
    "Ancient ruins are unearthed nearby, revealing both treasure and historical knowledge.",
    "A successful harvest festival strengthens community bonds and restores morale.",
]


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
        self._memory_window = memory_window or config.MEMORY_WINDOW

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
            print(f"\n{'='*60}\n  ERA {state.era}\n{'='*60}")
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
        pause(era=state.era)
        return outputs

    # ── Strategy Phase ────────────────────────────────────────────────────────

    def _run_strategy_phase(self, state: "SettlementState") -> list[dict]:
        print(f"\n  [STRATEGY PHASE]")
        outputs = []
        _all_colors = ["red", "blue", "green", "orange", "pink"]
        _faction_summaries: list[dict] = []
        _faction_narratives: list[str] = []

        for agent in self._factions_in_initiative_order(state):
            fname = agent.faction_data["name"]
            faction = state.get_faction(fname)
            tokens = dict(faction["tokens"])

            # ── Decide strategy ────────────────────────────────────────────
            # 1. Check if make exchange enables a goal purchase (skip LLM if so)
            make_override = self._should_make_instead(faction, state)
            if make_override:
                stance = "make"
                color = make_override["exchange_color"]
                strategy = "make"
                _make_receive_color = make_override["receive_color"]
                _make_give = make_override["give"]
                faction["needs_reconsideration"] = False
                print(f"    [{fname} → MAKE: {make_override['reason']}]")
            else:
                # 2. Reconsider stance via LLM if triggered
                if faction.get("needs_reconsideration", False):
                    context = MemoryContext.build(state, self._logger, self._memory_window, fname)
                    print(f"\n    → {fname} reconsidering stance (LLM)...", end="", flush=True)
                    output = agent.run_strategy(context, state.era, state._data["available_strategies"])
                    print(" done.\n")
                    print(output.content)
                    self._logger.log(output)
                    outputs.append(output.to_dict())
                    choice = agent.parse_strategy_choice(output)
                    new_stance = choice.get("stance", "").lower()
                    if new_stance:
                        faction["current_stance"] = new_stance
                    faction["needs_reconsideration"] = False
                    pause(f"  ── {fname} reconsideration done. Press Space/Enter to continue or Esc to quit ──", era=state.era)

                # 3. Resolve stance to strategy + color
                stance = faction.get("current_stance", "pursue_primary")
                strategy, color = self._stance_to_strategy(stance, faction, state)
                _make_receive_color = None
                _make_give = None

            color_level = state.get_color_level(color)
            cu = state.color_upgrades[color]
            custom_strategy_name = cu["strategy_name"]
            custom_make_name = cu["make_name"]

            # Make stance: attempt exchange first, fall back to normal if insufficient
            if stance == "make":
                make_opt = self._find_make_option_by_color(color)
                if make_opt:
                    give = _make_give or tokens.get(color, 0)  # use calculated amount, or all if no override
                    receive = make_receive_for_level(color_level, give)
                    if give >= 1:
                        receive_color = _make_receive_color or self._pick_make_receive_color(faction, tokens, color, state)
                        receive_colors = [receive_color] * receive
                        tokens = apply_make_exchange(tokens, color, give, receive, receive_colors)
                        tok_str = ", ".join(f"{c}:{n}" for c, n in tokens.items())
                        print(
                            f"    {fname} [{custom_make_name}] gave {give} {color},"
                            f" received {receive} {receive_color}"
                        )
                        print(f"      [Tokens now: {tok_str}]")
                        state.update_faction_tokens(fname, tokens)
                        narrative_out = agent.run_strategy_narrative(
                            state.era, "make", 0,
                            make_info={"name": custom_make_name, "description": f"built by {fname}"},
                            cultures=state.cultures,
                        )
                        print(f"\n{narrative_out.content}\n")
                        self._logger.log(narrative_out)
                        outputs.append(narrative_out.to_dict())
                        _faction_summaries.append({"name": fname, "activity": f"building ({custom_make_name})", "tokens_earned": 0})
                        _faction_narratives.append(narrative_out.content)
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
                bonus_colors = self._pick_bonus_colors(faction, tokens, color, bonus_count, state)
                tokens = award_tokens(tokens, color, base_count, bonus_count, bonus_colors)
                bonus_note = f" + {bonus_count} " + ", ".join(bonus_colors)
            else:
                tokens = award_tokens(tokens, color, base_count, 0)
                bonus_note = ""
            tokens_earned = base_count + bonus_count
            print(f"    {fname} [{stance}→{custom_strategy_name}] rolled {dice_display} → +{base_count} {color}{bonus_note}")

            tok_str = ", ".join(f"{c}:{n}" for c, n in tokens.items())
            print(f"      [Tokens now: {tok_str}]")
            state.update_faction_tokens(fname, tokens)

            # Brief in-character narrative (LLM, post-hoc flavor only)
            narrative_out = agent.run_strategy_narrative(state.era, strategy, tokens_earned, cultures=state.cultures)
            print(f"\n{narrative_out.content}\n")
            self._logger.log(narrative_out)
            outputs.append(narrative_out.to_dict())
            _STRATEGY_ACTIVITY = {
                "pray": "prayer and devotion", "discuss": "discourse and debate",
                "lead": "leadership and rallying", "organize": "planning and coordination",
                "forage": "scouting and gathering",
            }
            _faction_summaries.append({"name": fname, "activity": _STRATEGY_ACTIVITY.get(strategy, strategy), "tokens_earned": tokens_earned})
            _faction_narratives.append(narrative_out.content)

            pause(f"  ── {fname} done. Press Space/Enter to continue or Esc to quit ──", era=state.era)

        # ── GM strategy summary narration ─────────────────────────────────────
        narration_mode = config.STRATEGY_NARRATION_MODE
        if narration_mode != "off" and _faction_summaries:
            print(f"\n    → GM summarizing the era's efforts...", end="", flush=True)
            gm_output = self._gm.narrate_strategy_phase(
                round_num=state.era,
                state_summary=state.summary(),
                faction_summaries=_faction_summaries,
                faction_narratives=_faction_narratives if narration_mode == "narrative" else None,
                mode=narration_mode,
            )
            print(" done.\n")
            print(gm_output.content)
            self._logger.log(gm_output)
            outputs.append(gm_output.to_dict())
            pause("  ── Strategy phase complete. Press Space/Enter to continue or Esc to quit ──", era=state.era)

        return outputs

    def _stance_to_strategy(
        self, stance: str, faction: dict, state: "SettlementState"
    ) -> tuple[str, str]:
        """Map a strategic stance to (strategy_name, token_color)."""
        color_to_strat = {v["token_color"]: k for k, v in BASE_STRATEGIES.items()}
        goals = faction.get("goals", {})

        def color_for_cat(cat: str) -> str:
            return CULTURE_STRATEGY_COLOR.get(cat, "red")

        def strat_for_color(c: str) -> str:
            return color_to_strat.get(c, "pray")

        if stance == "pursue_primary":
            cat = goals.get("primary", {}).get("category", "spirituality")
        elif stance == "pursue_secondary":
            secs = goals.get("secondary", [])
            cat = secs[0].get("category", "spirituality") if secs else "spirituality"
        elif stance == "pursue_tertiary":
            cat = goals.get("tertiary", {}).get("category", "spirituality")
        elif stance == "coordinate":
            return "pray", "red"
        elif stance == "oppose":
            leader_name = state.leading_faction
            if leader_name:
                leader_f = state.get_faction(leader_name)
                leader_cat = leader_f.get("goals", {}).get("primary", {}).get("category", "spirituality")
                leader_color = color_for_cat(leader_cat)
                alt = next(
                    (c for c in ["red", "blue", "green", "orange", "pink"] if c != leader_color),
                    "blue",
                )
                return strat_for_color(alt), alt
            return "pray", "red"
        elif stance == "make":
            cat = goals.get("primary", {}).get("category", "spirituality")
        else:
            return "pray", "red"

        color = color_for_cat(cat)
        return strat_for_color(color), color

    def _pick_bonus_colors(
        self, faction: dict, tokens: dict, base_color: str,
        bonus_count: int, state: "SettlementState"
    ) -> list[str]:
        """
        Pick colors for bonus tokens (from rolling a 20).
        Fills the biggest goal-relevant shortfalls first, excluding the base color
        since the faction is already earning that.
        """
        _all_colors = ["red", "blue", "green", "orange", "pink"]
        goals = faction.get("goals", {})
        cultures = state.cultures

        # Simulate tokens after base award
        sim_tokens = dict(tokens)
        sim_tokens[base_color] = sim_tokens.get(base_color, 0)  # base not added yet but we want other colors

        # Collect shortfalls across goal-relevant purchases
        shortfalls: dict[str, int] = {}
        target_cats = []
        p = goals.get("primary", {})
        if p.get("category"):
            target_cats.append(p["category"])
        for s in goals.get("secondary", []):
            if s.get("category"):
                target_cats.append(s["category"])
        t = goals.get("tertiary", {})
        if t.get("category"):
            target_cats.append(t["category"])

        for cat in target_cats:
            cat_data = cultures.get(cat, {})
            next_lvl = cat_data.get("level", 0) + 1
            if next_lvl > 3 or not can_purchase(cat, next_lvl, cultures):
                continue
            cost = get_cost(cat, next_lvl)
            for c, needed in cost.items():
                if c == base_color:
                    continue
                short = needed - sim_tokens.get(c, 0)
                if short > 0:
                    shortfalls[c] = max(shortfalls.get(c, 0), short)

        # Fill bonus tokens from largest shortfall first
        result: list[str] = []
        remaining = bonus_count
        for c, short in sorted(shortfalls.items(), key=lambda x: x[1], reverse=True):
            if remaining <= 0:
                break
            take = min(short, remaining)
            result.extend([c] * take)
            remaining -= take

        # If still remaining, pick the color with the largest shortfall that isn't base
        if remaining > 0:
            fallback = next(
                (c for c in sorted(shortfalls, key=lambda c: shortfalls[c], reverse=True)),
                next(c for c in _all_colors if c != base_color),
            )
            result.extend([fallback] * remaining)

        return result

    def _future_path_cost(self, category: str, cultures: dict) -> dict[str, int]:
        """
        Total token cost for all remaining levels in a category.
        E.g. if category is at L0, sums costs for L1 + L2 + L3.
        """
        current_level = cultures.get(category, {}).get("level", 0)
        total: dict[str, int] = {}
        for lvl in range(current_level + 1, 4):
            cost = get_cost(category, lvl)
            for c, n in cost.items():
                total[c] = total.get(c, 0) + n
        return total

    def _should_make_instead(self, faction: dict, state: "SettlementState") -> dict | None:
        """
        Check if the faction should override to a make exchange.
        Returns {"reason", "exchange_color", "receive_color", "give"} or None.

        Logic:
        1. For each goal category, compute the NEXT level's shortfall.
        2. Compute the FULL remaining path cost across all goal categories
           to know which colors are reserved for future buys.
        3. Only exchange tokens that are genuinely surplus (not needed for
           any future goal purchase), and only exchange enough to cover
           the immediate shortfall.
        """
        tokens = dict(faction["tokens"])
        goals = faction.get("goals", {})
        cultures = state.cultures

        # Collect goal-relevant categories
        target_cats: list[tuple[str, str]] = []
        p = goals.get("primary", {})
        if p.get("category"):
            target_cats.append((p["category"], f"primary goal ({p.get('option', '?')})"))
        for s in goals.get("secondary", []):
            if s.get("category"):
                target_cats.append((s["category"], f"secondary goal ({s.get('option', '?')})"))
        t = goals.get("tertiary", {})
        if t.get("category"):
            target_cats.append((t["category"], f"tertiary goal ({t['category']})"))

        # Compute total future needs across ALL goal categories
        future_needs: dict[str, int] = {}
        for cat, _ in target_cats:
            path_cost = self._future_path_cost(cat, cultures)
            for c, n in path_cost.items():
                future_needs[c] = future_needs.get(c, 0) + n

        for cat, reason in target_cats:
            cat_data = cultures.get(cat, {})
            next_lvl = cat_data.get("level", 0) + 1
            if next_lvl > 3 or not can_purchase(cat, next_lvl, cultures):
                continue

            cost = get_cost(cat, next_lvl)

            # Find colors we're short on for the NEXT level
            shortfall: dict[str, int] = {}
            for c, needed in cost.items():
                have = tokens.get(c, 0)
                if have < needed:
                    shortfall[c] = needed - have

            if not shortfall:
                continue

            # For each short color, check if we have a surplus color to exchange
            for short_color, short_amount in shortfall.items():
                for surplus_color in ["red", "blue", "green", "orange", "pink"]:
                    if surplus_color == short_color:
                        continue

                    have = tokens.get(surplus_color, 0)
                    # Reserve tokens needed for this purchase's cost
                    reserved_for_purchase = cost.get(surplus_color, 0)
                    # Reserve tokens needed for future goal purchases
                    reserved_for_future = max(0, future_needs.get(surplus_color, 0) - have)
                    # True surplus: what we have minus all reservations
                    # (future_needs already includes this level's cost)
                    surplus_available = have - reserved_for_purchase
                    # Don't sacrifice more than we can afford to lose for future needs
                    # But allow exchanging if we have more than the full future path needs
                    future_remaining = future_needs.get(surplus_color, 0)
                    safe_to_exchange = max(0, have - future_remaining)
                    # Use the lesser of: surplus after this purchase, or safe-to-exchange
                    exchangeable = min(surplus_available, safe_to_exchange) if safe_to_exchange > 0 else surplus_available

                    if exchangeable < 1:
                        continue

                    color_level = state.get_color_level(surplus_color)

                    # Calculate minimum give to cover the shortfall
                    # Formula: receive = give * (level + 1), so give = ceil(short / (level + 1))
                    multiplier = color_level + 1
                    min_give = (short_amount + multiplier - 1) // multiplier  # ceiling division
                    give = min(min_give, exchangeable)
                    receive = make_receive_for_level(color_level, give)

                    if receive >= short_amount:
                        return {
                            "reason": (
                                f"exchange {give} {surplus_color} → "
                                f"{receive} {short_color} to cover {cat} L{next_lvl} "
                                f"shortfall ({reason})"
                            ),
                            "exchange_color": surplus_color,
                            "receive_color": short_color,
                            "give": give,
                        }

        return None

    def _pick_make_receive_color(
        self, faction: dict, tokens: dict, exchange_color: str, state: "SettlementState"
    ) -> str:
        """
        Decide which single color to receive from a make exchange.
        Pick the color with the largest shortfall for a goal-relevant purchase.
        Falls back to primary goal color.
        """
        _all_colors = ["red", "blue", "green", "orange", "pink"]
        goals = faction.get("goals", {})
        cultures = state.cultures

        # Simulate tokens after the exchange (the give color will be spent)
        sim_tokens = dict(tokens)
        sim_tokens[exchange_color] = 0

        # Find the color with the biggest shortfall across goal-relevant purchases
        best_color = None
        best_shortfall = 0

        target_cats = []
        p = goals.get("primary", {})
        if p.get("category"):
            target_cats.append(p["category"])
        for s in goals.get("secondary", []):
            if s.get("category"):
                target_cats.append(s["category"])
        t = goals.get("tertiary", {})
        if t.get("category"):
            target_cats.append(t["category"])

        for cat in target_cats:
            cat_data = cultures.get(cat, {})
            next_lvl = cat_data.get("level", 0) + 1
            if next_lvl > 3 or not can_purchase(cat, next_lvl, cultures):
                continue
            cost = get_cost(cat, next_lvl)
            for c, needed in cost.items():
                if c == exchange_color:
                    continue
                short = needed - sim_tokens.get(c, 0)
                if short > best_shortfall:
                    best_shortfall = short
                    best_color = c

        if best_color:
            return best_color

        # Fallback: primary goal color
        primary_cat = goals.get("primary", {}).get("category", "")
        return CULTURE_STRATEGY_COLOR.get(primary_cat, random.choice(_all_colors))

    def _find_make_option_by_color(self, color: str) -> dict | None:
        for opt in BASE_MAKE_OPTIONS.values():
            if opt["exchange_color"] == color:
                return opt
        return None

    # ── Investment Phase ──────────────────────────────────────────────────────

    def _run_investment_phase(self, state: "SettlementState") -> list[dict]:
        print(f"\n  [INVESTMENT PHASE]")
        outputs = []
        any_purchase_made = False
        for agent in self._factions_in_initiative_order(state):
            fname = agent.faction_data["name"]
            faction = state.get_faction(fname)
            tokens = dict(faction["tokens"])

            affordable = self._affordable_upgrades(tokens, state.cultures)
            if not affordable:
                print(f"\n    [SKIP: {fname} cannot afford any upgrade]")
                continue

            context = MemoryContext.build(state, self._logger, self._memory_window, fname)
            print(f"\n    → {fname} deciding investments...", end="", flush=True)
            output = agent.run_investment(context, state.era, state.cultures)
            print(" done.\n")

            choice = agent.parse_investment_choice(output)
            purchased_any = False

            for purchase in choice.get("purchases", []):
                cat = purchase.get("category", "").lower().replace(" ", "_")
                lvl = purchase.get("level")
                option = purchase.get("option", "")

                if cat not in CULTURE_TREE:
                    print(f"      [SKIP: unknown category '{cat}']")
                    continue
                if not can_purchase(cat, lvl, state.cultures):
                    print(f"      [SKIP: prerequisite not met for {cat} L{lvl}]")
                    continue

                cost = get_cost(cat, lvl)
                if not self._can_afford(tokens, cost):
                    print(f"      [SKIP: cannot afford {cat} L{lvl}]")
                    continue

                valid_opts = [o.lower() for o in CULTURE_TREE[cat]["levels"][lvl]["options"]]
                if option.lower() not in valid_opts:
                    print(f"      [SKIP: '{option}' not valid for {cat} L{lvl}]")
                    continue

                tokens = self._deduct_tokens(tokens, cost)
                state.apply_culture_upgrade(cat, lvl, option)
                print(f"      [UNLOCKED: {cat} L{lvl} — {option}]")
                purchased_any = True
                any_purchase_made = True

                new_strat = f"{cat}_strategy"
                new_make = f"{cat}_make"
                state.unlock_strategy(new_strat)
                state.unlock_make_option(new_make)

                # GM chronicles this cultural shift — it's a big deal
                print(f"\n    → GM chronicling cultural shift...", end="", flush=True)
                culture_narrative = self._gm.narrate_culture_purchase(
                    state.era, cat, option, fname, state._data["name"]
                )
                print(" done.\n")
                print(culture_narrative.content)
                self._logger.log(culture_narrative)
                outputs.append(culture_narrative.to_dict())

                # Check if this purchase raised a color's level → rename
                color = CULTURE_TREE[cat]["unlocks_color"]
                self._check_color_level_up(state, color, cat, option, agent, outputs)

            if purchased_any:
                print(output.content)
                self._logger.log(output)
                outputs.append(output.to_dict())
                tok_str = ", ".join(f"{c}:{n}" for c, n in tokens.items())
                print(f"      [Tokens now: {tok_str}]")
                state.update_faction_tokens(fname, tokens)
                pause(f"  ── {fname} done. Press Space/Enter to continue or Esc to quit ──", era=state.era)
            else:
                tok_str = ", ".join(f"{c}:{n}" for c, n in tokens.items())
                print(f"      [No purchases made. Tokens: {tok_str}]")
                state.update_faction_tokens(fname, tokens)

        # Reconsideration trigger
        if any_purchase_made:
            for f in state.factions:
                f["needs_reconsideration"] = True
            print("\n    [Reconsideration triggered: culture purchase this era]")

        # Cooperative purchase round
        coop_purchased = self._attempt_cooperative_purchases(state)
        if coop_purchased:
            any_purchase_made = True
            # Re-trigger reconsideration if not already set
            for f in state.factions:
                f["needs_reconsideration"] = True
            print("\n    [Reconsideration triggered: cooperative purchase this era]")

        # Recalculate VP for all factions
        scores = score_all_factions(state.factions, state.cultures)
        print("\n    VP totals:")
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
            cur_lvl = state.cultures.get(p_cat, {}).get("level", 0)
            if p_cat and p_lvl:
                if vp >= 30:
                    notes.append(f"primary ✓")
                else:
                    notes.append(f"primary needs {p_cat} L{p_lvl} '{p_opt}' (currently L{cur_lvl})")
            # Tertiary progress
            t = goals.get("tertiary", {})
            t_cat = t.get("category", "")
            if t_cat:
                t_lvl = state.cultures.get(t_cat, {}).get("level", 0)
                if t_lvl > 0:
                    notes.append(f"tertiary {t_cat} L{t_lvl} (+{t_lvl * 10} VP)")
            note_str = f"  [{'; '.join(notes)}]" if notes else ""
            print(f"      {fname}: {vp} VP{note_str}")

        return outputs

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

        print(
            f"\n    → {buyer_agent.faction_data['name']} naming the new {color} strategy "
            f"(L{new_level} culture)...",
            end="", flush=True,
        )
        rename_out = buyer_agent.run_rename_strategy(
            state.era, color, category, option, old_strategy, old_make
        )
        print(" done.")

        choice = buyer_agent.parse_rename_choice(rename_out)
        new_strat = choice.get("strategy_name", "").strip() or old_strategy
        new_make_n = choice.get("make_name", "").strip() or old_make

        state.set_color_names(color, new_strat, new_make_n)
        print(
            f"      [{color.upper()} L{new_level}] Strategy renamed: {old_strategy!r} → {new_strat!r}"
        )
        print(
            f"      [{color.upper()} L{new_level}] Make renamed: {old_make!r} → {new_make_n!r}"
            f"  (exchange formula: spend N → receive N+{new_level})"
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

    def _can_afford(self, tokens: dict, cost: dict) -> bool:
        return all(tokens.get(c, 0) >= n for c, n in cost.items())

    def _deduct_tokens(self, tokens: dict, cost: dict) -> dict:
        t = dict(tokens)
        for c, n in cost.items():
            t[c] = t.get(c, 0) - n
        return t

    def _affordable_upgrades(self, tokens: dict, cultures: dict) -> list[dict]:
        """Return list of upgrades this faction can afford right now."""
        affordable = []
        for cat, cat_data in cultures.items():
            next_lvl = cat_data["level"] + 1
            if next_lvl > 3:
                continue
            if not can_purchase(cat, next_lvl, cultures):
                continue
            cost = get_cost(cat, next_lvl)
            if self._can_afford(tokens, cost):
                for opt in CULTURE_TREE[cat]["levels"][next_lvl]["options"]:
                    affordable.append({"category": cat, "level": next_lvl, "option": opt, "cost": cost})
        return affordable

    def _attempt_cooperative_purchases(self, state: "SettlementState") -> bool:
        """
        After individual investments, attempt to pool tokens across all factions for
        upgrades no single faction could afford alone.
        Returns True if any cooperative purchase was made.
        """
        print(f"\n  [COOPERATIVE INVESTMENT]")
        made_any = False

        while True:
            coop = self._cooperative_upgrades(state.factions, state.cultures)
            if not coop:
                if not made_any:
                    print(f"    No cooperative opportunities this era.")
                break

            # Show all cooperative opportunities found
            print(f"\n    Opportunities found: {len(coop)}")
            for item in coop:
                cost_str = " + ".join(f"{n} {c}" for c, n in item["cost"].items())
                print(f"      {item['category']} L{item['level']} — {item['option']} (costs {cost_str})")

            # Show combined token pool
            combined: dict = {}
            for f in state.factions:
                for c, n in f["tokens"].items():
                    combined[c] = combined.get(c, 0) + n
            combined_str = ", ".join(f"{c}:{n}" for c, n in combined.items() if n > 0)
            print(f"    Combined token pool: [{combined_str}]")

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
                    best = self._pick_preferred_option(options_at_level, state.factions)
                    unique_opps.append(best)
                else:
                    unique_opps.append(item)

            # Sort by faction goal alignment — highest score first
            unique_opps.sort(
                key=lambda o: self._score_coop_option(o, state.factions), reverse=True
            )
            print(f"    Attempting {len(unique_opps)} unique category/level combinations (highest alignment first):")

            bought_one = False
            for opp in unique_opps:
                cat, lvl, option, cost = opp["category"], opp["level"], opp["option"], opp["cost"]
                cost_str = " + ".join(f"{n} {c}" for c, n in cost.items())
                other_option = next(
                    (o for o in CULTURE_TREE[cat]["levels"][lvl]["options"] if o != option), "?"
                )
                score = self._score_coop_option(opp, state.factions)
                other_score = self._score_coop_option(
                    {"category": cat, "level": lvl, "option": other_option}, state.factions
                )
                print(f"\n    Evaluating: {cat} L{lvl} — {option} (costs {cost_str})")
                print(f"      [Score: {option}={score}, {other_option}={other_score}]")

                # Show per-faction token state
                for f in state.factions:
                    tok_str = ", ".join(f"{c}:{n}" for c, n in f["tokens"].items() if n > 0) or "none"
                    print(f"      {f['name']}: [{tok_str}]")

                # Try to pool: for each color needed, take from richest faction(s)
                pool: dict[str, dict[str, int]] = {}
                short_colors: list[str] = []

                for color, needed in cost.items():
                    remaining = needed
                    for f in sorted(state.factions, key=lambda f: f["tokens"].get(color, 0), reverse=True):
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
                    print(f"    → NOT PURCHASED — combined tokens still short: {', '.join(short_colors)}")
                    continue

                # Deduct pooled tokens
                for fname, contributions in pool.items():
                    faction = state.get_faction(fname)
                    tokens = dict(faction["tokens"])
                    for color, amount in contributions.items():
                        tokens[color] -= amount
                    state.update_faction_tokens(fname, tokens)

                state.apply_culture_upgrade(cat, lvl, option)
                state.unlock_strategy(f"{cat}_strategy")
                state.unlock_make_option(f"{cat}_make")
                made_any = True
                bought_one = True

                contribs = "; ".join(
                    f"{fn}: " + ", ".join(f"{n} {c}" for c, n in cols.items())
                    for fn, cols in pool.items()
                )
                print(f"    → PURCHASED: {cat} L{lvl} — {option}")
                print(f"      Contributors: {contribs}")

                # GM chronicles this cultural shift
                print(f"\n    → GM chronicling cultural shift...", end="", flush=True)
                purchaser_str = " + ".join(pool.keys())
                culture_narrative = self._gm.narrate_culture_purchase(
                    state.era, cat, option, purchaser_str, state._data["name"]
                )
                print(" done.\n")
                print(culture_narrative.content)
                self._logger.log(culture_narrative)

                # Check if this purchase raised a color's level → rename
                # Largest contributor renames
                top_contributor = max(pool, key=lambda fn: sum(pool[fn].values()))
                top_agent = next(
                    (a for a in self._factions if a.faction_data["name"] == top_contributor),
                    self._factions[0],
                )
                color = CULTURE_TREE[cat]["unlocks_color"]
                self._check_color_level_up(state, color, cat, option, top_agent, [])

                pause("  ── Cooperative purchase made. Press Space/Enter to continue or Esc to quit ──", era=state.era)
                break  # restart outer while-loop with updated state

            if not bought_one:
                break

        return made_any

    def _cooperative_upgrades(self, factions: list[dict], cultures: dict) -> list[dict]:
        """Return upgrades no single faction can afford but all factions together can."""
        # Sum all faction tokens
        combined: dict = {}
        for f in factions:
            for c, n in f["tokens"].items():
                combined[c] = combined.get(c, 0) + n

        coop = []
        for cat, cat_data in cultures.items():
            next_lvl = cat_data["level"] + 1
            if next_lvl > 3:
                continue
            if not can_purchase(cat, next_lvl, cultures):
                continue
            cost = get_cost(cat, next_lvl)
            # Only affordable combined, not by any single faction
            if not self._can_afford(combined, cost):
                continue
            if any(self._can_afford(dict(f["tokens"]), cost) for f in factions):
                continue
            for opt in CULTURE_TREE[cat]["levels"][next_lvl]["options"]:
                coop.append({"category": cat, "level": next_lvl, "option": opt, "cost": cost})
        return coop

    def _score_coop_option(self, opt: dict, factions: list[dict]) -> int:
        """Score a culture option based on faction goal alignment."""
        option_name = opt["option"].lower()
        cat = opt["category"]
        score = 0
        for f in factions:
            goals = f.get("goals", {})
            p = goals.get("primary", {})
            if p.get("category") == cat and p.get("option", "").lower() == option_name:
                score += 3
            elif p.get("enemy_option", "").lower() == option_name:
                score -= 2
            for s in goals.get("secondary", []):
                if s.get("category") == cat and s.get("option", "").lower() == option_name:
                    score += 2
                elif s.get("enemy_option", "").lower() == option_name:
                    score -= 1
            t = goals.get("tertiary", {})
            if t.get("category") == cat:
                score += 1
        return score

    def _pick_preferred_option(self, options: list[dict], factions: list[dict]) -> dict:
        """
        Given two cooperative purchase options for the same category+level,
        pick the one with more faction goal support. Falls back to random on tie.
        """
        scored = [(opt, self._score_coop_option(opt, factions)) for opt in options]
        scored.sort(key=lambda x: x[1], reverse=True)

        opt_a, score_a = scored[0]
        opt_b, score_b = scored[1] if len(scored) > 1 else (None, 0)

        print(f"      [Option scoring: {opt_a['option']}={score_a}, {opt_b['option'] if opt_b else '?'}={score_b}]")

        if score_a == score_b:
            choice = random.choice(options)
            print(f"      [Tie — randomly chose {choice['option']}]")
            return choice
        return opt_a

    # ── Challenge Phase ───────────────────────────────────────────────────────

    def _run_challenge_phase(self, state: "SettlementState") -> list[dict]:
        print(f"\n  [CHALLENGE PHASE]")
        outputs = []

        # Track leader before challenge for reconsideration trigger in end-of-era
        self._leader_before_challenge = state.leading_faction

        # Draw challenge category
        cat = random.choice(CHALLENGE_CATEGORIES)
        challenge_text = f"{cat['category']}: {cat['description']}"
        state.set_challenge(challenge_text)
        difficulty = state.challenge_difficulty
        print(f"    Challenge: [{cat['category']}] {cat['description']}")
        print(f"    Difficulty: {difficulty}")

        leading_name = state.leading_faction
        leader_faction = state.get_faction(leading_name)
        leader_agent = next(
            (a for a in self._factions if a.faction_data["name"] == leading_name), None
        )
        leader_vp = leader_faction["victory_points"]
        leader_vp_bonus = leader_vp // 10

        # ── Step 1: Leader donates (no LLM) ──────────────────────────────────
        needed = max(0, difficulty - 10 - leader_vp_bonus)
        leader_tokens = dict(leader_faction["tokens"])
        leader_total = sum(leader_tokens.values())
        if leader_total > 0:
            leader_donation = min(leader_total, max(1, needed))
        else:
            leader_donation = 0

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
        print(f"\n    [LEADER DONATION: {leading_name} donates {leader_donation} token(s)]")
        print(f"    [can_solicit={can_solicit}, can_compel={can_compel}]")

        donation_parts = [f"{leading_name} (leader): {leader_donation}"]

        # Build initiative rank map: rank 0 = highest initiative (leader), 1, 2, ...
        initiative_order = state.initiative_order
        rank_map = {name: i for i, name in enumerate(initiative_order)}
        last_rank = len(initiative_order) - 1
        non_leaders = [a for a in self._factions if a.faction_data["name"] != leading_name]

        # ── Step 2a: Compel ───────────────────────────────────────────────────
        if can_compel:
            print(f"\n    [COMPEL]")
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

                print(
                    f"      [COMPEL: {tname} rolled {target_roll_raw}-{target_rank}={target_roll_adj},"
                    f" leader rolled {leader_roll} → {result_str}]"
                )

        # ── Step 2b: Solicit ──────────────────────────────────────────────────
        elif can_solicit:
            print(f"\n    [SOLICIT]")
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

                print(f"      [SOLICIT: {tname} → {result_str} (roll {solicit_roll})]")

        else:
            print(f"    [Leader cannot solicit or compel — proceeding to resolution]")
            for a in non_leaders:
                donation_parts.append(f"{a.faction_data['name']}: 0 (no solicitation)")

        # ── Step 3: Resolve ───────────────────────────────────────────────────
        d20 = roll(20)
        total = d20 + token_pool + leader_vp_bonus
        success = total >= difficulty

        print(
            f"\n    [Roll: {d20} + {token_pool} tokens + {leader_vp_bonus} VP bonus = {total}"
            f" vs difficulty {difficulty} → {'SUCCESS' if success else 'FAILURE'}]"
        )

        if success:
            boon = random.choice(PLACEHOLDER_BOONS)
            state.add_boon(boon)
            print(f"    [Boon: {boon}]")
            challenge_result = {"success": True, "roll": d20, "total": total, "boon": boon}
        else:
            # Re-roll initiative for all factions
            print(f"\n    [INITIATIVE RE-ROLL]")
            new_initiative: dict[str, int] = {}
            for agent in self._factions:
                fname = agent.faction_data["name"]
                r = roll(20)
                new_initiative[fname] = r
                print(f"      {fname}: rolled {r}")
            new_order = sorted(new_initiative, key=lambda n: new_initiative[n], reverse=True)
            state.set_initiative_order(new_order)
            # Re-sync faction_data references
            for agent in self._factions:
                agent.faction_data = state.get_faction(agent.faction_data["name"])
            new_leader = new_order[0]
            print(f"    [New leading faction: {new_leader}]")
            print(f"    [New initiative order: {', '.join(new_order)}]")
            challenge_result = {"success": False, "roll": d20, "total": total, "new_leader": new_leader}

        state.advance_difficulty(failed=not success)
        print(f"    [Next difficulty: {state.challenge_difficulty}]")

        # ── Step 4: Leader narrative (one LLM call) ───────────────────────────
        if leader_agent:
            donation_summary = "; ".join(donation_parts)
            print(f"\n    → {leading_name} narrating challenge...", end="", flush=True)
            narrative_output = leader_agent.run_challenge_narrative(
                context={},
                era=state.era,
                challenge_text=challenge_text,
                donation_summary=donation_summary,
                difficulty=difficulty,
                result=challenge_result,
                cultures=state.cultures,
            )
            print(" done.\n")
            print(narrative_output.content)
            self._logger.log(narrative_output)
            outputs.append(narrative_output.to_dict())

        pause("  ── Challenge resolved. Press Space/Enter to continue or Esc to quit ──", era=state.era)
        self._last_challenge_result = challenge_result
        return outputs

    # ── End of Era Phase ──────────────────────────────────────────────────────

    def _run_end_of_era_phase(self, state: "SettlementState") -> list[dict]:
        print(f"\n  [END OF ERA]")
        era_outputs_so_far = self._logger.get_recent(self._memory_window * 4)
        print(f"    → GM writing era summary...", end="", flush=True)
        gm_output = self._gm.narrate_end_of_era(
            {}, state.era, era_outputs_so_far, state.summary(),
            getattr(self, "_last_challenge_result", {})
        )
        print(" done.\n")
        print(gm_output.content)
        self._logger.log(gm_output)
        state.append_era_log(gm_output.content[:500])

        # Reconsideration trigger: leader changed during this era
        leader_before = getattr(self, "_leader_before_challenge", None)
        if leader_before is not None and leader_before != state.leading_faction:
            for f in state.factions:
                f["needs_reconsideration"] = True
            print("    [Reconsideration triggered: leading faction changed this era]")

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
