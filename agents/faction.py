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
from mechanics.strategies import STRATEGIC_STANCES, COLOR_TO_MAKE_TYPE


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
        self, context: dict, round_num: int, available_strategies: list[str]
    ) -> AgentOutput:
        tokens = context.get("own_tokens") or self.faction_data["tokens"]
        recent = self._recent_block(context)
        current_stance = self.faction_data.get("current_stance") or "pursue_primary"

        # Build make type hint if make is available
        make_hint = ""
        if "make" in available_strategies:
            tok_colors = [c for c, n in tokens.items() if n > 0]
            if tok_colors:
                example_color = tok_colors[0]
                make_type = COLOR_TO_MAKE_TYPE.get(example_color, "structure")
                make_hint = f"\nIf choosing 'make': you will name and describe the physical structure built. The structure type is determined by the color exchanged (e.g. red → Holy Site, blue → Commons, green → Marker, orange → Storehouse, pink → Workyard)."

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

YOUR CURRENT STANCE: {current_stance}
(You may maintain this stance or choose a new one.)

AVAILABLE STANCES:
{self._stance_descriptions()}

Each stance maps to a base action: pursue_primary/secondary/tertiary/coordinate/oppose → earn tokens via pray/discuss/lead/organize/forage. "make" → exchange tokens to build.{make_hint}

VOICE CONSTRAINT: Write your narrative as an in-character settler. Do NOT name token colors, reference victory points, or describe game mechanics. Describe your people's actions and motivations as if you are living in this world.

Choose your stance and the concrete strategy that enacts it. Output your choice in this exact format:

<strategy_choice>
{{
  "stance": "<stance name>",
  "strategy": "<pray|discuss|lead|organize|forage|make>",
  "make_exchange_color": null,
  "make_receive_colors": null,
  "make_structure_name": null,
  "make_structure_description": null,
  "narrative": "<1-2 sentences in-character, no token color names, no VP references>"
}}
</strategy_choice>

If strategy is "make": fill make_exchange_color, make_receive_colors (list of colors, length = 2 × tokens given), make_structure_name (what your people call it), and make_structure_description (1 sentence on how it functions).
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
You are {self.faction_data['name']}.

{self._ideology_block()}
{culture_section}
THIS ERA YOUR PEOPLE FOCUSED ON:
{activity_line}
{result_line}

Write 1-2 sentences in your faction's voice describing what your people did and why it matters to \
them. Speak as a settler, not a player. Make it vivid and grounded in your worldview.

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
        state_patch = self._extract_state_patch(raw)
        return AgentOutput(
            agent_role=self.role,
            phase=phase,
            round=round_num,
            content=raw,
            state_patch=state_patch,
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
        action for that color. Returns 1-2 word names rooted in the new culture + ideology.
        """
        prompt = f"""\
You are {self.faction_data['name']}.

{self._ideology_block()}

YOUR SETTLEMENT has just established a new cultural truth: {option} (the {category} of this place).

This has reshaped how your people approach a fundamental activity. The old names were:
  Strategy: "{old_strategy_name}"
  Make action: "{old_make_name}"

Now that {option} defines the culture of {category} here, give these activities new names that:
- Reflect the spirit of {option} in 1-2 words
- Carry the flavor of your ideology and worldview
- Are concrete and evocative, not generic

Examples of good naming:
  Pray → "Consecrate", Organize → "Command", Forage → "Harvest", Make Storehouse → "Barracks"

Output your choice in this exact format:

<rename_choice>
{{
  "strategy_name": "<1-2 word name for the strategy>",
  "make_name": "<1-2 word name for the make action>"
}}
</rename_choice>

Nothing else. Names only — no explanation.
"""
        return self._call_llm(prompt, era, "rename_strategy", max_tokens=128)

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

    # Required by BaseAgent ABC — delegates to strategy run as default
    def build_prompt(self, context: dict, injected) -> str:
        return ""

    def run(self, context: dict, round_num: int, phase: str, injected=None) -> AgentOutput:
        raise NotImplementedError("Use run_strategy(), run_investment(), or run_challenge() directly.")
