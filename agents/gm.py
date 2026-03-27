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
        previous_chronicle: str | None = None,
        strategy_summary: str | None = None,
        previous_challenges: list[str] | None = None,
    ) -> AgentOutput:
        prev_block = ""
        if previous_chronicle:
            prev_block = f"\nWHAT CAME BEFORE (the previous generation's legacy):\n{previous_chronicle[:400]}\n"

        strat_block = ""
        if strategy_summary:
            strat_block = f"\nWHAT THE PEOPLE WERE DOING WHEN THE CRISIS STRUCK:\n{strategy_summary[:400]}\n"

        prev_challenges_block = ""
        if previous_challenges:
            prev_challenges_block = (
                "\nPREVIOUS CRISES THIS SETTLEMENT HAS FACED:\n"
                + "\n".join(f"  - Gen {i+1}: {c}" for i, c in enumerate(previous_challenges))
                + "\n\nIf this new crisis has a thematic or causal connection to a previous one "
                "(e.g., both are magical, both relate to the same resource, or the current crisis "
                "is a consequence of how a previous one was resolved), draw that connection. "
                "History rhymes.\n"
            )

        prompt = f"""\
You are the chronicler of a fantasy settlement. You record history as it unfolds.

SETTLEMENT STATE:
{state_summary}
{prev_block}{strat_block}{prev_challenges_block}
THE CRISIS OF THIS AGE: "{challenge_text}"

Consider HOW this crisis connects to what came before. Is it:
- A CONSEQUENCE of the settlement's choices? (They ignored warnings, overextended, \
  neglected something vital, or their success created new vulnerabilities)
- An UNKNOWABLE disruption? (Something no one could have predicted that forces the \
  community to rethink everything they assumed was true)
- A FORETOLD reckoning? (Signs were there — did the people prepare, ignore them, \
  or reject the warnings?)

The best history reads like inevitability in hindsight. Plant the seeds: reference specific \
decisions, structures, or cultural shifts from earlier that made this crisis hit harder — or \
that gave the people tools they didn't know they'd need.

In 3-5 sentences, chronicle what befell the people. Name specific places and historical \
figures. Set the stakes in generational terms. Do not resolve the crisis yet.

VOICE CONSTRAINT: Write as a historian looking back across decades or centuries. No tokens, \
rolls, victory points, or game mechanics.
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

THE CRISIS OF THIS AGE:
{challenge_text}

THE LEADER'S PLAN:
{leader_plan}

HOW THE SETTLEMENT RESPONDED:
{donation_summary}

OUTCOME: The settlement {outcome_word}.
{boon_line}

This crisis defined an age. Write 3-5 sentences describing what happened over the decades \
or centuries it took to resolve.

Connect the outcome to the settlement's larger arc:
- If they PREVAILED: What earlier choices, structures, or cultural values gave them the \
  strength to endure? What scars remain alongside the triumph? What new vulnerability has \
  their success created? (Every victory plants the seeds of a future crisis.)
- If they FAILED: What weakness was exposed — was it structural, cultural, or leadership? \
  What was permanently lost? What desperate adaptation will define the next generation?

Reference specific named historical figures, structures, and places. Name the individual \
most associated with this crisis. End with their name and deed:

HISTORICAL FIGURE: [name] — [one sentence deed]

VOICE CONSTRAINT: No tokens, rolls, victory points, or game mechanics.
"""
        return self._call_llm(prompt, round_num, "challenge_outcome", max_tokens=512)

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
        return self._call_llm(prompt, round_num, "boon_narration", max_tokens=384)

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

Decades or centuries have passed. Write TWO sections:

First, close this historical period in 4-6 sentences. Describe what changed permanently: which \
communities rose, which declined, what the children of this generation will inherit. Name this \
period something NEW and DIFFERENT from previous periods. Reference any named historical figures.

Then, seamlessly transition to describing the settlement as it stands now — what a traveler \
would experience arriving at this moment. In 3-4 sentences: what do they see first? What sounds \
and smells reach them? What food is offered? What do the people wear, build, trade? Make it \
vivid, sensory, and specific to the current stage of development. If it's scattered camps, \
it should feel like frontier survival. If it's a city-state, it should feel like arriving \
at a capital. Do NOT use section labels or headers — let it flow naturally from the chronicle.

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

This shift took root over decades or centuries. In 3-4 sentences, chronicle how this changed \
the community permanently. Name the individual most responsible — someone whose name will be \
remembered for this transformation. End with their name and deed in this format:

HISTORICAL FIGURE: [name] — [one sentence deed]

VOICE CONSTRAINT: No tokens, victory points, unlocks, purchases, upgrades, levels, or game \
mechanics. No faction labels. Describe the lived reality of this change.
"""
        return self._call_llm(prompt, round_num, "culture_purchase", max_tokens=384)

    def narrate_strategy_phase(
        self,
        round_num: int,
        state_summary: str,
        faction_summaries: list[dict],
        mode: str = "summary",
    ) -> AgentOutput:
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
            label = fs.get("label", fs["name"])
            lines.append(f"- {label}: focused on {fs['activity']} — {outcome}")
        source_block = "WHAT EACH FACTION DID:\n" + "\n".join(lines)

        prompt = f"""\
You are the chronicler of a fantasy settlement.

SETTLEMENT STATE:
{state_summary}

{source_block}

Write a short chronicle of this age. For each faction, write 2-3 sentences in third person \
describing what they accomplished across decades or centuries. Use their full name. Then end \
with 1-2 sentences about what the settlement as a whole achieved and what remains fragile.

Write as a historian. Describe the work of generations: what was built, what traditions took root, \
how the landscape changed under sustained effort.

End with a hint of what's unresolved or fragile — something the people haven't noticed, \
something they're neglecting, or a tension that's growing beneath the surface. The reader \
should feel that prosperity and crisis are two sides of the same coin.

VOICE CONSTRAINT: Write as a historian. No tokens, rolls, victory points, strategies, or game \
mechanics. Ground every observation in the lived reality of generations.
"""
        return self._call_llm(prompt, round_num, "strategy_summary", max_tokens=1024)

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
