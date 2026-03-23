from dataclasses import dataclass, field


@dataclass
class PhaseConfig:
    name: str
    description: str
    # No agent_roles here — agents are dispatched dynamically by Arbiter based on faction list


STRATEGY_PHASE = PhaseConfig(
    name="strategy",
    description=(
        "Each faction chooses a strategy (Pray, Discuss, Lead, Organize, Forage, or Make). "
        "The GM rolls a d20 per faction and awards tokens based on the payout table."
    ),
)

INVESTMENT_PHASE = PhaseConfig(
    name="investment",
    description=(
        "Factions spend tokens to unlock Culture upgrades. Prerequisites must be met (L1 before L2, etc.). "
        "Factions may pool tokens or block opponents by purchasing opposing options."
    ),
)

CHALLENGE_PHASE = PhaseConfig(
    name="challenge",
    description=(
        "A settlement-wide challenge is drawn. The Leading Faction decides the response. "
        "All factions may donate tokens (+1 per token to the d20 roll). "
        "10+ = success (boon + leading faction stays); 9 or less = failure (new leading faction)."
    ),
)

END_OF_ERA_PHASE = PhaseConfig(
    name="end_of_era",
    description=(
        "The GM summarizes the era's events, faction power shifts, and settlement changes. "
        "VP is calculated. Victory condition is checked."
    ),
)

DEFAULT_PHASES: list[PhaseConfig] = [
    STRATEGY_PHASE,
    INVESTMENT_PHASE,
    CHALLENGE_PHASE,
    END_OF_ERA_PHASE,
]
