"""
Strategy definitions, payout tables, and Make exchange logic.
"""
import random


# ── Payout table ──────────────────────────────────────────────────────────────
# Single table used for all levels. Higher culture levels roll more dice;
# each die is checked independently and all results are summed.
# Format: (min_roll, max_roll, base_tokens, bonus_choice_tokens)

PAYOUT_TABLE: list = [
    (1,  1,  0, 0),
    (2,  12, 1, 0),
    (13, 19, 2, 0),
    (20, 20, 3, 1),  # 3 of color + 1 of any color
]


def roll_strategy_dice(color_level: int) -> list[int]:
    """
    Roll (color_level + 1) d20s.  Returns list of all rolls.
    L0 = 1d20, L1 = 2d20, L2 = 3d20, L3 = 4d20.
    Each die is evaluated independently against the payout table.
    """
    from mechanics.dice import roll as _roll
    n = max(1, color_level + 1)
    return [_roll(20) for _ in range(n)]


def lookup_payout(roll: int) -> tuple[int, int]:
    """Returns (base_tokens, bonus_choice_tokens) for a single die roll."""
    for (lo, hi, base, bonus) in PAYOUT_TABLE:
        if lo <= roll <= hi:
            return (base, bonus)
    return (0, 0)


def resolve_strategy_rolls(rolls: list[int]) -> tuple[int, int]:
    """
    Evaluate each die independently against the payout table and sum results.
    Returns (total_base, total_bonus).
    """
    total_base = 0
    total_bonus = 0
    for r in rolls:
        base, bonus = lookup_payout(r)
        total_base += base
        total_bonus += bonus
    return total_base, total_bonus


# ── Strategy color mappings ────────────────────────────────────────────────────

BASE_STRATEGIES: dict = {
    "pray":     {"token_color": "red",    "payout_table": "base"},
    "discuss":  {"token_color": "blue",   "payout_table": "base"},
    "lead":     {"token_color": "green",  "payout_table": "base"},
    "organize": {"token_color": "orange", "payout_table": "base"},
    "forage":   {"token_color": "pink",   "payout_table": "base"},
}

# Culture categories map to the token color of their unlocked strategy
CULTURE_STRATEGY_COLOR: dict = {
    "spirituality":    "red",
    "mindset":         "blue",
    "social_order":    "blue",
    "values":          "green",
    "politics":        "orange",
    "property":        "orange",
    "production":      "pink",
    "natural_affinity": "pink",
}

# ── Make exchange tables ───────────────────────────────────────────────────────

BASE_MAKE_OPTIONS: dict = {
    "holy_site":  {"exchange_color": "red"},
    "commons":    {"exchange_color": "blue"},
    "marker":     {"exchange_color": "green"},
    "storehouse": {"exchange_color": "orange"},
    "workyard":   {"exchange_color": "pink"},
}

# Make exchange: faction chooses N tokens to spend, receives N * (level + 1) back.
# L0: spend 2 → get 2  |  L1: spend 2 → get 4  |  L2: spend 2 → get 6  |  L3: spend 2 → get 8
def make_receive_for_level(color_level: int, give: int) -> int:
    """Return receive count for a make exchange. Formula: N * (level + 1)."""
    return give * (color_level + 1)


def apply_make_exchange(
    tokens: dict,
    exchange_color: str,
    give: int,
    receive: int,
    receive_colors: list[str],
) -> dict:
    """
    Apply a Make exchange to a token dict.
    receive_colors is a list of colors chosen by the faction, length == receive.
    Returns the updated token dict.
    """
    import copy
    t = copy.copy(tokens)
    if t.get(exchange_color, 0) < give:
        raise ValueError(
            f"Insufficient {exchange_color} tokens: need {give}, have {t.get(exchange_color, 0)}"
        )
    t[exchange_color] = t[exchange_color] - give
    for color in receive_colors:
        t[color] = t.get(color, 0) + 1
    return t


# ── Strategic stances ─────────────────────────────────────────────────────────
# LLM picks a stance; Arbiter resolves it to a concrete base strategy + color

STRATEGIC_STANCES: dict = {
    "pursue_primary":   {"description": "Focus on tokens needed for your Primary goal"},
    "pursue_secondary": {"description": "Focus on tokens needed for your Secondary goals"},
    "pursue_tertiary":  {"description": "Focus on tokens for your Tertiary category"},
    "coordinate":       {"description": "Support a cooperative purchase this era"},
    "oppose":           {"description": "Accumulate tokens to block an opposing culture"},
    "make":             {"description": "Exchange tokens to build something physical"},
}



def award_tokens(
    tokens: dict,
    color: str,
    base_count: int,
    bonus_count: int,
    bonus_colors: list[str] | None = None,
) -> dict:
    """
    Award base_count tokens of color, plus bonus_count tokens of bonus_colors.
    If bonus_colors is None, randomly pick colors for the bonus.
    Returns updated token dict.
    """
    import copy
    ALL_COLORS = ["red", "blue", "green", "orange", "pink"]
    t = copy.copy(tokens)
    t[color] = t.get(color, 0) + base_count
    if bonus_count > 0:
        chosen = bonus_colors or [random.choice(ALL_COLORS) for _ in range(bonus_count)]
        for c in chosen:
            t[c] = t.get(c, 0) + 1
    return t
