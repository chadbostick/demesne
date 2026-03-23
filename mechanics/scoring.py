"""
Victory Point calculation.
"""
from __future__ import annotations


def option_is_unlocked(cultures: dict, category: str, level: int, option: str) -> bool:
    cat = cultures.get(category, {})
    if cat.get("level", 0) < level:
        return False
    return option.lower() in [o.lower() for o in cat.get("options_chosen", [])]


def score_faction(faction_data: dict, cultures: dict) -> int:
    vp = 0
    goals = faction_data.get("goals", {})

    # Primary goal (30 VP)
    p = goals.get("primary", {})
    if p and option_is_unlocked(cultures, p["category"], p["level"], p["option"]):
        vp += 30

    # Secondary goals (15 VP each, max 30 VP)
    for s in goals.get("secondary", []):
        if option_is_unlocked(cultures, s["category"], s["level"], s["option"]):
            vp += 15

    # Tertiary goal (10 VP per level in category, max 30 VP)
    t = goals.get("tertiary", {})
    if t:
        cat_level = cultures.get(t["category"], {}).get("level", 0)
        vp += cat_level * 10

    return min(vp, 90)


def score_all_factions(factions: list[dict], cultures: dict) -> dict[str, int]:
    """Returns {faction_name: vp} for all factions."""
    return {f["name"]: score_faction(f, cultures) for f in factions}
