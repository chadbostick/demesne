"""
Token economy functions extracted from Arbiter.

Pure logic that operates on faction dicts and state — no LLM calls,
no Arbiter instance needed.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from mechanics.strategies import (
    BASE_STRATEGIES,
    CULTURE_STRATEGY_COLOR,
    BASE_MAKE_OPTIONS,
    make_receive_for_level,
)
from mechanics.cultures import CULTURE_TREE, get_cost, can_purchase
from mechanics.faction_utils import compute_goal_costs

if TYPE_CHECKING:
    from state.settlement import SettlementState

# ── Economic effects of culture options ──────────────────────────────────────

CULTURE_ECONOMY_EFFECTS: dict = {
    "Farming":        {"production": ["cultivated crops", "preserved grain"], "removes_scarcity": ["grain"]},
    "Hunting":        {"production": ["dressed hides", "smoked meat"], "trade_goods": ["furs", "bone tools"]},
    "Trading":        {"trade_goods": ["imported luxuries", "exotic spices"], "removes_scarcity": ["metal ore"]},
    "Raiding":        {"trade_goods": ["plundered goods", "captured livestock"], "scarcity": ["trust with neighbors"]},
    "Manufacturing":  {"production": ["finished goods", "textiles", "tools"], "trade_goods": ["manufactured exports"]},
    "Mining":         {"production": ["refined ore", "gemstones", "coal"], "removes_scarcity": ["metal ore", "stone"]},
    "Personal":       {"trade_goods": ["personal crafts"]},
    "Communal":       {"production": ["communal stores"]},
    "Barter":         {"trade_goods": ["bartered goods"]},
    "Currency":       {"trade_goods": ["coined money"], "production": ["minted currency"]},
    "Banking":        {"trade_goods": ["letters of credit", "bonds"], "production": ["banking services"]},
    "Taxes":          {"production": ["tax revenue", "state reserves"]},
    "Earth":          {"production": ["quarried stone", "clay works"], "removes_scarcity": ["stone"]},
    "Water":          {"production": ["irrigation", "clean water"], "removes_scarcity": ["water"]},
    "Air":            {"trade_goods": ["wind-powered goods"], "production": ["windmills"]},
    "Fire":           {"production": ["forged metal", "kilns", "smelted ore"], "removes_scarcity": ["metal ore"]},
}

# ── Helper: verbose print ────────────────────────────────────────────────────

VerboseFn = Callable[..., None] | None


# ── Functions ────────────────────────────────────────────────────────────────

def stance_to_strategy(
    stance: str, faction: dict, state: "SettlementState"
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


def pick_best_strategy(
    faction: dict, state: "SettlementState", verbose_fn: VerboseFn = None
) -> tuple[str, str, str]:
    """
    Smart goal pursuit with coalition awareness and sticky targeting.

    Returns (strategy_name, color, reason).

    Sticky behavior: once a faction starts pursuing a color, they stay
    on it until the shortfall is covered, unless a dramatically better
    opportunity emerges (>3 tokens closer).
    """
    tokens = dict(faction["tokens"])
    goals = faction.get("goals", {})
    cultures = state.cultures
    coalition_plan = faction.get("coalition_plan", {})
    coalition_cats = {c["category"]: c for c in coalition_plan.get("coalitions", [])}

    # Recompute costs against current culture state
    goal_costs = compute_goal_costs(goals, cultures)
    faction["goal_costs"] = goal_costs

    color_to_strat = {v["token_color"]: k for k, v in BASE_STRATEGIES.items()}

    # Evaluate all goals
    candidates: list[dict] = []
    for goal_key in ["primary", "secondary_0", "secondary_1", "tertiary"]:
        goal_data = goal_costs.get(goal_key)
        if not goal_data or not goal_data.get("remaining_levels"):
            continue

        cat = goal_data["category"]
        next_lvl = goal_data["remaining_levels"][0]

        if not can_purchase(cat, next_lvl, cultures):
            continue
        cost = get_cost(cat, next_lvl)

        # Compute per-color shortfalls
        shortfalls: dict[str, int] = {}
        total_short = 0
        for c, needed in cost.items():
            have = tokens.get(c, 0)
            short = max(0, needed - have)
            total_short += short
            if short > 0:
                shortfalls[c] = short

        if total_short == 0:
            continue

        # Coalition bonus
        effective_short = total_short
        coalition = coalition_cats.get(cat)
        if coalition:
            num_allies = len(coalition["allies"])
            coalition_discount = min(total_short - 1, num_allies)
            effective_short = max(1, total_short - coalition_discount)
            suffix = f" (coalition: {num_allies} allies)"
        else:
            suffix = " (solo)"

        # Pick the color with the biggest shortfall for this goal
        worst_color = max(shortfalls, key=shortfalls.get) if shortfalls else None
        if worst_color:
            candidates.append({
                "goal_key": goal_key,
                "category": cat,
                "level": next_lvl,
                "color": worst_color,
                "shortfall": shortfalls[worst_color],
                "total_short": total_short,
                "effective_short": effective_short,
                "suffix": suffix,
            })

    if not candidates:
        # Fallback
        aggregate = goal_costs.get("aggregate", {})
        if aggregate:
            biggest_gap_color = max(
                aggregate.keys(),
                key=lambda c: max(0, aggregate[c] - tokens.get(c, 0))
            )
            if biggest_gap_color in color_to_strat:
                return color_to_strat[biggest_gap_color], biggest_gap_color, "aggregate need"
        return "pray", "red", "fallback"

    # Sort by effective shortfall (closest goal first)
    candidates.sort(key=lambda c: c["effective_short"])
    best = candidates[0]

    # Sticky targeting: if faction was pursuing a color last era,
    # stay on it unless the best candidate is dramatically better
    current_pursuit = faction.get("_current_pursuit", {})
    current_color = current_pursuit.get("color")

    if current_color and current_color in color_to_strat:
        # Find the current pursuit in candidates
        current_candidate = next(
            (c for c in candidates if c["color"] == current_color), None
        )
        if current_candidate:
            # Stay on current unless best is >3 tokens closer
            improvement = current_candidate["effective_short"] - best["effective_short"]
            if improvement <= 3:
                # Stick with current
                faction["_current_pursuit"] = {"color": current_color, "goal_key": current_candidate["goal_key"]}
                strategy = color_to_strat[current_color]
                reason = (
                    f"{current_candidate['goal_key']}: {current_candidate['category']} "
                    f"L{current_candidate['level']} short {current_candidate['total_short']}"
                    f"{current_candidate['suffix']} [STAYING COURSE]"
                )
                return strategy, current_color, reason

    # Switch to best target
    faction["_current_pursuit"] = {"color": best["color"], "goal_key": best["goal_key"]}
    strategy = color_to_strat.get(best["color"], "pray")
    reason = (
        f"{best['goal_key']}: {best['category']} L{best['level']} "
        f"short {best['total_short']}{best['suffix']}"
    )
    return strategy, best["color"], reason


def should_make_instead(
    faction: dict, state: "SettlementState", verbose_fn: VerboseFn = None
) -> dict | None:
    """
    Check if the faction should override to a make exchange.
    Returns {"reason", "exchange_color", "receive_color", "give"} or None.

    Only reserves tokens needed for the SINGLE most achievable goal's
    next level -- not all goals combined. A faction pursuing production L3
    that also needs values L2 and property L1 only reserves for whichever
    is closest, leaving the rest available for exchange.
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

        for short_color, short_amount in shortfall.items():
            for surplus_color in ["red", "blue", "green", "orange", "pink"]:
                if surplus_color == short_color:
                    continue

                have = tokens.get(surplus_color, 0)

                # Only reserve what THIS purchase needs of this color
                reserved = cost.get(surplus_color, 0)
                exchangeable = have - reserved

                # Only make when there's genuine excess
                color_level = state.get_color_level(surplus_color)
                min_excess = 1 if color_level >= 1 else 2
                if exchangeable < min_excess:
                    continue

                multiplier = color_level + 1

                min_give = (short_amount + multiplier - 1) // multiplier
                give = min(min_give, exchangeable)
                receive = make_receive_for_level(color_level, give)

                if receive >= short_amount:
                    return {
                        "reason": (
                            f"exchange {give} {surplus_color} (surplus beyond next purchases) → "
                            f"{receive} {short_color} to cover {cat} L{next_lvl} "
                            f"shortfall ({reason})"
                        ),
                        "exchange_color": surplus_color,
                        "receive_color": short_color,
                        "give": give,
                    }

    return None


