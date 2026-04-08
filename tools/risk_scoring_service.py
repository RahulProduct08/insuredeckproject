"""
risk_scoring_service.py
------------------------
Generates numeric risk scores and risk class from structured application data
and risk flags produced by the underwriting_rule_engine.

This tool is deterministic — no LLM involved.
Score range: 0 (lowest risk) to 100 (highest risk).
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Score contribution weights
# ---------------------------------------------------------------------------

_FLAG_SEVERITY_POINTS = {
    "LOW":      2,
    "MEDIUM":   8,
    "HIGH":     18,
    "CRITICAL": 35,
}

# Risk class thresholds (score → class)
_RISK_CLASS_THRESHOLDS = [
    (0,  20,  "PREFERRED"),
    (20, 45,  "STANDARD"),
    (45, 75,  "SUBSTANDARD"),
    (75, 101, "DECLINED"),
]

# Premium loading schedule (risk class → percent)
_PREMIUM_LOADING = {
    "PREFERRED":    0.0,
    "STANDARD":     0.0,
    "SUBSTANDARD":  25.0,
    "DECLINED":     0.0,   # Not offered; handled by decision engine
}


# ---------------------------------------------------------------------------
# Sub-scores
# ---------------------------------------------------------------------------

def _age_score(structured_data: dict) -> float:
    """Base age score — older applicants have higher base risk."""
    personal = structured_data.get("personal_info") or {}
    age = personal.get("age")
    if age is None:
        return 10.0  # Unknown age = moderate base risk
    if age < 30:
        return 0.0
    if age < 40:
        return 5.0
    if age < 50:
        return 10.0
    if age < 60:
        return 18.0
    if age < 70:
        return 28.0
    return 40.0


def _health_score(structured_data: dict) -> float:
    """Health signal sub-score."""
    health = structured_data.get("health_info") or {}
    score = 0.0

    bmi = health.get("bmi")
    if bmi is not None:
        if bmi >= 40:
            score += 20
        elif bmi >= 35:
            score += 12
        elif bmi >= 30:
            score += 6
        elif bmi < 18.5:
            score += 5

    conditions = health.get("pre_existing_conditions") or []
    score += min(len(conditions) * 8, 30)

    medications = health.get("medications") or []
    score += min(len(medications) * 3, 15)

    return score


def _lifestyle_score(structured_data: dict) -> float:
    """Lifestyle signal sub-score."""
    personal = structured_data.get("personal_info") or {}
    score = 0.0

    if personal.get("smoker") is True:
        score += 20.0

    return score


def _financial_score(structured_data: dict) -> float:
    """Financial adequacy sub-score."""
    financial = structured_data.get("financial_info") or {}
    coverage = structured_data.get("coverage_requested") or {}
    score = 0.0

    income = financial.get("annual_income")
    sum_assured = coverage.get("sum_assured")

    if income and income > 0 and sum_assured:
        ratio = sum_assured / income
        if ratio > 30:
            score += 20
        elif ratio > 20:
            score += 10
        elif ratio > 10:
            score += 3

    return score


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def calculate_risk_score(
    structured_data: dict[str, Any],
    flags: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate a numeric risk score and assign a risk class.

    Args:
        structured_data: Normalized application data.
        flags:           Risk flags from underwriting_rule_engine.evaluate_rules().

    Returns:
        {
            "risk_score": float (0–100),
            "risk_class": "PREFERRED" | "STANDARD" | "SUBSTANDARD" | "DECLINED",
            "premium_loading_percent": float,
            "signals": {
                "age_score": float,
                "health_score": float,
                "lifestyle_score": float,
                "financial_score": float,
                "flag_score": float,
            },
        }
    """
    # Compute sub-scores
    age_s = _age_score(structured_data)
    health_s = _health_score(structured_data)
    lifestyle_s = _lifestyle_score(structured_data)
    financial_s = _financial_score(structured_data)

    # Add points from flags (deduplicating by flag_code to avoid double-counting)
    seen_codes: set[str] = set()
    flag_s = 0.0
    for flag in flags:
        code = flag.get("flag_code", "")
        if code not in seen_codes:
            flag_s += _FLAG_SEVERITY_POINTS.get(flag.get("severity", "LOW"), 2)
            seen_codes.add(code)

    # Combine — weighted average capped at 100
    raw_score = age_s + health_s + lifestyle_s + financial_s + flag_s
    risk_score = min(round(raw_score, 1), 100.0)

    # Assign risk class
    risk_class = "SUBSTANDARD"
    for low, high, cls in _RISK_CLASS_THRESHOLDS:
        if low <= risk_score < high:
            risk_class = cls
            break

    loading = _PREMIUM_LOADING.get(risk_class, 0.0)

    return {
        "risk_score": risk_score,
        "risk_class": risk_class,
        "premium_loading_percent": loading,
        "signals": {
            "age_score": age_s,
            "health_score": health_s,
            "lifestyle_score": lifestyle_s,
            "financial_score": financial_s,
            "flag_score": flag_s,
        },
    }
