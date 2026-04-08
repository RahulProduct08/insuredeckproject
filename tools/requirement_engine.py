"""
requirement_engine.py
-----------------------
Determines missing requirements for a pending underwriting application.

This tool is deterministic — it inspects the structured data for null/missing
fields and cross-references with risk flags to determine what information
is needed to proceed.

Does NOT use LLMs. See llm_requirement_generator.py for the LLM-assisted version.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Required field definitions
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = [
    {
        "field_name": "personal_info.age",
        "description": "Applicant date of birth or age",
        "priority": "REQUIRED",
        "document_type": "Government-issued ID or birth certificate",
        "reason": "Age is required to assess mortality risk and product eligibility",
    },
    {
        "field_name": "financial_info.annual_income",
        "description": "Verified annual income",
        "priority": "REQUIRED",
        "document_type": "Tax return or payslip (last 2 years)",
        "reason": "Income verification is required to assess coverage appropriateness",
    },
    {
        "field_name": "coverage_requested.sum_assured",
        "description": "Requested sum assured amount",
        "priority": "REQUIRED",
        "document_type": None,
        "reason": "Sum assured is required to calculate premium and assess coverage ratio",
    },
]

_PREFERRED_FIELDS = [
    {
        "field_name": "health_info.bmi",
        "description": "Height and weight for BMI calculation",
        "priority": "PREFERRED",
        "document_type": "Medical examination report",
        "reason": "BMI improves risk classification accuracy",
    },
    {
        "field_name": "health_info.pre_existing_conditions",
        "description": "List of any pre-existing medical conditions",
        "priority": "PREFERRED",
        "document_type": "Medical records or physician statement",
        "reason": "Pre-existing conditions affect risk class and exclusion clauses",
    },
    {
        "field_name": "financial_info.net_worth",
        "description": "Approximate net worth",
        "priority": "PREFERRED",
        "document_type": "Financial statement",
        "reason": "Net worth provides additional financial underwriting context",
    },
]

# Flag codes that trigger additional requirements
_FLAG_REQUIREMENTS = {
    "AGE_SENIOR": {
        "field_name": "health_info.medical_exam",
        "description": "Full medical examination report for applicants aged 60+",
        "priority": "REQUIRED",
        "document_type": "Medical examination report (within 90 days)",
        "reason": "Senior applicants require a medical exam for underwriting",
    },
    "COVERAGE_RATIO_HIGH": {
        "field_name": "financial_info.net_worth",
        "description": "Net worth statement to support high coverage request",
        "priority": "REQUIRED",
        "document_type": "Certified financial statement",
        "reason": "High coverage-to-income ratio requires net worth verification",
    },
    "PRE_EXISTING_HIGH": {
        "field_name": "health_info.treating_physician_report",
        "description": "Physician's report on pre-existing condition status and treatment",
        "priority": "REQUIRED",
        "document_type": "Attending physician statement (APS)",
        "reason": "High-risk pre-existing conditions require physician documentation",
    },
    "SMOKER": {
        "field_name": "health_info.smoking_cessation_history",
        "description": "Smoking history including pack-years and cessation attempts",
        "priority": "PREFERRED",
        "document_type": "Self-declaration form",
        "reason": "Smoking history details affect premium loading calculation",
    },
}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def identify_requirements(
    structured_data: dict[str, Any],
    risk_flags: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Identify missing information required to proceed with underwriting.

    Args:
        structured_data: Current structured application data.
        risk_flags:      Risk flags from underwriting_rule_engine (may be empty).

    Returns:
        {
            "requirements": [...],
            "can_proceed_without": [...],
            "blocking_requirements": [...],
            "estimated_fulfillment_days": int,
        }
    """
    requirements: list[dict] = []
    seen_fields: set[str] = set()

    personal = structured_data.get("personal_info") or {}
    financial = structured_data.get("financial_info") or {}
    health = structured_data.get("health_info") or {}
    coverage = structured_data.get("coverage_requested") or {}

    # ------------------------------------------------------------------
    # Check required fields
    # ------------------------------------------------------------------
    _check_field(
        requirements, seen_fields, _REQUIRED_FIELDS[0],
        personal.get("age") is None and personal.get("date_of_birth") is None
    )
    _check_field(
        requirements, seen_fields, _REQUIRED_FIELDS[1],
        financial.get("annual_income") is None
    )
    _check_field(
        requirements, seen_fields, _REQUIRED_FIELDS[2],
        coverage.get("sum_assured") is None
    )

    # ------------------------------------------------------------------
    # Check preferred fields
    # ------------------------------------------------------------------
    _check_field(requirements, seen_fields, _PREFERRED_FIELDS[0], health.get("bmi") is None)
    _check_field(
        requirements, seen_fields, _PREFERRED_FIELDS[1],
        health.get("pre_existing_conditions") is None
    )
    _check_field(
        requirements, seen_fields, _PREFERRED_FIELDS[2],
        financial.get("net_worth") is None
    )

    # ------------------------------------------------------------------
    # Check flag-triggered requirements
    # ------------------------------------------------------------------
    active_codes = {f.get("flag_code") for f in risk_flags}
    for flag_code, req_def in _FLAG_REQUIREMENTS.items():
        if flag_code in active_codes and req_def["field_name"] not in seen_fields:
            requirements.append(req_def)
            seen_fields.add(req_def["field_name"])

    # ------------------------------------------------------------------
    # Classify results
    # ------------------------------------------------------------------
    blocking = [r["field_name"] for r in requirements if r["priority"] == "REQUIRED"]
    non_blocking = [r["field_name"] for r in requirements if r["priority"] == "PREFERRED"]

    # Estimate fulfillment time based on document types
    days_estimate = 0
    for req in requirements:
        doc = req.get("document_type") or ""
        if "physician" in doc.lower() or "medical exam" in doc.lower():
            days_estimate = max(days_estimate, 14)
        elif "tax return" in doc.lower() or "financial statement" in doc.lower():
            days_estimate = max(days_estimate, 7)
        else:
            days_estimate = max(days_estimate, 3)

    return {
        "requirements": requirements,
        "can_proceed_without": non_blocking,
        "blocking_requirements": blocking,
        "estimated_fulfillment_days": days_estimate,
    }


def _check_field(
    requirements: list, seen: set,
    req_def: dict, is_missing: bool
) -> None:
    """Add a requirement if the field is missing."""
    if is_missing and req_def["field_name"] not in seen:
        requirements.append(req_def)
        seen.add(req_def["field_name"])
