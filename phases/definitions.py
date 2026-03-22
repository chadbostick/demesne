from dataclasses import dataclass, field


@dataclass
class RiffingRule:
    """
    Defines a conditional injection of one agent's output into another's prompt.

    condition options:
      "always"                  – always inject
      "if_keyword:<word>"       – inject only if source output contains <word>
      "if_round_gt:<n>"         – inject only if current round > n
    """
    source_role: str
    target_role: str
    condition: str = "always"
    excerpt_lines: int = 5      # how many lines of source output to inject


@dataclass
class PhaseConfig:
    name: str
    description: str
    agent_roles: list[str] = field(default_factory=list)
    riffing_rules: list[RiffingRule] = field(default_factory=list)


# ── Default 4-phase sequence ──────────────────────────────────────────────────

EVENT_PHASE = PhaseConfig(
    name="event",
    description="The Historian generates an inciting event that befalls the settlement.",
    agent_roles=["historian"],
    riffing_rules=[],
)

INTERPRETATION_PHASE = PhaseConfig(
    name="interpretation",
    description="The Prophet and Rumormonger interpret the event's meaning.",
    agent_roles=["prophet", "rumormonger"],
    riffing_rules=[
        # Rumormonger sees the Prophet's interpretation first
        RiffingRule(
            source_role="prophet",
            target_role="rumormonger",
            condition="always",
            excerpt_lines=5,
        ),
    ],
)

EXPANSION_PHASE = PhaseConfig(
    name="expansion",
    description="The Cartographer expands on physical and social consequences.",
    agent_roles=["cartographer"],
    riffing_rules=[
        # Cartographer is fed the Historian's event and Prophet's interpretation
        RiffingRule(
            source_role="historian",
            target_role="cartographer",
            condition="always",
            excerpt_lines=4,
        ),
        RiffingRule(
            source_role="prophet",
            target_role="cartographer",
            condition="always",
            excerpt_lines=3,
        ),
    ],
)

CONSEQUENCE_PHASE = PhaseConfig(
    name="consequence",
    description=(
        "The Arbiter collects all state patches from this round and applies them "
        "to the Settlement State. No agents run — this is a deterministic merge step."
    ),
    agent_roles=[],   # Arbiter-only: no agent calls
    riffing_rules=[],
)

DEFAULT_PHASES: list[PhaseConfig] = [
    EVENT_PHASE,
    INTERPRETATION_PHASE,
    EXPANSION_PHASE,
    CONSEQUENCE_PHASE,
]
