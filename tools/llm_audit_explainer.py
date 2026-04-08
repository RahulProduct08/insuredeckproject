"""
llm_audit_explainer.py
-----------------------
Generates explainable reasoning for underwriting decisions using Claude.

LLM Guardrails (WAT Framework v3):
  - Temperature = 0
  - JSON output only
  - Must pass schema validation
  - Cannot trigger workflows
  - Cannot make decisions (only explains decisions already made)
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

_PROMPT_VERSION = "audit_v1"
_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts", f"{_PROMPT_VERSION}.txt"
)


def _load_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _fallback_explanation(
    decision: str,
    application_summary: dict,
    risk_profile: dict,
    rules_applied: list,
) -> dict:
    """Deterministic fallback explanation when API is unavailable."""
    risk_score = risk_profile.get("risk_score", "N/A")
    risk_class = risk_profile.get("risk_class", "N/A")

    summary_map = {
        "APPROVED": f"Application approved. Risk score {risk_score}, class {risk_class} — within acceptable limits.",
        "APPROVED_WITH_CONDITIONS": f"Application approved with conditions. Risk score {risk_score}, class {risk_class} — conditions apply to manage identified risks.",
        "REJECTED": f"Application rejected. Risk score {risk_score}, class {risk_class} — exceeds maximum acceptable risk threshold.",
        "PENDED": f"Application pending. Risk score {risk_score} — requires additional information or manual underwriter review.",
    }

    return {
        "summary": summary_map.get(decision, f"Decision: {decision}. Risk score: {risk_score}."),
        "decision_rationale": f"Based on risk score of {risk_score} and classification of {risk_class}.",
        "risk_factors_considered": [
            f["description"] for f in (risk_profile.get("risk_flags") or [])
        ][:5],
        "rules_applied": rules_applied[:5],
        "mitigating_factors": [],
        "conditions_explained": [],
        "appeal_guidance": "To appeal this decision, contact the underwriting team with supporting documentation." if decision == "REJECTED" else None,
        "compliance_notes": "Decision generated per underwriting SOP WAT-v3. Audit trail maintained.",
        "prompt_version": "fallback_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_audit_explanation(
    decision: str,
    application_summary: dict[str, Any],
    risk_profile: dict[str, Any],
    rules_applied: list[str],
) -> dict[str, Any]:
    """
    Generate a plain-language audit explanation for an underwriting decision.

    Args:
        decision:            Final decision string (APPROVED, REJECTED, etc.)
        application_summary: Sanitized application data (no PII sent to LLM).
        risk_profile:        Risk profile dict with score, class, flags.
        rules_applied:       List of rule descriptions that led to the decision.

    Returns:
        {
            "summary": str,
            "decision_rationale": str,
            "risk_factors_considered": [...],
            "rules_applied": [...],
            "mitigating_factors": [...],
            "conditions_explained": [...],
            "appeal_guidance": str | None,
            "compliance_notes": str,
            "prompt_version": str,
            "generated_at": str,
        }

    Guardrails:
        - PII fields stripped before sending to LLM
        - Temperature = 0
        - Output validated as dict with "summary" key
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return _fallback_explanation(decision, application_summary, risk_profile, rules_applied)

    try:
        template = _load_prompt()

        # Strip PII before sending to LLM
        safe_summary = _strip_pii(application_summary)
        safe_risk = _strip_pii(risk_profile)

        parts = template.split("USER:", 1)
        system_prompt = parts[0].replace("SYSTEM:", "").strip()
        user_template = parts[1].strip() if len(parts) > 1 else ""

        user_message = (
            user_template
            .replace("{{decision}}", decision)
            .replace("{{application_summary}}", json.dumps(safe_summary, indent=2)[:3000])
            .replace("{{risk_profile}}", json.dumps(safe_risk, indent=2)[:2000])
            .replace("{{rules_applied}}", json.dumps(rules_applied[:10]))
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

        if not isinstance(result, dict) or "summary" not in result:
            raise ValueError("Invalid audit explanation output structure")

        result["prompt_version"] = _PROMPT_VERSION
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        return result

    except Exception:
        return _fallback_explanation(decision, application_summary, risk_profile, rules_applied)


def log_audit_event(
    application_id: str,
    input_data: dict,
    tool_called: str,
    output: dict,
    prompt_version: str | None = None,
    validation_status: str = "VALID",
) -> str:
    """
    Write an entry to underwriting_audit_logs.

    This is a utility called by workflows to maintain the audit trail.
    Returns the log_id.
    """
    from database import get_db

    log_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO underwriting_audit_logs
               (log_id, application_id, input, tool_called, prompt_version,
                output, validation_status, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                log_id, application_id,
                json.dumps(input_data), tool_called, prompt_version,
                json.dumps(output), validation_status, now,
            )
        )
        conn.commit()
    finally:
        conn.close()

    return log_id


def _strip_pii(data: dict) -> dict:
    """Remove PII fields before sending data to LLM."""
    _PII_FIELDS = {"name", "date_of_birth", "phone", "email", "address", "ssn", "tax_id"}
    if not isinstance(data, dict):
        return data
    return {
        k: _strip_pii(v) if isinstance(v, dict) else v
        for k, v in data.items()
        if k not in _PII_FIELDS
    }
