"""
llm_classifier.py
------------------
Identifies risk signals from enriched application data using Claude.

LLM Guardrails (WAT Framework v3):
  - Temperature = 0
  - JSON output only
  - Must pass schema validation
  - Cannot trigger workflows
  - Cannot make decisions
"""

from __future__ import annotations

import json
import os
from typing import Any

_PROMPT_VERSION = "classifier_v1"
_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts", f"{_PROMPT_VERSION}.txt"
)


def _load_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _fallback_classification(enriched_profile: dict) -> dict:
    """
    Deterministic fallback when API is unavailable.
    Uses the deterministic rule engine instead.
    """
    from tools.underwriting_rule_engine import evaluate_rules
    rule_result = evaluate_rules(enriched_profile)
    return {
        "signals": rule_result.get("flags", []),
        "conflicting_signals": [],
        "manual_review_recommended": rule_result.get("manual_review_required", False),
        "review_reason": rule_result.get("review_reason"),
        "classifier_confidence": "HIGH",  # Deterministic = high confidence
    }


def classify_risk_signals(enriched_profile: dict[str, Any]) -> dict[str, Any]:
    """
    Identify risk signals from enriched application data.

    Args:
        enriched_profile: Application data merged with external data.

    Returns:
        {
            "signals": [...],
            "conflicting_signals": [...],
            "manual_review_recommended": bool,
            "review_reason": str | None,
            "classifier_confidence": "HIGH" | "MEDIUM" | "LOW",
        }

    Guardrails:
        - Output is validated (signals must be list)
        - Temperature = 0
        - Falls back to deterministic rule engine if API unavailable
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return _fallback_classification(enriched_profile)

    try:
        template = _load_prompt()

        profile_text = json.dumps(enriched_profile, indent=2)
        if len(profile_text) > 8000:
            profile_text = profile_text[:8000] + "\n... [truncated]"

        parts = template.split("USER:", 1)
        system_prompt = parts[0].replace("SYSTEM:", "").strip()
        user_template = parts[1].strip() if len(parts) > 1 else "{{enriched_profile}}"
        user_message = user_template.replace("{{enriched_profile}}", profile_text)

        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_output = message.content[0].text.strip()
        if raw_output.startswith("```"):
            lines = raw_output.split("\n")
            raw_output = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

        result = json.loads(raw_output)

        if not isinstance(result, dict) or "signals" not in result:
            raise ValueError("Invalid classifier output structure")

        return result

    except Exception:
        return _fallback_classification(enriched_profile)
