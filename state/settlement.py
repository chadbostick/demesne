import json
from copy import deepcopy
from mechanics.cultures import ALL_CATEGORIES, CULTURE_TREE


def _empty_cultures() -> dict:
    return {cat: {"level": 0, "options_chosen": []} for cat in ALL_CATEGORIES}


def _default_color_upgrades() -> dict:
    return {
        "red":    {"level": 0, "strategy_name": "pray",     "make_name": "Holy Site"},
        "blue":   {"level": 0, "strategy_name": "discuss",  "make_name": "Commons"},
        "green":  {"level": 0, "strategy_name": "lead",     "make_name": "Marker"},
        "orange": {"level": 0, "strategy_name": "organize", "make_name": "Storehouse"},
        "pink":   {"level": 0, "strategy_name": "forage",   "make_name": "Workyard"},
    }


def _empty_tokens() -> dict:
    return {"red": 0, "blue": 0, "green": 0, "orange": 0, "pink": 0}


class SettlementState:
    """Game state for one settlement run."""

    def __init__(self, name: str = "Unnamed Settlement"):
        self._data: dict = {
            "name": name,
            "era": 0,
            "cultures": _empty_cultures(),
            "color_upgrades": _default_color_upgrades(),
            "available_strategies": ["pray", "discuss", "lead", "organize", "forage", "make"],
            "available_make_options": ["holy_site", "commons", "marker", "storehouse", "workyard"],
            "leading_faction": None,
            "factions": [],
            "era_log": [],
            "current_challenge": None,
            "boons": [],
            "landmarks": [],
            "places": [],
            "initiative_order": [],
            "location": None,
            "terrain": None,
            "landmark_description": None,
            "challenge_difficulty": 10,
            "challenges_failed": 0,
            "game_over": False,
            "winner": None,
        }

    # ── Faction management ────────────────────────────────────────────────────

    def add_faction(self, faction_data: dict) -> None:
        """Add a faction dict to the settlement. Sets leading faction if first."""
        self._data["factions"].append(deepcopy(faction_data))
        if self._data["leading_faction"] is None:
            self._data["leading_faction"] = faction_data["name"]

    def get_faction(self, name: str) -> dict:
        for f in self._data["factions"]:
            if f["name"] == name:
                return f
        raise KeyError(f"Faction '{name}' not found")

    def update_faction_tokens(self, name: str, tokens: dict) -> None:
        f = self.get_faction(name)
        f["tokens"] = tokens

    def update_faction_vp(self, name: str, vp: int) -> None:
        self.get_faction(name)["victory_points"] = vp

    def set_leading_faction(self, name: str) -> None:
        self._data["leading_faction"] = name

    # ── Culture management ────────────────────────────────────────────────────

    def apply_culture_upgrade(self, category: str, level: int, option: str) -> None:
        cat = self._data["cultures"][category]
        cat["level"] = level
        if option not in cat["options_chosen"]:
            cat["options_chosen"].append(option)

    def unlock_strategy(self, strategy_name: str) -> None:
        if strategy_name not in self._data["available_strategies"]:
            self._data["available_strategies"].append(strategy_name)

    def unlock_make_option(self, make_name: str) -> None:
        if make_name not in self._data["available_make_options"]:
            self._data["available_make_options"].append(make_name)

    # ── Geography ──────────────────────────────────────────────────────────────

    def set_location(self, location: str) -> None:
        self._data["location"] = location

    def set_terrain(self, terrain: str) -> None:
        self._data["terrain"] = terrain

    def set_landmark_description(self, description: str) -> None:
        self._data["landmark_description"] = description

    # ── Places (villages, towns, city-states) ────────────────────────────────

    TIER_FOR_LEVEL = {1: "village", 2: "town", 3: "city-state"}

    def add_place(self, place: dict) -> None:
        """Add a named place (village/town/city-state) to the settlement."""
        self._data["places"].append(place)

    def count_places_by_tier(self, tier: str) -> int:
        return sum(1 for p in self._data["places"] if p.get("tier") == tier)

    def places_summary(self) -> str:
        if not self._data["places"]:
            return "Places: scattered camps only, no villages yet"
        lines = ["Places:"]
        for p in self._data["places"]:
            lines.append(f"  {p['tier'].title()}: {p['name']} (era {p.get('founded_era', '?')})")
        return "\n".join(lines)

    def settlement_stage(self) -> str:
        """Describe the current stage of settlement development."""
        places = self._data["places"]
        if not places:
            return "scattered camps"
        tiers = [p["tier"] for p in places]
        if "city-state" in tiers:
            n = tiers.count("city-state")
            return f"city-state ({n} major center{'s' if n > 1 else ''})"
        if "town" in tiers:
            n = tiers.count("town")
            return f"town{'s' if n > 1 else ''} and villages"
        n = len(places)
        return f"{n} village{'s' if n > 1 else ''}"

    # ── Era management ────────────────────────────────────────────────────────

    def increment_era(self) -> None:
        self._data["era"] += 1

    def append_era_log(self, entry: str) -> None:
        self._data["era_log"].append(entry)

    def set_challenge(self, challenge: str) -> None:
        self._data["current_challenge"] = challenge

    def add_boon(self, boon: str) -> None:
        self._data["boons"].append(boon)

    def set_initiative_order(self, order: list[str]) -> None:
        """Set initiative order (highest roll first) and set leading faction."""
        self._data["initiative_order"] = list(order)
        if order:
            self._data["leading_faction"] = order[0]

    def advance_difficulty(self, failed: bool = False) -> None:
        """Increment challenge difficulty by 1 each era, +1 more on failure."""
        self._data["challenge_difficulty"] += 1
        if failed:
            self._data["challenge_difficulty"] += 1
            self._data["challenges_failed"] += 1

    def add_landmark(self, name: str, description: str, builder: str) -> None:
        self._data["landmarks"].append({
            "name": name,
            "description": description,
            "built_by": builder,
            "era": self._data["era"],
        })

    def get_color_level(self, color: str) -> int:
        """Return the highest culture level achieved across all categories that map to this color."""
        return self._data["color_upgrades"].get(color, {}).get("level", 0)

    def advance_color_level(self, color: str) -> bool:
        """
        Recompute the max level for this color from current cultures.
        Updates color_upgrades[color]["level"] and returns True if it increased.
        """
        new_level = max(
            (self._data["cultures"][cat]["level"]
             for cat, data in CULTURE_TREE.items()
             if data["unlocks_color"] == color),
            default=0,
        )
        current = self._data["color_upgrades"][color]["level"]
        if new_level > current:
            self._data["color_upgrades"][color]["level"] = new_level
            return True
        return False

    def set_color_names(self, color: str, strategy_name: str, make_name: str) -> None:
        """Update the custom strategy and make names for a color after a culture level-up."""
        cu = self._data["color_upgrades"].get(color)
        if cu is not None:
            cu["strategy_name"] = strategy_name
            cu["make_name"] = make_name

    def set_game_over(self, winner: str) -> None:
        self._data["game_over"] = True
        self._data["winner"] = winner

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return deepcopy(self._data)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self._data, indent=indent)

    def culture_summary(self) -> str:
        lines = ["Culture levels:"]
        for cat, data in self._data["cultures"].items():
            lvl = data["level"]
            opts = ", ".join(data["options_chosen"]) if data["options_chosen"] else "none"
            lines.append(f"  {cat}: L{lvl} [{opts}]")
        return "\n".join(lines)

    def faction_summary(self) -> str:
        lines = [f"Leading faction: {self._data['leading_faction']}"]
        for f in self._data["factions"]:
            tok = ", ".join(f"{c}:{n}" for c, n in f["tokens"].items() if n > 0) or "none"
            lines.append(f"  {f['name']} ({f['ideology']}) — VP:{f['victory_points']} tokens:[{tok}]")
        return "\n".join(lines)

    def summary(self) -> str:
        d = self._data
        lines = [
            f"Settlement: {d['name']} (Era {d['era']})",
        ]
        if d.get("location") or d.get("terrain"):
            lines.append(f"Geography: {d.get('terrain', '?')} {d.get('location', '?')}")
        if d.get("landmark_description"):
            lines.append(f"Landmarks: {d['landmark_description']}")
        lines.append(f"Stage: {self.settlement_stage()}")
        lines.append(self.places_summary())
        lines += [
            self.faction_summary(),
            self.culture_summary(),
            f"Strategies available: {', '.join(d['available_strategies'])}",
            f"Current challenge: {d['current_challenge'] or 'none'}",
            f"Boons: {', '.join(d['boons']) if d['boons'] else 'none'}",
        ]
        return "\n".join(lines)

    @property
    def era(self) -> int:
        return self._data["era"]

    @property
    def game_over(self) -> bool:
        return self._data["game_over"]

    @property
    def leading_faction(self) -> str | None:
        return self._data["leading_faction"]

    @property
    def factions(self) -> list[dict]:
        return self._data["factions"]

    @property
    def cultures(self) -> dict:
        return self._data["cultures"]

    @property
    def challenge_difficulty(self) -> int:
        return self._data["challenge_difficulty"]

    @property
    def initiative_order(self) -> list[str]:
        return self._data["initiative_order"]

    @property
    def color_upgrades(self) -> dict:
        return self._data["color_upgrades"]

    def __repr__(self) -> str:
        return f"<SettlementState name={self._data['name']!r} era={self._data['era']}>"
