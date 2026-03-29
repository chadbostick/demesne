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
            "historical_figures": [],
            "economy": {
                "trade_goods": [],
                "production": [],
                "scarcity": [],
                "trade_partners": [],
            },
            "initiative_order": [],
            "inspiration_seeds": {"source_article": "", "seeds": []},
            "used_names": [],
            "available_ideologies": [],
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

    def eliminate_faction(self, name: str) -> None:
        """Remove a faction from the game (influence dropped below 0)."""
        self._data["factions"] = [f for f in self._data["factions"] if f["name"] != name]
        self._data["initiative_order"] = [n for n in self._data["initiative_order"] if n != name]
        if self._data["leading_faction"] == name:
            # Transfer leadership to highest influence remaining
            if self._data["factions"]:
                best = max(self._data["factions"], key=lambda f: f.get("influence", 0))
                self._data["leading_faction"] = best["name"]
            else:
                self._data["leading_faction"] = None

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

    # ── Available ideologies pool ─────────────────────────────────────────

    def set_available_ideologies(self, ideologies: list[str]) -> None:
        self._data["available_ideologies"] = list(ideologies)

    def pop_available_ideology(self) -> str | None:
        """Remove and return a random ideology from the available pool."""
        import random as _random
        pool = self._data["available_ideologies"]
        if not pool:
            return None
        choice = _random.choice(pool)
        pool.remove(choice)
        return choice

    # ── Inspiration seeds ──────────────────────────────────────────────────

    def set_inspiration_seeds(self, source_article: str, seeds: list[str]) -> None:
        self._data["inspiration_seeds"] = {
            "source_article": source_article,
            "seeds": [{"id": i, "concept": s, "used": False, "used_in": None} for i, s in enumerate(seeds)],
        }

    def get_seed(self, index: int) -> str | None:
        """Get a specific seed by index and mark it used."""
        seeds = self._data["inspiration_seeds"]["seeds"]
        if 0 <= index < len(seeds):
            seeds[index]["used"] = True
            return seeds[index]["concept"]
        return None

    def get_next_seed(self, used_in: str = "") -> str | None:
        """Get the next unused seed and mark it used."""
        for seed in self._data["inspiration_seeds"]["seeds"]:
            if not seed["used"]:
                seed["used"] = True
                seed["used_in"] = used_in
                return seed["concept"]
        return None

    # ── Name deduplication ────────────────────────────────────────────────

    def register_name(self, name: str) -> None:
        if name and name not in self._data["used_names"]:
            self._data["used_names"].append(name)

    def used_names_block(self) -> str:
        names = self._data.get("used_names", [])
        if not names:
            return ""
        return f"NAMES ALREADY IN USE (choose DIFFERENT names): {', '.join(names)}"

    # ── Historical figures ──────────────────────────────────────────────────

    def add_historical_figure(self, figure: dict) -> None:
        """Add a named historical figure. Keys: name, role, faction, era, deed, status."""
        self._data["historical_figures"].append(figure)

    def historical_figures_summary(self) -> str:
        figures = self._data.get("historical_figures", [])
        if not figures:
            return ""
        lines = ["Notable historical figures:"]
        for f in figures[-10:]:  # last 10 to keep prompt manageable
            status = f.get("status", "legendary")
            lines.append(f"  - {f['name']} ({f.get('faction', '?')}, gen {f.get('era', '?')}): {f.get('deed', '')} [{status}]")
        return "\n".join(lines)

    # ── Economy ──────────────────────────────────────────────────────────────

    def add_trade_good(self, good: str) -> None:
        if good not in self._data["economy"]["trade_goods"]:
            self._data["economy"]["trade_goods"].append(good)

    def add_production(self, item: str) -> None:
        if item not in self._data["economy"]["production"]:
            self._data["economy"]["production"].append(item)

    def add_scarcity(self, item: str) -> None:
        if item not in self._data["economy"]["scarcity"]:
            self._data["economy"]["scarcity"].append(item)

    def remove_scarcity(self, item: str) -> None:
        self._data["economy"]["scarcity"] = [s for s in self._data["economy"]["scarcity"] if s != item]

    def add_trade_partner(self, partner: dict) -> None:
        """Add external trade partner. Keys: name, location, relationship."""
        existing_names = [p["name"] for p in self._data["economy"]["trade_partners"]]
        if partner["name"] not in existing_names:
            self._data["economy"]["trade_partners"].append(partner)

    def economy_summary(self) -> str:
        econ = self._data.get("economy", {})
        lines = []
        if econ.get("production"):
            lines.append(f"Production: {', '.join(econ['production'])}")
        if econ.get("trade_goods"):
            lines.append(f"Trade goods: {', '.join(econ['trade_goods'])}")
        if econ.get("scarcity"):
            lines.append(f"Scarcity: {', '.join(econ['scarcity'])}")
        if econ.get("trade_partners"):
            partners = [f"{p['name']} ({p.get('relationship', 'neutral')})" for p in econ["trade_partners"]]
            lines.append(f"Trade partners: {', '.join(partners)}")
        return "\n".join(lines) if lines else "Economy: subsistence, no established trade"

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

    def cultural_identity(self) -> str:
        """
        Describe the settlement's established cultures as lived reality,
        with factions ranked by influence and their aspirations.
        Used by GM to ground narration in what the settlement IS, not just
        what happened to it.
        """
        # Established cultures as character traits
        _CULTURE_MEANING = {
            "Anarchy": "decentralized, no formal authority, self-governing",
            "Authoritarian": "centralized command, obedience expected, strong rulers",
            "Monarchy": "hereditary rule, royal court, noble dynasties",
            "Republic": "elected representatives, civic participation, rule of law",
            "Democracy": "direct popular governance, public debate, majority rule",
            "Empire": "expansionist sovereign state, imperial bureaucracy, conquered territories",
            "Personal": "individual property rights, private ownership, self-reliance",
            "Communal": "shared resources, collective stewardship, mutual obligation",
            "Barter": "direct trade, haggling, goods-for-goods exchange economy",
            "Currency": "standardized money, minted coins, monetary valuation",
            "Banking": "financial institutions, credit, investment, compound interest",
            "Taxes": "state revenue collection, public treasury, redistributive authority",
            "Ancestors": "reverence for the dead, ancestral wisdom, tradition-bound spirituality",
            "Nature": "animistic worship, sacred groves, spiritual ecology",
            "Monotheism": "single deity, organized clergy, doctrinal authority",
            "Polytheism": "pantheon of gods, temples, diverse priesthoods",
            "Science": "empirical method, secular inquiry, evidence over faith",
            "Mysticism": "hidden truths, esoteric knowledge, transcendent experience",
            "Impulsive": "act-first culture, boldness rewarded, risk-taking",
            "Cautious": "deliberation before action, patience valued, risk-averse",
            "Rational": "logic-driven decisions, debate culture, skepticism of emotion",
            "Emotional": "passion-driven, empathy central, feelings guide action",
            "Diplomatic": "negotiation as primary tool, coalition-building, compromise",
            "Isolationist": "self-sufficient, closed borders, distrust of outsiders",
            "Fraternal": "bonds of brotherhood, peer loyalty, egalitarian fellowship",
            "Familial": "blood ties paramount, clan structure, inheritance-based",
            "Tribal": "kinship groups, tribal councils, oral tradition",
            "Hierarchical": "ranked society, stratified classes, authority by station",
            "Class": "rigid social strata, aristocratic privilege, birth determines fate",
            "Meritocracy": "advancement by ability, competitive excellence, earned status",
            "Strength": "physical prowess valued, martial culture, might makes right",
            "Knowledge": "learning valued, scholars respected, curiosity rewarded",
            "Talent": "natural gifts celebrated, charisma and creativity prized",
            "Skill": "craft mastery, technical expertise, demonstrated competence",
            "Prestige": "reputation economy, social standing, honor and display",
            "Power": "raw authority, dominance hierarchies, control as currency",
            "Farming": "agricultural society, settled cultivation, seasonal rhythms",
            "Hunting": "hunter culture, tracking, animal knowledge, frontier ethos",
            "Raiding": "plunder economy, military expeditions, conquest for resources",
            "Trading": "merchant culture, trade routes, commercial diplomacy",
            "Manufacturing": "industrial production, factories, mass craft",
            "Mining": "deep extraction, underground industry, mineral wealth",
            "Earth": "stone-working, stability, endurance, geological awareness",
            "Water": "waterways, navigation, fluid adaptation, aquatic resources",
            "Air": "wind power, open skies, communication, movement of ideas",
            "Fire": "forges, smelting, transformation through heat, industry",
            "Light": "transparency, illumination, public knowledge, openness",
            "Dark": "secrecy, hidden knowledge, shadow governance, subterfuge",
        }

        lines = []

        # Established cultures as defining traits
        established = []
        for cat, data in self._data["cultures"].items():
            if data["level"] == 0:
                continue
            for opt in data["options_chosen"]:
                meaning = _CULTURE_MEANING.get(opt, opt.lower())
                established.append(f"  {opt} ({cat}): {meaning}")

        if established:
            lines.append("ESTABLISHED CULTURES (locked in — the MAJORITY lives this way, narrate as community identity):")
            lines.extend(established)
        else:
            lines.append("NO ESTABLISHED CULTURE YET — scattered camps with competing visions.")

        # List what's absent
        absent = [cat for cat, data in self._data["cultures"].items() if data["level"] == 0]
        if absent:
            lines.append(f"\nNOT YET PART OF COMMUNITY IDENTITY (L0 — individual factions may aspire to these, "
                         f"but the settlement does not embody them): {', '.join(absent)}")

        # Factions by influence
        factions = sorted(self._data["factions"], key=lambda f: f.get("influence", 0), reverse=True)
        if factions:
            lines.append("\nFACTIONS BY INFLUENCE (for individual perspective, not community identity):")
            for f in factions:
                ideology = f.get("ideology", "?")
                inf = f.get("influence", 0)
                lines.append(f"  {f['name']} ({ideology}, influence {inf})")

        return "\n".join(lines)

    _TIER_NAMES = {0: "undeveloped", 1: "foundational", 2: "established", 3: "dominant"}

    def culture_summary(self) -> str:
        lines = ["Culture development:"]
        for cat, data in self._data["cultures"].items():
            lvl = data["level"]
            tier = self._TIER_NAMES.get(lvl, str(lvl))
            opts = ", ".join(data["options_chosen"]) if data["options_chosen"] else "none"
            lines.append(f"  {cat}: {tier} [{opts}]")
        return "\n".join(lines)

    def faction_summary(self) -> str:
        lines = [f"Leading faction: {self._data['leading_faction']}"]
        for f in self._data["factions"]:
            tok = ", ".join(f"{c}:{n}" for c, n in f["tokens"].items() if n > 0) or "none"
            inf = f.get("influence", 0)
            lines.append(f"  {f['name']} ({f['ideology']}) — VP:{f['victory_points']} influence:{inf} tokens:[{tok}]")
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
        hist = self.historical_figures_summary()
        econ = self.economy_summary()
        lines += [
            self.faction_summary(),
            self.culture_summary(),
            econ,
        ]
        if hist:
            lines.append(hist)
        lines.append(self.cultural_identity())
        used = self.used_names_block()
        if used:
            lines.append(used)
        lines += [
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
