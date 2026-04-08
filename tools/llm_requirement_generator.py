"""
llm_requirement_generator.py
------------------------------
Generates requirement lists for incomplete underwriting applications using Claude.

LLM Guardrails (WAT Framework v3):
  - Temperature = 0
  - JSON output only
  - Must pass schema validation (output bound to allowed schema fields)
  - Cannot trigger workflows
  - Cannot make decisions
"""

from __future__ import annotations

import json
import os
from typing import Any

_PROMPT_VERSION = "requirement_v1"
_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts", f"{_PROMPT_VERSION}.txt"
)


def _load_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _fallback_requirements(
    application_data: dict,
    risk_flags: list,
    missing_fields: list,
) -> dict:
    """Deterministic fallback — delegates to requirement_engine."""
    from tools.requirement_engine import identify_requirements
    return identify_requirements(application_data, risk_flags)


def generate_requirements(
    application_data: dict[str, Any],
    risk_flags: list[dict[str, Any]],
    missing_fields: list[str],
) -> dict[str, Any]:
    """
    Generate a list of requirements needed to proceed with underwriting.

    Args:
        application_data: Current structured application data.
        risk_flags:       Risk flags from the rule engine.
        missing_fields:   Fields identified as missing by the extractor.

    Returns:
        {
            "requirements": [...],
            "can_proceed_without": [...],
            "blocking_requirements": [...],
            "estimated_fulfillment_days": int,
        }

    Guardrails:
        - All field_name values are validated against allowed schema fields
        - Temperature = 0
        - Falls back to deterministic requirement_engine if API unavailable
    """
    _ALLOWED_FIELDS = {
        "personal_info.date_of_birth", "personal_info.smoker",
        "personal_info.occupation", "financial_info.annual_income",
        "financial_info.net_worth", "financial_info.existing_coverage",
        "health_info.bmi", "health_info.pre_existing_conditions",
        "health_info.medications", "coverage_requested.sum_assured",
        "coverage_requested.policy_term_years",
        "health_info.medical_exam", "health_info.treating_physician_report",
        "health_info.smoking_cessation_history", "financial_info.net_worth",
    }

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return _fallback_requirements(application_data, risk_flags, missing_fields)

    try:
        template = _load_prompt()

        parts = template.split("USER:", 1)
        system_prompt = parts[0].replace("SYSTEM:", "").strip()
        user_template = parts[1].strip() if len(parts) > 1 else ""

        user_message = (
            user_template
            .replace("{{application_data}}", json.dumps(application_data, indent=2)[:4000])
            .replace("{{risk_flags}}", json.dumps(risk_flags, indent=2)[:2000])
            .replace("{{missing_fields}}", json.dumps(missing_fields))
        )

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

        if not isinstance(result, dict) or "requirements" not in result:
            raise ValueError("Invalid requirements output structure")

        # Guardrail: only allow schema-bound field names
        filtered_requirements = [
            req for req in result.get("requirements", [])
            if req.get("field_name") in _ALLOWED_FIELDS
        ]
        result["requirements"] = filtered_requirements
        result["blocking_requirements"] = [
            r["field_name"] for r in filtered_requirements
            if r.get("priority") == "REQUIRED"
        ]

        return result

    except Exception:
        return _fallback_requirements(application_data, risk_flags, missing_fields)
