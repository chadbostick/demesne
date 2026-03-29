"""
FactionAgent — LLM-powered agent that plays a single settler faction.

One instance per faction. Uses different prompt templates for each phase:
  - strategy:   choose a strategy (or make exchange)
  - investment: decide which culture upgrades to purchase
  - challenge:  decide how many tokens to donate
"""
from __future__ import annotations
import json
import re
from agents.base import BaseAgent, AgentOutput
from mechanics.ideologies import IDEOLOGIES
from mechanics.cultures import CULTURE_TREE
from mechanics.strategies import STRATEGIC_STANCES
from mechanics.rename_examples import RENAME_EXAMPLES


class FactionAgent(BaseAgent):

    def __init__(self, faction_data: dict) -> None:
        """
        faction_data must have: name, ideology, species, organization_type, tokens, goals
        """
        self.faction_data = faction_data
        self.role = f"faction_{faction_data['name'].lower().replace(' ', '_')}"
        ideology_name = faction_data["ideology"]
        self.ideology = IDEOLOGIES.get(ideology_name, {})
        self.constraints = []   # per-phase constraints injected at runtime

    # ── Prompt builders ────────────────────────────────────────────────────────

    def _ideology_block(self) -> str:
        id_ = self.ideology
        return (
            f"IDEOLOGY: {self.faction_data['ideology']}\n"
            f"{id_.get('description', '')}\n\n"
            f"Worldview: {id_.get('worldview', '')}\n"
            f"Core fear: {id_.get('core_fear', '')}\n"
            f"Blind spot: {id_.get('blind_spot', '')}\n"
            f"Voice: {id_.get('voice', '')}"
        )

    def _goals_block(self) -> str:
        id_ = self.ideology
        p = id_.get("primary", {})
        lines = [
            "YOUR GOALS:",
            f"  Primary (30 VP): {p.get('option')} (L{p.get('level')} {p.get('category')})",
            f"    Why: {p.get('motivation', '')}",
            f"    Oppose: {p.get('enemy_option')} — {p.get('enemy_reason', '')}",
        ]
        for i, s in enumerate(id_.get("secondary", []), 1):
            lines += [
                f"  Secondary {i} (15 VP): {s.get('option')} (L{s.get('level')} {s.get('category')})",
                f"    Why: {s.get('motivation', '')}",
                f"    Oppose: {s.get('enemy_option')} — {s.get('enemy_reason', '')}",
            ]
        t = id_.get("tertiary", {})
        lines += [
            f"  Tertiary (10 VP/level): {t.get('category')} category",
            f"    Why: {t.get('motivation', '')}",
        ]
        return "\n".join(lines)

    def _tokens_block(self, tokens: dict) -> str:
        tok_str = ", ".join(f"{c}: {n}" for c, n in tokens.items())
        return f"YOUR TOKENS: {tok_str}"

    def _cultural_identity_block(self, cultures: dict) -> str:
        """
        Lists all established culture elements with this faction's attitude toward each.
        Included in every narration prompt so LLMs ground their output in the settlement's reality.
        """
        established = []
        for cat, data in cultures.items():
            if data["level"] == 0:
                continue
            for opt in data["options_chosen"]:
                attitude = self._culture_attitude(cat, opt)
                established.append(f"  • {data.get('display_name', cat)} L{data['level']}: {opt}  [{attitude}]")
        if not established:
            return ""
        lines = ["ESTABLISHED SETTLEMENT CULTURE (permanent — every settler lives within these now):"]
        lines.extend(established)
        return "\n".join(lines)

    def _culture_attitude(self, category: str, option: str) -> str:
        """Return this faction's relationship to an established culture option."""
        goals = self.faction_data.get("goals", {})
        opt_lower = option.lower()
        p = goals.get("primary", {})
        if p.get("category") == category and p.get("option", "").lower() == opt_lower:
            return "you championed this — advances your primary goal"
        for s in goals.get("secondary", []):
            if s.get("category") == category and s.get("option", "").lower() == opt_lower:
                return "you support this — advances a secondary goal"
        if p.get("enemy_option", "").lower() == opt_lower:
            return "you resent this — directly opposes your primary goal"
        for s in goals.get("secondary", []):
            if s.get("enemy_option", "").lower() == opt_lower:
                return "you resent this — conflicts with a secondary goal"
        return "neutral — part of the community now, not your priority"

    def _available_cultures_block(self, cultures: dict) -> str:
        lines = ["AVAILABLE CULTURE PURCHASES (next level for each category):"]
        for cat, data in cultures.items():
            current_level = data["level"]
            next_level = current_level + 1
            if next_level > 3:
                continue
            opts = CULTURE_TREE[cat]["levels"][next_level]["options"]
            cost = CULTURE_TREE[cat]["levels"][next_level]["cost"]
            cost_str = " + ".join(f"{n} {c}" for c, n in cost.items())
            lines.append(
                f"  {cat} L{next_level}: {opts[0]} or {opts[1]} — costs {cost_str}"
            )
        return "\n".join(lines)

    def _culture_preferences_block(self, cultures: dict) -> str:
        """Render this faction's culture preferences for unpurchased levels only."""
        prefs = self.faction_data.get("culture_preferences", {})
        if not prefs:
            return ""
        label_map = {
            "must-have": "want",
            "preferred": "lean toward",
            "indifferent": "indifferent to",
            "antithesis": "oppose",
        }
        lines = ["YOUR CULTURE PREFERENCES (unpurchased levels only):"]
        for cat, levels in prefs.items():
            current_level = cultures.get(cat, {}).get("level", 0)
            for lvl in sorted(levels.keys()):
                if lvl <= current_level:
                    continue
                opts = levels[lvl]
                parts = []
                for opt_name, label in opts.items():
                    parts.append(f"{label_map.get(label, label)} {opt_name}")
                lines.append(f"  {cat} L{lvl}: {', '.join(parts)}")
        return "\n".join(lines)

    # ── Phase-specific run methods ─────────────────────────────────────────────

    def _stance_descriptions(self) -> str:
        """Build stance list with faction-specific goal annotations."""
        id_ = self.ideology
        p = id_.get("primary", {})
        secs = id_.get("secondary", [])
        t = id_.get("tertiary", {})

        lines = []
        for stance, info in STRATEGIC_STANCES.items():
            if stance == "pursue_primary":
                lines.append(
                    f"  pursue_primary   — earn tokens toward: {p.get('option')} ({p.get('category')} L{p.get('level')})"
                )
            elif stance == "pursue_secondary":
                sec_names = "; ".join(f"{s.get('option')} ({s.get('category')})" for s in secs)
                lines.append(f"  pursue_secondary — earn tokens toward: {sec_names}")
            elif stance == "pursue_tertiary":
                lines.append(f"  pursue_tertiary  — earn tokens toward: {t.get('category')} category")
            else:
                lines.append(f"  {stance:<17}— {info['description']}")
        return "\n".join(lines)

    def run_investment(
        self, context: dict, round_num: int, cultures: dict
    ) -> AgentOutput:
        tokens = context.get("own_tokens") or self.faction_data["tokens"]
        recent = self._recent_block(context)

        culture_block = self._cultural_identity_block(cultures)
        culture_section = f"\n{culture_block}\n" if culture_block else ""

        prompt = f"""\
You are {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}

{self._goals_block()}

{self._tokens_block(tokens)}
{culture_section}
SETTLEMENT STATE:
{context.get('state_summary', '')}

{self._available_cultures_block(cultures)}

{self._culture_preferences_block(cultures)}

{recent}

INVESTMENT PHASE: Decide whether to spend tokens to unlock a Culture upgrade.

Rules:
- You may purchase one or more Culture upgrades if you can afford them.
- You must have L1 before buying L2, and L2 before buying L3.
- If you want to block an opponent, you can spend tokens on a Culture level even if it isn't
  your goal — but be strategic about the cost.
- If you have nothing to buy or choose to save tokens, that is valid.

Describe your investment decision in your character's voice (2-3 sentences).
Then output your decision in this exact format:

<investment_choice>
{{
  "purchases": [
    {{"category": "<category>", "level": <number>, "option": "<option name>"}}
  ],
  "narrative": "<your 2-3 sentence description>"
}}
</investment_choice>

If you choose not to invest, use an empty purchases list: "purchases": []
"""
        return self._call_llm(prompt, round_num, "investment")

    def run_challenge_plan(
        self,
        era: int,
        challenge_text: str,
        cultures: dict | None = None,
    ) -> "AgentOutput":
        """Leader narrates what they plan to do about the challenge, before the roll."""
        culture_block = self._cultural_identity_block(cultures) if cultures else ""
        culture_section = f"\n{culture_block}\n" if culture_block else ""

        prompt = f"""\
You are the chronicler for {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}, \
currently leading the settlement through a crisis.

{self._ideology_block()}
{culture_section}
THE CRISIS OF THIS AGE:
{challenge_text}

This is not a single battle or a brief storm — this is the defining crisis of an entire \
age, unfolding over decades or centuries. Describe what {self.faction_data['name']} \
will commit to face this. What will be sacrificed? What institutions mobilized? What will \
the elders tell the children about this moment?

Write in THIRD PERSON — refer to {self.faction_data['name']} by name or as "they", never \
"we" or "our". 2-3 sentences.

VOICE CONSTRAINT: No tokens, dice, victory points, or game mechanics.
"""
        return self._call_llm(prompt, era, "challenge_plan", max_tokens=256)

    def _recent_block(self, context: dict) -> str:
        recent = context.get("recent_actions", [])
        if not recent:
            return "No prior actions yet."
        lines = ["RECENT ACTIONS:"]
        for a in recent:
            lines.append(f"  [Era {a['era']} / {a['phase']} / {a['agent']}]: {a['content'][:120]}...")
        return "\n".join(lines)

    def run_make_narrative(
        self,
        era: int,
        make_type: str,
        location: str,
        terrain: str,
        settlement_stage: str,
        cultures: dict | None = None,
        existing_landmarks: list[dict] | None = None,
    ) -> "AgentOutput":
        """
        When a faction uses Make, describe the structure they build.
        Returns structured JSON with name, location, description, purpose.
        """
        culture_block = self._cultural_identity_block(cultures) if cultures else ""
        culture_section = f"\n{culture_block}\n" if culture_block else ""

        landmarks_block = ""
        if existing_landmarks:
            lines = ["EXISTING STRUCTURES IN THE SETTLEMENT:"]
            for lm in existing_landmarks:
                lines.append(f"  - {lm['name']}: {lm.get('description', '')}")
            landmarks_block = "\n".join(lines) + "\n"

        # Scale structure complexity to settlement stage
        if "city-state" in settlement_stage:
            scale_guidance = (
                "This is a WORLD-CLASS structure in a major city-state. Think grand architecture, "
                "advanced engineering, monumental scale. The best materials, the finest craft, "
                "institutional power made physical. Something that would be famous across nations."
            )
        elif "town" in settlement_stage:
            scale_guidance = (
                "This is a substantial structure in a growing town. Professional craft, durable "
                "materials, civic ambition. Larger than anything a village could build, with "
                "purpose-built rooms and organized labor behind it."
            )
        elif "village" in settlement_stage:
            scale_guidance = (
                "This is a village-scale structure. Local materials, community-built, functional "
                "but with emerging craft traditions. It has character and permanence but remains "
                "modest in scale."
            )
        else:
            scale_guidance = (
                "This is a SIMPLE, PRIMITIVE structure built by scattered camps of survivors. "
                "Think rough shelters, cleared ground, cairns, lean-tos, drying racks, fire pits, "
                "basic fencing. Use only materials found in the immediate landscape. No grand "
                "architecture, no advanced engineering, no monumental anything. These people are "
                "still learning to survive here."
            )

        prompt = f"""\
You are {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}
{culture_section}
SETTLEMENT GEOGRAPHY:
  Location: {location}
  Terrain: {terrain}
  Current stage: {settlement_stage}

{landmarks_block}
Your people are building something that will stand for generations.

SCALE GUIDANCE:
{scale_guidance}

Describe this structure. It should reflect your people's species, ideology, and the current \
level of development. Consider the geography and what already exists here.

Output in this exact format:

<make_structure>
{{
  "name": "<a proper name for this structure>",
  "location": "<where in the settlement or surrounding area it stands — 1 sentence>",
  "description": "<what it looks like physically — 1-2 sentences>",
  "purpose": "<what it does for the community — 1 sentence>"
}}
</make_structure>

VOICE CONSTRAINT: Do NOT mention token colors (red, blue, green, orange, pink), game mechanics, \
victory points, or any metagame concepts. Describe a real place in a real world.

Nothing else.
"""
        return self._call_llm(prompt, era, "make_structure", max_tokens=384)

    def parse_make_structure(self, output: "AgentOutput") -> dict:
        """Extract make_structure JSON. Returns {} on failure."""
        match = re.search(r"<make_structure>(.*?)</make_structure>", output.content, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}

    def run_rename_strategy(
        self,
        era: int,
        color: str,
        category: str,
        option: str,
        old_strategy_name: str,
        old_make_name: str,
    ) -> "AgentOutput":
        """
        After a culture level-up, the buying faction renames the Strategy and Make
        action for that color. Returns 1-2 word names rooted in what the community does.
        """
        _COLOR_ACTIVITY = {
            "red":    ("gathering for prayer, ritual, and spiritual practice",
                       "a sacred site where the community gathers to mark what is holy"),
            "blue":   ("coming together to talk, debate, and share ideas",
                       "a commons — a shared space where people meet, speak, and decide"),
            "green":  ("leading and rallying people toward a shared direction",
                       "a landmark or marker that declares what this community stands for"),
            "orange": ("organizing labor, coordinating people, and getting things done",
                       "a storehouse where goods, tools, or resources are managed and distributed"),
            "pink":   ("scouting, foraging, and gathering from the land",
                       "a workyard where people craft, build, and process what the land provides"),
        }
        activity_desc, make_desc = _COLOR_ACTIVITY.get(color, (old_strategy_name, old_make_name))

        examples = RENAME_EXAMPLES.get(option.lower(), {})
        sample_strategies = ", ".join(f'"{s}"' for s in examples.get("strategies", [])[:6])
        sample_makes = ", ".join(f'"{m}"' for m in examples.get("makes", [])[:5])
        examples_block = ""
        if sample_strategies or sample_makes:
            examples_block = (
                f"\nSAMPLE NAMES for {option} culture (choose one or invent something similar):\n"
                + (f"  Strategy options: {sample_strategies}\n" if sample_strategies else "")
                + (f"  Make options:     {sample_makes}\n" if sample_makes else "")
            )

        prompt = f"""\
Your settlement has just shaped its {category} culture around: {option}.

This changes how your community describes two of its core activities. Your task is to rename them.

THE ACTIVITY (strategy):
People {activity_desc}.
With {option} now defining {category} here, what do your people CALL this practice?
Your ideology ({self.faction_data['ideology']}) can flavor the word — but the name must describe
a community practice or verb, not a personal power or supernatural ability.

THE PLACE (make):
People build {make_desc}.
With {option} now defining {category} here, what do your people CALL this place or act?
A noun for a real place or communal act — not a power or abstract concept.
{examples_block}
Output your choice in this exact format:

<rename_choice>
{{
  "strategy_name": "<1-2 words>",
  "make_name": "<1-2 words>"
}}
</rename_choice>

Nothing else.
"""
        return self._call_llm(prompt, era, "rename_strategy", max_tokens=256)

    def introduce_faction(
        self, location: str, terrain: str, neighbor_factions: list[dict],
        inspiration: str | None = None,
        arriving: bool = False,
        settlement_context: str | None = None,
    ) -> "AgentOutput":
        """
        Introduce a faction. If arriving=True, this is a mid-game arrival
        at an established settlement, not a founding.
        """
        neighbors_block = ""
        if neighbor_factions:
            label = "ESTABLISHED FACTIONS ALREADY HERE:" if arriving else "OTHER FACTIONS SETTLING HERE:"
            lines = [label]
            for nf in neighbor_factions:
                lines.append(f"  - {nf.get('name', nf['ideology'])} ({nf['ideology']} {nf['species']})")
            neighbors_block = "\n".join(lines)

        if arriving and settlement_context:
            arrival_block = (
                f"You are arriving at an ESTABLISHED settlement:\n{settlement_context}\n\n"
                f"This place already has cultures, structures, and history. Your people are new here. "
                f"Consider WHY your people have come — perhaps you are:\n"
                f"  - Immigrants drawn by the settlement's growing prosperity\n"
                f"  - A splinter faction that broke from an existing group over ideological differences\n"
                f"  - Representatives of a distant realm, guild, or empire seeking a foothold\n"
                f"  - Refugees fleeing catastrophe elsewhere, bringing skills and desperation\n"
                f"  - A counter-movement that arose in response to the settlement's failures\n"
                f"  - A merchant class that emerged from the settlement's trade networks\n"
                f"Choose the origin that best fits your ideology and this settlement's story. "
                f"What do you bring that the settlement lacks?"
            )
        else:
            arrival_block = "Your people have journeyed here to build something lasting."

        prompt = f"""\
You are the leader of a group of {self.faction_data['species']} {'arriving at' if arriving else 'settling'} this land.

{self._ideology_block()}

GEOGRAPHY:
  Location: {location}
  Terrain: {terrain}

{neighbors_block}
{f'CREATIVE INSPIRATION (weave this naturally as a detail or concept — do not use literally): {inspiration}' if inspiration else ''}
{arrival_block} As their leader, introduce your faction:

1. Choose a name for your organization — something that reflects your species, your ideology, and \
your ambitions. Not a generic label like "The Guild" — a proper name with character.
2. Name the founding leader — an individual whose name will be remembered for generations.
3. Explain in 2-3 sentences why your people are settling this land and what they hope to achieve. \
Ground it in the geography and your worldview.

Output your introduction in this exact format:

<faction_intro>
{{
  "faction_name": "<your organization's name>",
  "organization_type": "<guild|family|church|warband|company|council|circle|order|tribe|other>",
  "founding_leader": "<full name of the leader who brought your people here>",
  "description": "<2-3 sentences: why you are here, what you hope to build>"
}}
</faction_intro>

Nothing else.
"""
        return self._call_llm(prompt, 0, "faction_intro", max_tokens=256)

    def parse_faction_intro(self, output: "AgentOutput") -> dict:
        """Extract faction_intro JSON. Returns {} on failure."""
        match = re.search(r"<faction_intro>(.*?)</faction_intro>", output.content, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}

    def name_settlement(
        self, location: str, terrain: str, inspiration: str | None = None,
    ) -> "AgentOutput":
        """
        Leading faction names the settlement based on geography and ideology.
        Returns a name and 3-sentence description of natural landmarks.
        """
        insp_block = f"\nCREATIVE INSPIRATION (weave this naturally into the landmark description — do not use literally): {inspiration}\n" if inspiration else ""
        prompt = f"""\
You are {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}

Your people have arrived at a new land to settle. The region is approximately 10km by 10km.

GEOGRAPHY:
  Location: {location}
  Terrain: {terrain}
{insp_block}
As the leading faction, you have the honor of naming this settlement. Choose a name that reflects \
what your people see when they look at this land — filtered through your ideology and worldview.

Then describe the natural landmarks of this region in exactly 3 sentences. What rivers, ridges, \
groves, shores, or formations define this place? Ground the description in the specific location \
and terrain. Make the landscape vivid and real.

Output your choice in this exact format:

<settlement_name>
{{
  "name": "<settlement name>",
  "description": "<3 sentences describing the natural landmarks>"
}}
</settlement_name>

Nothing else.
"""
        return self._call_llm(prompt, 0, "name_settlement", max_tokens=256)

    def parse_settlement_name(self, output: "AgentOutput") -> dict:
        """Extract settlement_name JSON. Returns {} on failure."""
        match = re.search(r"<settlement_name>(.*?)</settlement_name>", output.content, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}

    def name_place(
        self,
        era: int,
        tier: str,
        tier_context: str,
        culture_trigger: dict,
        location: str,
        terrain: str,
        existing_places: list[dict],
        co_founders: list[str] | None = None,
    ) -> "AgentOutput":
        """
        After a culture purchase, the founding faction(s) name the new place
        and describe its character.
        """
        culture_block = self._cultural_identity_block(
            {culture_trigger["category"]: {"level": culture_trigger["level"], "options_chosen": [culture_trigger["option"]]}}
        )

        existing_block = ""
        if existing_places:
            lines = ["EXISTING PLACES:"]
            for p in existing_places:
                lines.append(f"  - {p['name']} ({p['tier']})")
            existing_block = "\n".join(lines)

        co_founders_note = ""
        if co_founders:
            co_founders_note = f"\nCo-founded with: {', '.join(co_founders)}"

        prompt = f"""\
You are {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}

SETTLEMENT GEOGRAPHY:
  Location: {location}
  Terrain: {terrain}

{existing_block}

{tier_context}

The culture that sparked this: {culture_trigger['option']} ({culture_trigger['category']} L{culture_trigger['level']}).
{co_founders_note}

Name this {tier} and describe what makes it distinctive — its character, quirks, what a traveler \
would notice first. Ground it in your people's species, ideology, and this land's geography.

Output in this exact format:

<place_name>
{{
  "name": "<proper name for this {tier}>",
  "details": "<2-3 sentences: character, quirks, what makes it unique>"
}}
</place_name>

Nothing else.
"""
        return self._call_llm(prompt, era, "place_naming", max_tokens=384)

    def parse_place_name(self, output: "AgentOutput") -> dict:
        match = re.search(r"<place_name>(.*?)</place_name>", output.content, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}

    # ── Output parsers ─────────────────────────────────────────────────────────

    def parse_strategy_choice(self, output: AgentOutput) -> dict:
        """Extract strategy_choice JSON from agent output. Returns {} on failure."""
        match = re.search(r"<strategy_choice>(.*?)</strategy_choice>", output.content, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}

    def parse_investment_choice(self, output: AgentOutput) -> dict:
        match = re.search(r"<investment_choice>(.*?)</investment_choice>", output.content, re.DOTALL)
        if not match:
            return {"purchases": []}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {"purchases": []}

    def parse_rename_choice(self, output: AgentOutput) -> dict:
        """Extract rename_choice JSON. Returns {} on failure."""
        match = re.search(r"<rename_choice>(.*?)</rename_choice>", output.content, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}

    def parse_challenge_response(self, output: AgentOutput) -> dict:
        match = re.search(r"<challenge_response>(.*?)</challenge_response>", output.content, re.DOTALL)
        if not match:
            return {"tokens_donated": {}, "narrative": ""}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {"tokens_donated": {}, "narrative": ""}
