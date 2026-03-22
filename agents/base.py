from __future__ import annotations
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from textwrap import dedent
from typing import Optional

import anthropic
import config


@dataclass
class AgentOutput:
    agent_role: str
    phase: str
    round: int
    content: str
    state_patch: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "agent_role": self.agent_role,
            "phase": self.phase,
            "round": self.round,
            "content": self.content,
            "state_patch": self.state_patch,
            "timestamp": self.timestamp,
        }


class BaseAgent(ABC):
    """
    Abstract base for all creative agents.

    Subclasses must define:
      role              – short identifier (e.g. "historian")
      prompt_template   – string with placeholders:
                            {state_summary}, {recent_actions}, {injected}, {constraints}
      constraints       – list of rule strings appended to every prompt
    """

    role: str = "base"
    prompt_template: str = "{state_summary}\n\n{recent_actions}\n\n{injected}\n\n{constraints}"
    constraints: list[str] = []

    def build_prompt(self, context: dict, injected: Optional[str]) -> str:
        recent = context.get("recent_actions", [])
        if recent:
            recent_text = "Recent actions:\n" + "\n---\n".join(
                f"[Round {a['round']} / {a['phase']} / {a['agent']}]\n{a['content']}"
                for a in recent
            )
        else:
            recent_text = "No prior actions yet."

        constraints_text = (
            "Constraints:\n" + "\n".join(f"- {c}" for c in self.constraints)
            if self.constraints
            else ""
        )

        injected_text = (
            f"--- Riffing input ---\n{injected}\n--- End riffing input ---"
            if injected
            else ""
        )

        return self.prompt_template.format(
            state_summary=context.get("state_summary", ""),
            recent_actions=recent_text,
            injected=injected_text,
            constraints=constraints_text,
        )

    def run(self, context: dict, round_num: int, phase: str,
            injected: Optional[str] = None) -> AgentOutput:
        prompt = self.build_prompt(context, injected)
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=config.MODEL,
            max_tokens=1024,
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

    def _extract_state_patch(self, text: str) -> dict:
        """
        Agents may optionally embed a JSON state patch in their output like:
          <state_patch>{"current_event": "...", "notes": ["..."]}</state_patch>
        Returns {} if none found or if parsing fails.
        """
        import re
        match = re.search(r"<state_patch>(.*?)</state_patch>", text, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}