def pick_make_receive_distribution(
    faction: dict, tokens: dict, exchange_color: str,
    receive_count: int, state: "SettlementState"
) -> list[str]:
    """
    Distribute received tokens across colors to cover goal shortfalls.
    Each received token can be a different color. Fills biggest shortfalls first.
    """
    _all_colors = ["red", "blue", "green", "orange", "pink"]
    goals = faction.get("goals", {})
    cultures = state.cultures

    # Simulate tokens after the exchange (the give color will be spent)
    sim_tokens = dict(tokens)
    sim_tokens[exchange_color] = 0

    # Collect shortfalls across all goal-relevant next-level purchases
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
            if c == exchange_color:
                continue
            short = needed - sim_tokens.get(c, 0)
            if short > 0:
                shortfalls[c] = max(shortfalls.get(c, 0), short)

    # Fill received tokens: biggest shortfalls first
    result: list[str] = []
    remaining = receive_count

    for c, short in sorted(shortfalls.items(), key=lambda x: x[1], reverse=True):
        if remaining <= 0:
            break
        take = min(short, remaining)
        result.extend([c] * take)
        sim_tokens[c] = sim_tokens.get(c, 0) + take
        remaining -= take

    # If still remaining, pick the color with the largest overall need
    if remaining > 0:
        fallback = next(
            (c for c in sorted(shortfalls, key=lambda c: shortfalls[c], reverse=True) if c != exchange_color),
            next((c for c in _all_colors if c != exchange_color), "red"),
        )
        result.extend([fallback] * remaining)

    return result


