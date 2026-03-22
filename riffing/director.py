from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from phases.definitions import PhaseConfig, RiffingRule
    from agents.base import AgentOutput


class RiffingDirector:
    """
    Evaluates RiffingRules and extracts injected excerpts for a target agent.
    """

    def resolve(
        self,
        phase: "PhaseConfig",
        target_role: str,
        prior_outputs: dict[str, "AgentOutput"],
        round_num: int,
    ) -> Optional[str]:
        """
        Returns a combined injection string (or None) for target_role,
        based on the phase's riffing_rules and the outputs produced so far
        in this round.
        """
        injections: list[str] = []

        for rule in phase.riffing_rules:
            if rule.target_role != target_role:
                continue

            source_output = prior_outputs.get(rule.source_role)
            if source_output is None:
                continue  # source hasn't run yet this phase

            if not self._condition_met(rule, source_output, round_num):
                continue

            excerpt = self._excerpt(source_output.content, rule.excerpt_lines)
            injections.append(
                f"[From {rule.source_role.title()}]:\n{excerpt}"
            )

        return "\n\n".join(injections) if injections else None

    # ── Private helpers ───────────────────────────────────────────────────────

    def _condition_met(
        self,
        rule: "RiffingRule",
        source_output: "AgentOutput",
        round_num: int,
    ) -> bool:
        cond = rule.condition

        if cond == "always":
            return True

        if cond.startswith("if_keyword:"):
            keyword = cond.split(":", 1)[1].lower()
            return keyword in source_output.content.lower()

        if cond.startswith("if_round_gt:"):
            threshold = int(cond.split(":", 1)[1])
            return round_num > threshold

        # Unknown condition — skip
        return False

    def _excerpt(self, text: str, n_lines: int) -> str:
        lines = [l for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:n_lines])
