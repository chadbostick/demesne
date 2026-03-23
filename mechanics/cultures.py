"""
Full culture upgrade tree.

Each category has 3 levels. Each level has 2 opposing options and a token cost.
unlocks_color: the token color of the new Strategy/Make option unlocked when
               any level of this category is purchased.
"""

CULTURE_TREE: dict = {
    "politics": {
        "display_name": "Politics",
        "unlocks_color": "orange",
        "levels": {
            1: {"options": ["Anarchy", "Authoritarian"], "cost": {"red": 1, "orange": 2}},
            2: {"options": ["Monarchy", "Republic"],     "cost": {"red": 2, "orange": 4}},
            3: {"options": ["Democracy", "Empire"],      "cost": {"red": 4, "orange": 8}},
        },
    },
    "property": {
        "display_name": "Property",
        "unlocks_color": "orange",
        "levels": {
            1: {"options": ["Personal", "Communal"],  "cost": {"pink": 1, "orange": 2}},
            2: {"options": ["Barter", "Currency"],    "cost": {"pink": 2, "orange": 4}},
            3: {"options": ["Banking", "Taxes"],      "cost": {"pink": 4, "orange": 8}},
        },
    },
    "spirituality": {
        "display_name": "Spirituality",
        "unlocks_color": "red",
        "levels": {
            1: {"options": ["Ancestors", "Nature"],         "cost": {"red": 1, "blue": 1, "orange": 1}},
            2: {"options": ["Monotheism", "Polytheism"],    "cost": {"red": 2, "blue": 2, "orange": 2}},
            3: {"options": ["Science", "Mysticism"],        "cost": {"red": 4, "blue": 4, "orange": 4}},
        },
    },
    "mindset": {
        "display_name": "Mindset",
        "unlocks_color": "blue",
        "levels": {
            1: {"options": ["Impulsive", "Cautious"],          "cost": {"red": 1, "blue": 2}},
            2: {"options": ["Rational", "Emotional"],          "cost": {"red": 2, "blue": 4}},
            3: {"options": ["Diplomatic", "Isolationist"],     "cost": {"red": 4, "blue": 8}},
        },
    },
    "social_order": {
        "display_name": "Social Order",
        "unlocks_color": "blue",
        "levels": {
            1: {"options": ["Fraternal", "Familial"],       "cost": {"green": 1, "blue": 2}},
            2: {"options": ["Tribal", "Hierarchical"],      "cost": {"green": 2, "blue": 4}},
            3: {"options": ["Class", "Meritocracy"],        "cost": {"green": 4, "blue": 8}},
        },
    },
    "values": {
        "display_name": "Values",
        "unlocks_color": "green",
        "levels": {
            1: {"options": ["Strength", "Knowledge"],   "cost": {"green": 1, "blue": 1, "pink": 1}},
            2: {"options": ["Talent", "Skill"],         "cost": {"green": 2, "blue": 2, "pink": 2}},
            3: {"options": ["Prestige", "Power"],       "cost": {"green": 4, "blue": 4, "pink": 4}},
        },
    },
    "production": {
        "display_name": "Production",
        "unlocks_color": "pink",
        "levels": {
            1: {"options": ["Farming", "Hunting"],           "cost": {"orange": 1, "pink": 2}},
            2: {"options": ["Raiding", "Trading"],           "cost": {"orange": 2, "pink": 4}},
            3: {"options": ["Manufacturing", "Mining"],      "cost": {"orange": 4, "pink": 8}},
        },
    },
    "natural_affinity": {
        "display_name": "Natural Affinity",
        "unlocks_color": "pink",
        "levels": {
            1: {"options": ["Earth", "Water"],  "cost": {"green": 1, "pink": 2}},
            2: {"options": ["Air", "Fire"],     "cost": {"green": 2, "pink": 4}},
            3: {"options": ["Light", "Dark"],   "cost": {"green": 4, "pink": 8}},
        },
    },
}

ALL_CATEGORIES = list(CULTURE_TREE.keys())


def get_cost(category: str, level: int) -> dict:
    return CULTURE_TREE[category]["levels"][level]["cost"]


def get_options(category: str, level: int) -> list[str]:
    return CULTURE_TREE[category]["levels"][level]["options"]


def get_opposing_option(category: str, level: int, chosen_option: str) -> str | None:
    options = get_options(category, level)
    for opt in options:
        if opt.lower() != chosen_option.lower():
            return opt
    return None


def can_purchase(category: str, level: int, current_cultures: dict) -> bool:
    """Check if level prerequisites are met (need L1 before L2, L2 before L3)."""
    current_level = current_cultures.get(category, {}).get("level", 0)
    return level == current_level + 1
