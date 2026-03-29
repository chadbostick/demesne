"""Cooperation / coalition mechanics for culture upgrades.

Standalone functions extracted from Arbiter, covering cooperative
purchase evaluation, option scoring, and faction-benefit checks.
"""

from __future__ import annotations

import random
from typing import Callable

from mechanics.cultures import CULTURE_TREE, can_purchase, get_cost
from mechanics.token_economy import can_afford


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def faction_benefits_from(faction: dict, category: str) -> bool:
    """Check if a faction has *category* in any of their goals."""
    goals = faction.get("goals", {})
    p = goals.get("primary", {})
    if p.get("category") == category:
        return True
    for s in goals.get("secondary", []):
        if s.get("category") == category:
            return True
    t = goals.get("tertiary", {})
    if t.get("category") == category:
        return True
    return False


def score_coop_option(opt: dict, factions: list[dict]) -> int:
    """Score a culture option based on faction goal alignment.

    Scores both direct option matches AND category-path alignment
    (a faction benefits from any purchase in a category they need).
    """
    option_name = opt["option"].lower()
    cat = opt["category"]
    score = 0
    for f in factions:
        goals = f.get("goals", {})
        p = goals.get("primary", {})
        if p.get("category") == cat:
            if p.get("option", "").lower() == option_name:
                score += 3  # direct goal match
            elif p.get("enemy_option", "").lower() == option_name:
                score -= 2  # enemy option
            else:
                score += 2  # category on primary path (prerequisite)
        for s in goals.get("secondary", []):
            if s.get("category") == cat:
                if s.get("option", "").lower() == option_name:
                    score += 2
                elif s.get("enemy_option", "").lower() == option_name:
                    score -= 1
                else:
                    score += 1  # category on secondary path
        t = goals.get("tertiary", {})
        if t.get("category") == cat:
            score += 1
    return score


# ---------------------------------------------------------------------------
# Main cooperation functions
# ---------------------------------------------------------------------------

def cooperative_upgrades(factions: list[dict], cultures: dict) -> list[dict]:
    """Return upgrades that willing factions can afford together but not alone.

    Factions with antithesis preference for a specific option are excluded
    from that option's pool (they won't fund something they oppose).
    """
    coop = []
    for cat, cat_data in cultures.items():
        next_lvl = cat_data["level"] + 1
        if next_lvl > 3:
            continue
        if not can_purchase(cat, next_lvl, cultures):
            continue
        cost = get_cost(cat, next_lvl)

        # Only consider factions that benefit from this category
        cat_willing = [f for f in factions if faction_benefits_from(f, cat)]
        if not cat_willing:
            continue

        for opt in CULTURE_TREE[cat]["levels"][next_lvl]["options"]:
            # Further filter: exclude factions whose preference is antithesis
            willing = [
                f for f in cat_willing
                if f.get("culture_preferences", {}).get(cat, {}).get(next_lvl, {}).get(opt, "indifferent") != "antithesis"
            ]
            if not willing:
                continue

            # Sum willing factions' tokens
            willing_combined: dict = {}
            for f in willing:
                for c, n in f["tokens"].items():
                    willing_combined[c] = willing_combined.get(c, 0) + n

            # Affordable by willing factions combined, not by any single one
            if not can_afford(willing_combined, cost):
                continue
            if any(can_afford(dict(f["tokens"]), cost) for f in willing):
                continue
            coop.append({"category": cat, "level": next_lvl, "option": opt, "cost": cost})
    return coop


def pick_preferred_option(
    options: list[dict],
    factions: list[dict],
    verbose_fn: Callable[..., None] | None = None,
) -> dict:
    """Pick the cooperative option with the most faction goal support.

    Given two (or more) cooperative purchase options for the same
    category+level, pick the one with more faction goal support.
    Falls back to random on tie.
    """
    scored = [(opt, score_coop_option(opt, factions)) for opt in options]
    scored.sort(key=lambda x: x[1], reverse=True)

    opt_a, score_a = scored[0]
    opt_b, score_b = scored[1] if len(scored) > 1 else (None, 0)

    if verbose_fn:
        verbose_fn(f"      [Option scoring: {opt_a['option']}={score_a}, {opt_b['option'] if opt_b else '?'}={score_b}]")

    if score_a == score_b:
        choice = random.choice(options)
        if verbose_fn:
            verbose_fn(f"      [Tie — randomly chose {choice['option']}]")
        return choice
    return opt_a
