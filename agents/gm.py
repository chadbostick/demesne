"""
GMAgent — LLM-powered Game Master.

Runs in:
  - Challenge Phase setup: narrates the challenge drawn
  - End of Era Phase: summarizes the era's events
"""
from __future__ import annotations
from agents.base import BaseAgent, AgentOutput


class GMAgent(BaseAgent):

    role = "gm"
    constraints = []

    def narrate_challenge(
        self,
        context: dict,
        round_num: int,
        challenge_text: str,
        state_summary: str,
    ) -> AgentOutput:
        prompt = f"""\
You are the chronicler of a fantasy settlement. You record history as it unfolds.

SETTLEMENT STATE:
{state_summary}

THE CRISIS OF THIS GENERATION: "{challenge_text}"

This is not a brief event — this is the defining crisis of an entire generation. It unfolds over \
years or decades and will be remembered for centuries. Make it specific to THIS settlement: its \
geography, terrain, established cultures, structures, and people. If the event seems impossible \
for this region (e.g. "Tsunami" in a desert), interpret it as a metaphor or find a creative way \
it manifests here.

In 3-5 sentences, chronicle what befell the people. Name specific places, describe what families \
experienced, how daily life was disrupted across years. Set the stakes in generational terms: \
what will be lost if this is not overcome? What will the children inherit? Do not resolve the \
crisis yet — only describe its weight.

VOICE CONSTRAINT: Write as a historian looking back across decades. No tokens, rolls, victory \
points, or game mechanics. No metagaming language.
"""
        return self._call_llm(prompt, round_num, "challenge_narration")

    def narrate_challenge_outcome(
        self,
        round_num: int,
        challenge_text: str,
        leader_plan: str,
        donation_summary: str,
        result: dict,
        state_summary: str,
    ) -> AgentOutput:
        success = result.get("success", False)
        outcome_word = "prevailed" if success else "failed"
        if success:
            boons = result.get("boons", [result.get("boon", "")])
            boon_line = f"Boons earned: {', '.join(boons)}"
        else:
            new_leader = result.get("new_leader", "another group")
            boon_line = f"The settlement suffered setback. Leadership has passed to {new_leader}."

        prompt = f"""\
You are the chronicler of a fantasy settlement. You record history as it unfolds.

SETTLEMENT STATE:
{state_summary}

THE CRISIS OF THIS GENERATION:
{challenge_text}

THE LEADER'S PLAN:
{leader_plan}

HOW THE SETTLEMENT RESPONDED:
{donation_summary}

OUTCOME: The settlement {outcome_word}.
{boon_line}

This crisis defined a generation. Write 3-5 sentences describing what happened over the years \
it took to resolve. How did families endure? What was permanently changed? If they prevailed, \
what scars remain alongside the triumph? If they failed, what was lost that can never return? \
Describe consequences that children will grow up knowing.

VOICE CONSTRAINT: Write as a historian looking back across decades. No tokens, rolls, \
victory points, or game mechanics.
"""
        return self._call_llm(prompt, round_num, "challenge_outcome", max_tokens=256)

    def narrate_boon(
        self,
        round_num: int,
        boons: list[str],
        challenge_text: str,
        state_summary: str,
    ) -> AgentOutput:
        boon_list = "\n".join(f"  - {b}" for b in boons)
        prompt = f"""\
You are the chronicler of a fantasy settlement. You record history as it unfolds.

SETTLEMENT STATE:
{state_summary}

THE SETTLEMENT OVERCAME A CHALLENGE:
{challenge_text}

AS A RESULT, THE SETTLEMENT RECEIVES:
{boon_list}

These are the lasting legacies born from overcoming the crisis — they will define the next \
generation and reshape how the settlement grows. Narrate what emerged from the struggle.

Give things proper names. Describe how they changed the settlement permanently — not just \
what appeared, but how life is different for the children born after. These are the stories \
that grandparents will tell. Transform each boon into a vivid, generational milestone.

Write 3-5 sentences per boon. Past tense, third-person omniscient.

VOICE CONSTRAINT: Write as a historian. No tokens, rolls, victory points, or game mechanics.
"""
        return self._call_llm(prompt, round_num, "boon_narration", max_tokens=512)

    def narrate_place_founding(
        self,
        round_num: int,
        place_name: str,
        tier: str,
        tier_context: str,
        faction_details: str,
        culture_trigger: dict,
        state_summary: str,
        existing_places: list[dict],
    ) -> AgentOutput:
        existing_block = ""
        if existing_places:
            lines = ["EXISTING PLACES IN THE SETTLEMENT:"]
            for p in existing_places:
                desc = p.get("gm_description", p.get("faction_details", ""))
                lines.append(f"  - {p['name']} ({p['tier']}): {desc[:100]}")
            existing_block = "\n".join(lines)

        prompt = f"""\
You are the chronicler of a fantasy settlement. You record history as it unfolds.

SETTLEMENT STATE:
{state_summary}

{existing_block}

A NEW {tier.upper()} HAS BEEN FOUNDED: {place_name}

{tier_context}

THE FOUNDERS DESCRIBE IT AS:
{faction_details}

CULTURE THAT SPARKED THIS: {culture_trigger['option']} ({culture_trigger['category']} L{culture_trigger['level']})

As the settlement's chronicler, describe where this {tier} sits in the landscape and how it \
relates to existing places. What does it look like from the road? How does it fit into — or \
stand apart from — the growing settlement? What role does it play?

Write 3-4 sentences. Place it spatially: directions, distances, landmarks, terrain features. \
Make it feel like a real place on a real map.

VOICE CONSTRAINT: Write as a historian and cartographer. No game mechanics, tokens, or metagaming.
"""
        return self._call_llm(prompt, round_num, "place_founding", max_tokens=384)

    def narrate_end_of_era(
        self,
        context: dict,
        round_num: int,
        era_outputs: list[dict],
        state_summary: str,
        challenge_result: dict,
        previous_era_names: list[str] | None = None,
        previous_chronicles: list[str] | None = None,
    ) -> AgentOutput:
        # Extract only in-character narrative text from era outputs (skip mechanical logs)
        narrative_lines = []
        for o in era_outputs:
            phase = o.get("phase", "")
            content = o.get("content", "").strip()
            if content:
                narrative_lines.append(f"[{phase}]: {content[:300]}")
        era_narrative = "\n\n".join(narrative_lines) if narrative_lines else "No narration recorded."

        if challenge_result.get("success"):
            result_text = (
                f"The settlement overcame the challenge. "
                f"Boon received: {challenge_result.get('boon', 'none')}."
            )
        else:
            result_text = (
                f"The settlement failed the challenge. "
                f"Leadership has shifted to {challenge_result.get('new_leader', 'another faction')}."
            )

        # Build previous context
        prev_block = ""
        if previous_chronicles:
            prev_lines = []
            for i, chron in enumerate(previous_chronicles):
                name = previous_era_names[i] if previous_era_names and i < len(previous_era_names) else f"Generation {i+1}"
                prev_lines.append(f"  Gen {i+1} ({name}): {chron[:150]}...")
            prev_block = "PREVIOUS GENERATIONS (do NOT repeat these themes or titles):\n" + "\n".join(prev_lines)

        era_names_block = ""
        if previous_era_names:
            era_names_block = f"\nPERIOD NAMES ALREADY USED (choose a NEW, DIFFERENT name):\n  {', '.join(previous_era_names)}\n"

        prompt = f"""\
You are the chronicler of a fantasy settlement. You record history as it unfolds.

SETTLEMENT STATE AT END OF GENERATION {round_num}:
{state_summary}

{prev_block}
{era_names_block}
WHAT THE FACTIONS SAID AND DID THIS GENERATION:
{era_narrative}

CHALLENGE OUTCOME:
{result_text}

A generation has passed. Write TWO sections:

SECTION 1 — THE CHRONICLE (4-6 sentences):
Close this historical period. Describe what changed permanently: which communities rose, \
which declined, what the children of this generation will inherit. Name this period something \
NEW and DIFFERENT from previous periods. Reference any named historical figures from this era.

SECTION 2 — A TRAVELER ARRIVES (3-4 sentences):
Describe what a traveler would experience arriving at the settlement RIGHT NOW. What do they \
see first? What sounds and smells reach them? What food is offered? What do the people look \
like, wear, do? What buildings or structures dominate the skyline? What goods are being \
traded in the market (if one exists)? Make it vivid, sensory, and specific to the current \
stage of development. If it's scattered camps, it should feel like frontier survival. If \
it's a city-state, it should feel like arriving at a capital.

VOICE CONSTRAINT: Write as a historian closing a chapter. No tokens, rolls, victory points, \
strategies, or game mechanics. No words like "faction," "phase," "era," "points," or "unlocked." \
Refer to groups by their nature and character.
"""
        return self._call_llm(prompt, round_num, "end_of_era")

    def narrate_culture_purchase(
        self,
        round_num: int,
        category: str,
        option: str,
        purchaser: str,
        settlement_name: str,
    ) -> AgentOutput:
        prompt = f"""\
You are the chronicler of {settlement_name}. You record history as it unfolds.

A CULTURAL SHIFT HAS TAKEN ROOT:
The people of {settlement_name} have embraced a new way: {option} — a shift in how the community \
understands {category}. This was driven by {purchaser}.

This shift took root over a generation — it was not a decree but a gradual transformation. \
In 3-4 sentences, chronicle how this changed the community permanently. How do the children \
of this generation grow up differently than their parents? What old ways were abandoned? \
What new assumptions do people carry without questioning?

VOICE CONSTRAINT: Write as a witness to living history, not a game commentator. Do NOT mention \
tokens, victory points, unlocks, purchases, upgrades, levels, or any game mechanics. \
No faction labels. No metagaming language. Describe the lived reality of this change.
"""
        return self._call_llm(prompt, round_num, "culture_purchase", max_tokens=256)

    def narrate_strategy_phase(
        self,
        round_num: int,
        state_summary: str,
        faction_summaries: list[dict],
        faction_narratives: list[str] | None = None,
        mode: str = "summary",
    ) -> AgentOutput:
        if mode == "narrative" and faction_narratives:
            source_block = "WHAT THE PEOPLE DID THIS ERA:\n" + "\n\n".join(faction_narratives)
        else:
            lines = []
            for fs in faction_summaries:
                if fs["tokens_earned"] == 0:
                    outcome = "their efforts yielded nothing"
                elif fs["tokens_earned"] <= 2:
                    outcome = "modest gains"
                elif fs["tokens_earned"] <= 5:
                    outcome = "strong results"
                else:
                    outcome = "an exceptional bounty"
                lines.append(f"- {fs['name']}: focused on {fs['activity']} — {outcome}")
            source_block = "WHAT HAPPENED:\n" + "\n".join(lines)

        prompt = f"""\
You are the chronicler of a fantasy settlement. You record history as it unfolds.

SETTLEMENT STATE:
{state_summary}

{source_block}

A generation has passed. Write 3-4 sentences summarizing what the settlement's people accomplished \
across these decades. Describe the work of a lifetime: what was built, what traditions took root, \
how the landscape changed under sustained effort. What will this generation be remembered for?

VOICE CONSTRAINT: Write as a historian. No tokens, rolls, victory points, strategies, or game \
mechanics. Ground every observation in the lived reality of generations.
"""
        return self._call_llm(prompt, round_num, "strategy_summary", max_tokens=256)

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
            state_patch={},
        )
