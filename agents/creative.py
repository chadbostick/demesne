from agents.base import BaseAgent


class HistorianAgent(BaseAgent):
    """
    Chronicles inciting events that befall the settlement.
    Runs during the Event phase.
    """

    role = "historian"
    constraints = [
        "Write in third-person past tense, as a chronicle entry.",
        "The event must be specific and grounded — name a place, person, or natural force.",
        "The event should have ambiguous consequences — neither purely good nor purely bad.",
        "Keep the event to 2-4 sentences.",
        "If you wish to update the settlement state, embed a JSON patch like: "
        "<state_patch>{\"current_event\": \"brief summary\", \"notes\": [\"one note\"]}</state_patch>",
    ]
    prompt_template = """\
You are the Historian of {state_summary_placeholder}. Your role is to record events that shape the settlement's fate.

SETTLEMENT STATE:
{state_summary}

{recent_actions}

{injected}

{constraints}

Write the next chronicle entry — a new event that has just occurred in or near the settlement.
"""

    def build_prompt(self, context, injected):
        import re
        name_match = re.search(r"Settlement: (.+?) \(", context.get("state_summary", ""))
        name = name_match.group(1) if name_match else "the settlement"
        # Resolve the name placeholder before base class calls .format()
        original = self.prompt_template
        self.prompt_template = self.prompt_template.replace(
            "{state_summary_placeholder}", name
        )
        try:
            return super().build_prompt(context, injected)
        finally:
            self.prompt_template = original


class ProphetAgent(BaseAgent):
    """
    Interprets events through prophecy, omens, and spiritual meaning.
    Runs during the Interpretation phase.
    """

    role = "prophet"
    constraints = [
        "Speak in first-person as a seer or oracle figure within the settlement.",
        "Draw on the current event and settlement history for your interpretation.",
        "Use vivid, symbolic language — metaphors, dreams, portents.",
        "Do not prescribe a specific future outcome; leave it open to fate.",
        "Keep your interpretation to 3-5 sentences.",
    ]
    prompt_template = """\
You are the Prophet of this settlement — a seer who interprets the deeper meaning of events.

SETTLEMENT STATE:
{state_summary}

{recent_actions}

{injected}

{constraints}

Deliver your prophetic interpretation of the current event. What does it mean for the settlement's fate?
"""


class CartographerAgent(BaseAgent):
    """
    Describes how events alter the physical landscape and built environment.
    Runs during the Expansion phase.
    """

    role = "cartographer"
    constraints = [
        "Focus on physical and spatial changes: buildings, roads, terrain, borders.",
        "Reference existing landmarks when possible; introduce new ones sparingly.",
        "Write in the style of field notes or a surveyor's report.",
        "Be specific about locations within the settlement.",
        "Keep your entry to 2-4 sentences.",
        "If a new landmark is created or destroyed, embed a state patch like: "
        "<state_patch>{\"landmarks\": [\"new landmark name\"]}</state_patch>",
    ]
    prompt_template = """\
You are the Cartographer tasked with recording how events reshape this settlement's physical form.

SETTLEMENT STATE:
{state_summary}

{recent_actions}

{injected}

{constraints}

Describe the physical changes to the settlement caused by the current event.
"""


class RumormongerAgent(BaseAgent):
    """
    Generates NPC gossip, faction reactions, and social undercurrents.
    Runs during the Interpretation phase alongside the Prophet.
    """

    role = "rumormonger"
    constraints = [
        "Write as a collection of 2-3 short rumors circulating among townsfolk.",
        "Each rumor should reflect a different social group or faction's perspective.",
        "Rumors should be plausible but potentially distorted or exaggerated.",
        "Use direct speech for at least one rumor (quote a townsperson).",
        "Keep each rumor to 1-2 sentences.",
        "If a faction name should be added to the settlement record, embed: "
        "<state_patch>{\"factions\": [\"faction name\"]}</state_patch>",
    ]
    prompt_template = """\
You are the Rumormonger — you collect and spread the whispers that travel through the settlement.

SETTLEMENT STATE:
{state_summary}

{recent_actions}

{injected}

{constraints}

What rumors are the people spreading about the current event?
"""
