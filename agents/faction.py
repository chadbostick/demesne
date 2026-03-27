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

    def run_strategy(
        self, context: dict, round_num: int, available_strategies: list[str],
        cultures: dict | None = None,
    ) -> AgentOutput:
        tokens = context.get("own_tokens") or self.faction_data["tokens"]
        recent = self._recent_block(context)
        current_stance = self.faction_data.get("current_stance") or "pursue_primary"
        prefs_block = self._culture_preferences_block(cultures) if cultures else ""
        prefs_section = f"\n{prefs_block}\n" if prefs_block else ""

        prompt = f"""\
You are {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}

{self._goals_block()}

{self._tokens_block(tokens)}

SETTLEMENT STATE:
{context.get('state_summary', '')}

{recent}

COOPERATION APPROACH: {self.ideology.get('cooperation_currency', '')}
BETRAYAL TENDENCY: {self.ideology.get('betrayal_pattern', '')}
{prefs_section}

YOUR CURRENT STANCE: {current_stance}
(You may maintain this stance or choose a new one.)

AVAILABLE STANCES:
{self._stance_descriptions()}

Each stance maps to a base action: pursue_primary/secondary/tertiary/coordinate/oppose → earn tokens via pray/discuss/lead/organize/forage. "make" → exchange tokens to build.

VOICE CONSTRAINT: Write your narrative as an in-character settler. Do NOT name token colors, reference victory points, or describe game mechanics. Describe your people's actions and motivations as if you are living in this world.

Choose your stance and the concrete strategy that enacts it. Output your choice in this exact format:

<strategy_choice>
{{
  "stance": "<stance name>",
  "strategy": "<pray|discuss|lead|organize|forage|make>",
  "narrative": "<1-2 sentences in-character, no token color names, no VP references>"
}}
</strategy_choice>
"""
        return self._call_llm(prompt, round_num, "strategy")

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

    def run_challenge(
        self,
        context: dict,
        round_num: int,
        challenge_text: str,
        is_leading: bool,
        prior_donations: dict[str, dict],
    ) -> AgentOutput:
        tokens = context.get("own_tokens") or self.faction_data["tokens"]
        total_tokens = sum(tokens.values())

        donations_so_far = ""
        if prior_donations:
            donations_so_far = "DONATIONS SO FAR:\n" + "\n".join(
                f"  {name}: {sum(d.values())} tokens" for name, d in prior_donations.items()
            )

        role_note = (
            "You are the LEADING FACTION. You decide the response strategy and your donation "
            "will anchor the effort."
            if is_leading
            else "You may donate tokens to support the Leading Faction's response. "
                 "Consider whether the outcome serves your goals."
        )

        prompt = f"""\
You are {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}

{self._tokens_block(tokens)}

SETTLEMENT STATE:
{context.get('state_summary', '')}

CHALLENGE THIS ERA:
{challenge_text}

{role_note}

{donations_so_far}

Rules:
- Each token donated adds +1 to the d20 roll. Total of 10+ = success.
- Tokens spent on the challenge are permanently lost.
- Success: the settlement receives a Boon and the Leading Faction stays in power.
- Failure: the challenge harms the settlement, the Leading Faction loses power.

Decide how many tokens to donate and from which colors. Describe your decision in your voice (1-2 sentences).

<challenge_response>
{{
  "tokens_donated": {{"red": 0, "blue": 0, "green": 0, "orange": 0, "pink": 0}},
  "narrative": "<your 1-2 sentence description>"
}}
</challenge_response>

Only include colors where you are donating > 0 tokens. You may donate 0 total if you choose.
"""
        return self._call_llm(prompt, round_num, "challenge")

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
You are {self.faction_data['name']}, leading the settlement through a crisis.

{self._ideology_block()}
{culture_section}
THE CRISIS:
{challenge_text}

As the leader, describe what your people will do to face this challenge. What resources will you \
commit? What strategy will you employ? Speak as a leader rallying their people before the outcome \
is known.

VOICE CONSTRAINT: Write as an in-character settler leader. Do NOT mention tokens, dice rolls, \
victory points, difficulty numbers, or any game mechanics. 2-3 sentences only.
"""
        return self._call_llm(prompt, era, "challenge_plan", max_tokens=256)

    def run_challenge_narrative(
        self,
        context: dict,
        era: int,
        challenge_text: str,
        donation_summary: str,
        difficulty: int,
        result: dict,
        cultures: dict | None = None,
    ) -> "AgentOutput":
        """Leader-only LLM call: narrate challenge resolution in character."""
        success = result.get("success", False)
        roll_total = result.get("total", 0)
        outcome_word = "prevailed" if success else "failed"
        if success:
            boon_line = f"A boon was earned: {result.get('boon', '')}"
        else:
            boon_line = "The settlement suffered setback. Leadership will pass to another faction."

        culture_block = self._cultural_identity_block(cultures) if cultures else ""
        culture_section = f"\n{culture_block}\n" if culture_block else ""

        prompt = f"""\
You are {self.faction_data['name']}, leading the settlement through a crisis.

{self._ideology_block()}
{culture_section}
THE CRISIS:
{challenge_text}

HOW THE SETTLEMENT RESPONDED:
{donation_summary}

OUTCOME: The settlement {outcome_word}.
{boon_line}

Narrate this moment in your faction's voice. Speak as the leader addressing your people.

VOICE CONSTRAINT: Write as an in-character settler leader. Do NOT mention tokens, dice rolls,
victory points, difficulty numbers, or any game mechanics. Ground the language in your ideology's
voice and worldview. 2-3 sentences only.
"""
        return self._call_llm(prompt, era, "challenge_narrative")

    # ── Shared helpers ─────────────────────────────────────────────────────────

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
        exchange_color: str,
        receive_color: str,
        location: str,
        terrain: str,
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

        prompt = f"""\
