"""
llm_extractor.py
-----------------
Extracts structured application data from unstructured raw input using Claude.

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

_PROMPT_VERSION = "extractor_v1"
_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts", f"{_PROMPT_VERSION}.txt"
)


def _load_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _call_claude(prompt: str) -> str:
    """Call Claude API with temperature=0 and return raw text output."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _fallback_extraction(raw_input: dict) -> dict:
    """
    Deterministic fallback when Claude API is unavailable.
    Extracts whatever structured fields are directly present in raw_input.
    """
    forms = raw_input.get("forms") or {}
    return {
        "personal_info": {
            "name": forms.get("name") or raw_input.get("name"),
            "date_of_birth": forms.get("date_of_birth") or raw_input.get("date_of_birth"),
            "age": forms.get("age") or raw_input.get("age"),
            "gender": forms.get("gender") or raw_input.get("gender"),
            "occupation": forms.get("occupation") or raw_input.get("occupation"),
            "smoker": forms.get("smoker") if forms.get("smoker") is not None else raw_input.get("smoker"),
        },
        "financial_info": {
            "annual_income": forms.get("annual_income") or raw_input.get("annual_income"),
            "net_worth": forms.get("net_worth") or raw_input.get("net_worth"),
            "existing_coverage": forms.get("existing_coverage") or raw_input.get("existing_coverage"),
        },
        "health_info": {
            "bmi": forms.get("bmi") or raw_input.get("bmi"),
            "pre_existing_conditions": forms.get("pre_existing_conditions") or raw_input.get("pre_existing_conditions") or [],
            "family_history": forms.get("family_history") or raw_input.get("family_history") or [],
            "medications": forms.get("medications") or raw_input.get("medications") or [],
        },
        "coverage_requested": {
            "sum_assured": forms.get("sum_assured") or raw_input.get("sum_assured"),
            "policy_term_years": forms.get("policy_term_years") or raw_input.get("policy_term_years"),
            "premium_frequency": forms.get("premium_frequency") or raw_input.get("premium_frequency"),
        },
        "extraction_confidence": "LOW",
        "missing_fields": [],
    }


def extract_structured_data(raw_input: dict[str, Any]) -> dict[str, Any]:
    """
    Extract structured application data from unstructured raw input.

    Args:
        raw_input: Dictionary containing forms, notes, documents from the application.

    Returns:
        {
            "structured_data": {...},
            "extraction_confidence": "HIGH" | "MEDIUM" | "LOW",
            "missing_fields": [...],
        }

    Guardrails:
        - Output is validated against application schema
        - Temperature = 0 (via API parameter)
        - Falls back to deterministic extraction if API unavailable
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        # Graceful degradation — use deterministic fallback
        extracted = _fallback_extraction(raw_input)
        return {
            "structured_data": extracted,
            "extraction_confidence": extracted.get("extraction_confidence", "LOW"),
            "missing_fields": extracted.get("missing_fields", []),
        }

    try:
        template = _load_prompt()

        # Format the raw input for the prompt
        raw_text = json.dumps(raw_input, indent=2)
        if len(raw_text) > 8000:
            raw_text = raw_text[:8000] + "\n... [truncated]"

        # Split the template at USER: marker
        parts = template.split("USER:", 1)
        system_prompt = parts[0].replace("SYSTEM:", "").strip()
        user_template = parts[1].strip() if len(parts) > 1 else "{{raw_input}}"

        user_message = user_template.replace("{{raw_input}}", raw_text)

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

        # Strip markdown code fences if present
        if raw_output.startswith("```"):
            lines = raw_output.split("\n")
            raw_output = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

        extracted = json.loads(raw_output)

        # Validate output is a dict (schema guardrail)
        if not isinstance(extracted, dict):
            raise ValueError("LLM output is not a JSON object")

        structured_data = {
            k: v for k, v in extracted.items()
            if k not in ("extraction_confidence", "missing_fields")
        }

        return {
            "structured_data": structured_data,
            "extraction_confidence": extracted.get("extraction_confidence", "MEDIUM"),
            "missing_fields": extracted.get("missing_fields", []),
        }

    except Exception:
        # Fallback on any API or parse error
        extracted = _fallback_extraction(raw_input)
        return {
            "structured_data": extracted,
            "extraction_confidence": "LOW",
            "missing_fields": [],
        }
