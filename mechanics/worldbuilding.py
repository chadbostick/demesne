"""
Worldbuilding tables for settlement generation.
Rolled once at the start of a game to determine the region's geography and faction species.
"""

LOCATIONS: list[str] = [
    "Estuary",
    "Coastline",
    "Island",
    "Interior - Cross Roads",
    "Lake",
    "Interior - Road Stop",
    "Isolated Wilderness",
]

TERRAINS: list[str] = [
    "Mountains",
    "Forest",
    "Plains",
    "Desert",
    "Tundra",
    "Hills",
    "Valley",
    "Plateau",
    "Swamp",
    "Marsh",
]

# ── Species tables ────────────────────────────────────────────────────────────
# Named with source prefix so additional tables (homebrew, etc.) can be added later.

DND5_RACES: list[str] = [
    "Dragonborn", "Dwarf", "Elf", "Gnome", "Half-Elf", "Halfling", "Half-Orc",
    "Human", "Tiefling", "Genasi", "Goliath", "Bugbear", "Goblin", "Hobgoblin",
    "Kenku", "Kobold", "Lizardfolk", "Orc", "Shifter", "Warforged", "Gith",
    "Leonin", "Satyr", "Fairy", "Harengon", "Owlin", "Aarakocra", "Aasimar",
    "Firbolg", "Tabaxi", "Triton", "Yuan-ti", "Tortle", "Changeling", "Kalashtar",
    "Centaur", "Loxodon", "Minotaur", "Simic Hybrid", "Vedalken", "Verdan",
    "Locathah", "Grung",
]