You are {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}
{culture_section}
SETTLEMENT GEOGRAPHY:
  Location: {location}
  Terrain: {terrain}

{landmarks_block}
Your people are building a {make_type} — a structure that will stand for generations. This is a \
place where your community converts {exchange_color} effort into {receive_color} resources.

Describe this structure. It should reflect your people's species, ideology, and history in this \
settlement. Consider the geography and what already exists here.

Output in this exact format:

<make_structure>
{{
  "name": "<a proper name for this structure>",
  "location": "<where in the settlement or surrounding area it stands — 1 sentence>",
  "description": "<what it looks like physically — 1-2 sentences>",
  "purpose": "<what it does for the community — 1 sentence>"
}}
</make_structure>

Nothing else.
"""
        return self._call_llm(prompt, era, "make_structure", max_tokens=256)

    def parse_make_structure(self, output: "AgentOutput") -> dict:
        """Extract make_structure JSON. Returns {} on failure."""
        match = re.search(r"<make_structure>(.*?)</make_structure>", output.content, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}

    def run_strategy_narrative(
        self,
        era: int,
        strategy: str,
        tokens_earned: int,
        make_info: dict | None = None,
        cultures: dict | None = None,
    ) -> "AgentOutput":
        """
        Brief in-character narration of what the faction did this era.
        Strategy is already decided — LLM only provides flavor.
        """
        _STRATEGY_ACTIVITY = {
            "pray":     "spiritual practice — prayer, ritual, devotion",
            "discuss":  "assembly and discourse — debate, persuasion, civic exchange",
            "lead":     "leadership and inspiration — rallying, guiding, setting direction",
            "organize": "civic organization — planning, coordinating, building systems",
            "forage":   "scouting and gathering — exploring the land, collecting resources",
        }

        if make_info:
            activity_line = (
                f"Your people built something this era: {make_info['name']}.\n"
                f"What it is: {make_info['description']}"
            )
            result_line = "The structure now stands in the settlement."
        else:
            activity = _STRATEGY_ACTIVITY.get(strategy, strategy)
            if tokens_earned == 0:
                quality = "the effort yielded little — a difficult era"
            elif tokens_earned <= 2:
                quality = "the effort yielded modest returns"
            elif tokens_earned <= 5:
                quality = "the effort yielded strong returns"
            else:
                quality = "the effort yielded an exceptional bounty"
            activity_line = f"Your people's focus this era: {activity}."
            result_line = f"How it went: {quality}."

        culture_block = self._cultural_identity_block(cultures) if cultures else ""
        culture_section = f"\n{culture_block}\n" if culture_block else ""

        prompt = f"""\
You are the chronicler for {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}
{culture_section}
THIS ERA THEY FOCUSED ON:
{activity_line}
{result_line}

Write 2-3 sentences describing what {self.faction_data['name']} did and why it matters to \
them. Write in THIRD PERSON — refer to the faction by name or as "they", never "we" or "our". \
Make it vivid and grounded in their worldview.

VOICE CONSTRAINT: No token colors, no rolls, no victory points, no game mechanics, no faction \
labels, no fantasy clichés. Pure in-character settler voice.
"""
        return self._call_llm(prompt, era, "strategy_narrative", max_tokens=256)

    def _call_llm(self, prompt: str, round_num: int, phase: str, max_tokens: int = 1024) -> AgentOutput:
        import anthropic
        import config
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=config.MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        return AgentOutput(
            agent_role=self.role,
            phase=phase,
            round=round_num,
            content=raw,
        )

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
        return self._call_llm(prompt, era, "rename_strategy", max_tokens=128)

    def introduce_faction(
        self, location: str, terrain: str, neighbor_factions: list[dict]
    ) -> "AgentOutput":
        """
        At game start, the faction introduces itself: names itself and explains
        why it is settling this land.
        """
        neighbors_block = ""
        if neighbor_factions:
            lines = ["OTHER FACTIONS SETTLING HERE:"]
            for nf in neighbor_factions:
                lines.append(f"  - {nf['ideology']} ({nf['species']})")
            neighbors_block = "\n".join(lines)

        prompt = f"""\
You are the leader of a group of {self.faction_data['species']} arriving at a new land to settle.

{self._ideology_block()}

GEOGRAPHY:
  Location: {location}
  Terrain: {terrain}

{neighbors_block}

Your people have journeyed here to build something lasting. As their leader, introduce your faction:

1. Choose a name for your organization — something that reflects your species, your ideology, and \
your ambitions. Not a generic label like "The Guild" — a proper name with character.
2. Explain in 2-3 sentences why your people are settling this land and what they hope to achieve. \
Ground it in the geography and your worldview.

Output your introduction in this exact format:

<faction_intro>
{{
  "faction_name": "<your organization's name>",
  "organization_type": "<guild|family|church|warband|company|council|circle|order|tribe|other>",
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
        self, location: str, terrain: str
    ) -> "AgentOutput":
        """
        Leading faction names the settlement based on geography and ideology.
        Returns a name and 3-sentence description of natural landmarks.
        """
        prompt = f"""\
You are {self.faction_data['name']}, a {self.faction_data['organization_type']} of {self.faction_data['species']}.

{self._ideology_block()}

Your people have arrived at a new land to settle. The region is approximately 10km by 10km.

GEOGRAPHY:
  Location: {location}
  Terrain: {terrain}

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
        return self._call_llm(prompt, era, "place_naming", max_tokens=256)

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
