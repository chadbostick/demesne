"""
Shared faction utilities: data construction, goal cost computation, coalition analysis.
Extracted from main.py to eliminate circular imports with arbiter.py.
"""
from __future__ import annotations
from collections import defaultdict

from mechanics.cultures import CULTURE_TREE, get_cost
from mechanics.ideologies import IDEOLOGIES


def empty_tokens() -> dict:
    return {"red": 0, "blue": 0, "green": 0, "orange": 0, "pink": 0}


def build_faction_data(ideology_name: str, faction_index: int) -> dict:
    """Create a faction data dict for a given ideology."""
    id_ = IDEOLOGIES[ideology_name]
    goals = {
        "primary": id_["primary"],
        "secondary": id_["secondary"],
        "tertiary": id_["tertiary"],
    }
    return {
        "name": f"{ideology_name} Faction",
        "ideology": ideology_name,
        "species": "Human",
        "organization_type": "Guild",
        "tokens": empty_tokens(),
        "victory_points": 0,
        "goals": goals,
        "needs_reconsideration": False,
        "culture_preferences": id_.get("culture_preferences", {}),
        "influence": 0,
        "goal_costs": compute_goal_costs(goals),
    }


def compute_goal_costs(goals: dict, cultures: dict | None = None) -> dict:
    """
    Compute total tokens needed per color for each goal, considering
    current culture levels. Returns dict with per-goal and aggregate costs.
    """
    cultures = cultures or {}
    result = {}

    # Primary
    p = goals.get("primary", {})
    if p.get("category"):
        cat = p["category"]
        target_lvl = p["level"]
        current = cultures.get(cat, {}).get("level", 0)
        cost: dict[str, int] = {}
        levels = []
        for lvl in range(current + 1, target_lvl + 1):
            lvl_cost = get_cost(cat, lvl)
            for c, n in lvl_cost.items():
                cost[c] = cost.get(c, 0) + n
            levels.append(lvl)
        result["primary"] = {"category": cat, "target_level": target_lvl, "total_cost": cost, "remaining_levels": levels}

    # Secondary
    for i, s in enumerate(goals.get("secondary", [])):
        if s.get("category"):
            cat = s["category"]
            target_lvl = s["level"]
            current = cultures.get(cat, {}).get("level", 0)
            cost = {}
            levels = []
            for lvl in range(current + 1, target_lvl + 1):
                lvl_cost = get_cost(cat, lvl)
                for c, n in lvl_cost.items():
                    cost[c] = cost.get(c, 0) + n
                levels.append(lvl)
            result[f"secondary_{i}"] = {"category": cat, "target_level": target_lvl, "total_cost": cost, "remaining_levels": levels}

    # Tertiary
    t = goals.get("tertiary", {})
    if t.get("category"):
        cat = t["category"]
        current = cultures.get(cat, {}).get("level", 0)
        cost = {}
        levels = []
        for lvl in range(current + 1, 4):
            lvl_cost = get_cost(cat, lvl)
            for c, n in lvl_cost.items():
                cost[c] = cost.get(c, 0) + n
            levels.append(lvl)
        result["tertiary"] = {"category": cat, "target_level": 3, "total_cost": cost, "remaining_levels": levels}

    # Aggregate
    aggregate: dict[str, int] = {}
    for goal_data in result.values():
        for c, n in goal_data["total_cost"].items():
            aggregate[c] = aggregate.get(c, 0) + n
    result["aggregate"] = aggregate

    return result


def compute_coalitions(factions_data: list[dict]) -> dict[str, dict]:
    """
    Compute coalition heuristics for each faction based on goal overlaps.
    Returns {faction_name: {coalitions, solo_targets, conflicts, priority_order}}.
    """
    cat_interest: dict[str, list[dict]] = defaultdict(list)
    for f in factions_data:
        goals = f.get("goals", {})
        fname = f["name"]
        p = goals.get("primary", {})
        if p.get("category"):
            cat_interest[p["category"]].append({
                "faction": fname, "type": "primary", "level": p["level"],
                "option": p["option"], "vp": 30,
            })
        for s in goals.get("secondary", []):
            if s.get("category"):
                cat_interest[s["category"]].append({
                    "faction": fname, "type": "secondary", "level": s["level"],
                    "option": s["option"], "vp": 15,
                })
        t = goals.get("tertiary", {})
        if t.get("category"):
            cat_interest[t["category"]].append({
                "faction": fname, "type": "tertiary", "level": 3,
                "option": "any", "vp": 30,
            })

    result: dict[str, dict] = {}
    for f in factions_data:
        fname = f["name"]
        coalitions = []
        solo_targets = []
        conflicts = []

        goals = f.get("goals", {})
        my_cats = set()
        p = goals.get("primary", {})
        if p.get("category"):
            my_cats.add(p["category"])
        for s in goals.get("secondary", []):
            if s.get("category"):
                my_cats.add(s["category"])
        t = goals.get("tertiary", {})
        if t.get("category"):
            my_cats.add(t["category"])

        for cat in my_cats:
            others_in_cat = [e for e in cat_interest[cat] if e["faction"] != fname]
            if not others_in_cat:
                solo_targets.append(cat)
                continue

            my_entries = [e for e in cat_interest[cat] if e["faction"] == fname]
            my_options = {e["option"] for e in my_entries if e["option"] != "any"}

            allies = []
            rivals = []
            for other in others_in_cat:
                if other["option"] == "any" or not my_options:
                    allies.append(other)
                elif other["option"] in my_options:
                    allies.append(other)
                else:
                    for my_e in my_entries:
                        if my_e["level"] == other["level"] and my_e["option"] != other["option"] and my_e["option"] != "any":
                            rivals.append(other)
                            break
                    else:
                        allies.append(other)

            if allies:
                ally_names = list(set(a["faction"] for a in allies))
                total_vp = sum(a["vp"] for a in allies) + sum(e["vp"] for e in my_entries)
                coalitions.append({
                    "category": cat,
                    "allies": ally_names,
                    "total_vp_at_stake": total_vp,
                    "reason": f"{len(ally_names)+1} factions benefit from {cat} advancement",
                })
            else:
                solo_targets.append(cat)

            for rival in rivals:
                conflicts.append({
                    "category": cat,
                    "rival": rival["faction"],
                    "their_option": rival["option"],
                    "reason": f"opposing options at {cat} level {rival['level']}",
                })

        coalitions.sort(key=lambda c: c["total_vp_at_stake"], reverse=True)

        result[fname] = {
            "coalitions": coalitions,
            "solo_targets": solo_targets,
            "conflicts": conflicts,
            "priority_order": [c["category"] for c in coalitions] + solo_targets,
        }

    return result
