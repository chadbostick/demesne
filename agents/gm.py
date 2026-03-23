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
    prompt_template = ""  # not used directly

    def build_prompt(self, context: dict, injected) -> str:
        return ""

    def run(self, context: dict, round_num: int, phase: str, injected=None) -> AgentOutput:
        raise NotImplementedError("Use narrate_challenge() or narrate_end_of_era() directly.")

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

A CHALLENGE has befallen the settlement this era:
{challenge_text}

In 2-4 sentences, narrate this challenge in vivid, grounded prose. Set the stakes. Describe what
is at risk for the people of this settlement. Do not resolve the challenge yet — only introduce it.

VOICE CONSTRAINT: Write as a witness to real events. Do NOT mention tokens, rolls, victory points,
game mechanics, or faction names as organizational labels. Refer to factions by their character and
ideology, not as "factions." No metagaming language of any kind.
"""
        return self._call_llm(prompt, round_num, "challenge_narration")

    def narrate_end_of_era(
        self,
        context: dict,
        round_num: int,
        era_outputs: list[dict],
        state_summary: str,
        challenge_result: dict,
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

        prompt = f"""\
You are the chronicler of a fantasy settlement. You record history as it unfolds.

SETTLEMENT STATE AT END OF ERA {round_num}:
{state_summary}

WHAT THE FACTIONS SAID AND DID THIS ERA:
{era_narrative}

CHALLENGE OUTCOME:
{result_text}

Write a 3-5 sentence End of Era chronicle. Describe how the settlement has changed, which groups
gained or lost influence, and what the era's events mean for the people living here.

VOICE CONSTRAINT: Write as a witness to real history — a chronicler, not a game commentator.
Do NOT mention tokens, rolls, victory points, strategies, or any game mechanics. Do NOT use
words like "faction," "phase," "era," "points," or "unlocked." Refer to groups by their nature
and ideology. No metagaming language of any kind. Ground every observation in the lives of settlers.
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

In 2-3 sentences, chronicle what this means for daily life. How do people live differently now? \
What has changed in the rhythm, the rituals, the relationships of the community? \
This is permanent — every settler lives within this now, whether they chose it or not.

VOICE CONSTRAINT: Write as a witness to living history, not a game commentator. Do NOT mention \
tokens, victory points, unlocks, purchases, upgrades, levels, or any game mechanics. \
No faction labels. No metagaming language. Describe the lived reality of this change.
"""
        return self._call_llm(prompt, round_num, "culture_purchase", max_tokens=256)

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