def pick_bonus_colors(
    faction: dict, tokens: dict, base_color: str,
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


def next_level_needs(faction: dict, state: "SettlementState") -> dict[str, int]:
    """
    Compute tokens needed for the NEXT purchasable level of each goal category.
    Only reserves for immediate next purchases, not the entire remaining path.
    """
    goals = faction.get("goals", {})
    cultures = state.cultures
    needs: dict[str, int] = {}

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
        if next_lvl > 3:
            continue
        cost = get_cost(cat, next_lvl)
        for c, n in cost.items():
            needs[c] = needs.get(c, 0) + n
    return needs


def future_path_cost(category: str, cultures: dict) -> dict[str, int]:
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


def can_afford(tokens: dict, cost: dict) -> bool:
    return all(tokens.get(c, 0) >= n for c, n in cost.items())


def deduct_tokens(tokens: dict, cost: dict) -> dict:
    t = dict(tokens)
    for c, n in cost.items():
        t[c] = t.get(c, 0) - n
    return t


def affordable_upgrades(tokens: dict, cultures: dict) -> list[dict]:
    """Return list of upgrades this faction can afford right now."""
    affordable = []
    for cat, cat_data in cultures.items():
        next_lvl = cat_data["level"] + 1
        if next_lvl > 3:
            continue
        if not can_purchase(cat, next_lvl, cultures):
            continue
        cost = get_cost(cat, next_lvl)
        if can_afford(tokens, cost):
            for opt in CULTURE_TREE[cat]["levels"][next_lvl]["options"]:
                affordable.append({"category": cat, "level": next_lvl, "option": opt, "cost": cost})
    return affordable


def apply_culture_economy(state: "SettlementState", option: str) -> None:
    """Apply economic effects when a culture option is purchased."""
    effects = CULTURE_ECONOMY_EFFECTS.get(option, {})
    for item in effects.get("production", []):
        state.add_production(item)
    for item in effects.get("trade_goods", []):
        state.add_trade_good(item)
    for item in effects.get("scarcity", []):
        state.add_scarcity(item)
    for item in effects.get("removes_scarcity", []):
        state.remove_scarcity(item)


def find_make_option_by_color(color: str) -> dict | None:
    for opt in BASE_MAKE_OPTIONS.values():
        if opt["exchange_color"] == color:
            return opt
    return None
