"""
underwriting_rule_engine.py
-----------------------------
Executes deterministic underwriting rules against a structured application profile.

Rules are evaluated in order of severity.
This tool does NOT use LLMs — all logic is deterministic.

Returns flags and whether manual review is required.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

def _rule_age(data: dict) -> list[dict]:
    """Age boundary and eligibility rules."""
    flags = []
    personal = data.get("personal_info") or {}
    age = personal.get("age")
    if age is None:
        return flags

    if age < 18:
        flags.append({
            "flag_code": "AGE_BELOW_MINIMUM",
            "severity": "CRITICAL",
            "description": f"Applicant age {age} is below the minimum insurable age of 18",
            "value": age,
            "threshold": 18,
        })
    elif age > 65:
        flags.append({
            "flag_code": "AGE_ABOVE_STANDARD",
            "severity": "HIGH",
            "description": f"Applicant age {age} exceeds standard underwriting age of 65; loading applies",
            "value": age,
            "threshold": 65,
        })
    elif age >= 60:
        flags.append({
            "flag_code": "AGE_SENIOR",
            "severity": "MEDIUM",
            "description": f"Applicant age {age} is in senior bracket (60+); additional health checks required",
            "value": age,
            "threshold": 60,
        })
    return flags


def _rule_bmi(data: dict) -> list[dict]:
    """BMI risk flags."""
    flags = []
    health = data.get("health_info") or {}
    bmi = health.get("bmi")
    if bmi is None:
        return flags

    if bmi >= 40:
        flags.append({
            "flag_code": "BMI_CRITICAL",
            "severity": "CRITICAL",
            "description": f"BMI {bmi:.1f} is critically high (≥40); significant mortality risk",
            "value": round(bmi, 1),
            "threshold": 40,
        })
    elif bmi >= 35:
        flags.append({
            "flag_code": "BMI_VERY_HIGH",
            "severity": "HIGH",
            "description": f"BMI {bmi:.1f} is very high (35–40); premium loading required",
            "value": round(bmi, 1),
            "threshold": 35,
        })
    elif bmi >= 30:
        flags.append({
            "flag_code": "BMI_HIGH",
            "severity": "MEDIUM",
            "description": f"BMI {bmi:.1f} is elevated (30–35); minor loading may apply",
            "value": round(bmi, 1),
            "threshold": 30,
        })
    elif bmi < 18.5:
        flags.append({
            "flag_code": "BMI_LOW",
            "severity": "MEDIUM",
            "description": f"BMI {bmi:.1f} is underweight (<18.5); health assessment required",
            "value": round(bmi, 1),
            "threshold": 18.5,
        })
    return flags


def _rule_smoker(data: dict) -> list[dict]:
    """Smoker risk flag."""
    flags = []
    personal = data.get("personal_info") or {}
    if personal.get("smoker") is True:
        flags.append({
            "flag_code": "SMOKER",
            "severity": "HIGH",
            "description": "Active smoker identified; premium loading applies (typically 25–50%)",
            "value": True,
            "threshold": False,
        })
    return flags


def _rule_pre_existing_conditions(data: dict) -> list[dict]:
    """Pre-existing medical condition rules."""
    flags = []
    health = data.get("health_info") or {}
    conditions = health.get("pre_existing_conditions") or []

    # High-risk conditions that trigger critical flags
    critical_conditions = {
        "cancer", "hiv", "heart failure", "organ transplant",
        "end-stage renal disease", "cirrhosis"
    }
    high_risk_conditions = {
        "diabetes", "coronary artery disease", "stroke", "copd",
        "multiple sclerosis", "lupus", "epilepsy"
    }

    for condition in conditions:
        condition_lower = condition.lower()
        if any(c in condition_lower for c in critical_conditions):
            flags.append({
                "flag_code": "PRE_EXISTING_CRITICAL",
                "severity": "CRITICAL",
                "description": f"Critical pre-existing condition: '{condition}' — likely decline",
                "value": condition,
                "threshold": "critical_conditions_list",
            })
        elif any(c in condition_lower for c in high_risk_conditions):
            flags.append({
                "flag_code": "PRE_EXISTING_HIGH",
                "severity": "HIGH",
                "description": f"High-risk pre-existing condition: '{condition}' — underwriter review required",
                "value": condition,
                "threshold": "high_risk_conditions_list",
            })
        else:
            flags.append({
                "flag_code": "PRE_EXISTING_MODERATE",
                "severity": "MEDIUM",
                "description": f"Pre-existing condition on record: '{condition}'",
                "value": condition,
                "threshold": None,
            })

    return flags


def _rule_coverage_ratio(data: dict) -> list[dict]:
    """Check if requested coverage is proportional to income."""
    flags = []
    financial = data.get("financial_info") or {}
    coverage = data.get("coverage_requested") or {}

    income = financial.get("annual_income")
    sum_assured = coverage.get("sum_assured")

    if income and income > 0 and sum_assured:
        ratio = sum_assured / income
        if ratio > 30:
            flags.append({
                "flag_code": "COVERAGE_RATIO_CRITICAL",
                "severity": "CRITICAL",
                "description": f"Sum assured is {ratio:.1f}x annual income (>{30}x) — financial underwriting required",
                "value": round(ratio, 1),
                "threshold": 30,
            })
        elif ratio > 20:
            flags.append({
                "flag_code": "COVERAGE_RATIO_HIGH",
                "severity": "HIGH",
                "description": f"Sum assured is {ratio:.1f}x annual income (>{20}x) — income verification required",
                "value": round(ratio, 1),
                "threshold": 20,
            })
    return flags


def _rule_medications(data: dict) -> list[dict]:
    """Flag polypharmacy (multiple medications)."""
    flags = []
    health = data.get("health_info") or {}
    medications = health.get("medications") or []
    count = len(medications)

    if count >= 5:
        flags.append({
            "flag_code": "POLY_PHARMACY_HIGH",
            "severity": "HIGH",
            "description": f"Applicant is on {count} medications — complex health profile review required",
            "value": count,
            "threshold": 5,
        })
    elif count >= 3:
        flags.append({
            "flag_code": "POLY_PHARMACY_MODERATE",
            "severity": "MEDIUM",
            "description": f"Applicant is on {count} medications",
            "value": count,
            "threshold": 3,
        })
    return flags


def _rule_family_history(data: dict) -> list[dict]:
    """Flag significant family medical history."""
    flags = []
    health = data.get("health_info") or {}
    history = health.get("family_history") or []

    high_risk_history = {"cancer", "heart disease", "stroke", "diabetes", "huntington"}

    significant = [
        h for h in history
        if any(r in h.lower() for r in high_risk_history)
    ]

    if len(significant) >= 2:
        flags.append({
            "flag_code": "FAMILY_HISTORY_MULTIPLE",
            "severity": "HIGH",
            "description": f"Multiple significant family history conditions: {significant}",
            "value": significant,
            "threshold": 2,
        })
    elif significant:
        flags.append({
            "flag_code": "FAMILY_HISTORY_NOTED",
            "severity": "LOW",
            "description": f"Family history noted: {significant}",
            "value": significant,
            "threshold": 1,
        })
    return flags


# ---------------------------------------------------------------------------
# Rule registry — ordered by priority
# ---------------------------------------------------------------------------

_RULES = [
    _rule_age,
    _rule_bmi,
    _rule_smoker,
    _rule_pre_existing_conditions,
    _rule_coverage_ratio,
    _rule_medications,
    _rule_family_history,
]

_MANUAL_REVIEW_TRIGGER_CODES = {
    "AGE_ABOVE_STANDARD", "BMI_CRITICAL", "PRE_EXISTING_CRITICAL",
    "COVERAGE_RATIO_CRITICAL", "POLY_PHARMACY_HIGH",
}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def evaluate_rules(structured_data: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate all underwriting rules against the structured application data.

    Args:
        structured_data: Normalized application data (output of llm_extractor).

    Returns:
        {
            "flags": [...],
            "flag_count": int,
            "critical_count": int,
            "high_count": int,
            "manual_review_required": bool,
            "review_reason": str | None,
        }
    """
    all_flags: list[dict] = []
    for rule_fn in _RULES:
        try:
            all_flags.extend(rule_fn(structured_data))
        except Exception:
            continue

    critical_count = sum(1 for f in all_flags if f["severity"] == "CRITICAL")
    high_count = sum(1 for f in all_flags if f["severity"] == "HIGH")

    manual_review = any(
        f["flag_code"] in _MANUAL_REVIEW_TRIGGER_CODES for f in all_flags
    )
    review_reason = None
    if manual_review:
        trigger_flags = [
            f["flag_code"] for f in all_flags
            if f["flag_code"] in _MANUAL_REVIEW_TRIGGER_CODES
        ]
        review_reason = f"Manual review triggered by: {trigger_flags}"

    return {
        "flags": all_flags,
        "flag_count": len(all_flags),
        "critical_count": critical_count,
        "high_count": high_count,
        "manual_review_required": manual_review,
        "review_reason": review_reason,
    }
