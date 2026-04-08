"""
decision_engine.py
-------------------
Final underwriting decision logic (WAT Framework v3).

This tool is deterministic — no LLMs.
It takes the risk profile and applies business rules to produce one of:
  APPROVED | APPROVED_WITH_CONDITIONS | REJECTED | PENDED

The decision_engine does NOT generate the audit explanation — that is done
by llm_audit_explainer.
"""

from __future__ import annotations

import json
from typing import Any


# ---------------------------------------------------------------------------
# Decision thresholds
# ---------------------------------------------------------------------------

_AUTO_APPROVE_MAX_SCORE = 35.0        # Risk score ≤ 35 → APPROVED or APPROVED_WITH_CONDITIONS
_AUTO_REJECT_MIN_SCORE  = 80.0        # Risk score ≥ 80 → REJECTED
_CONDITIONS_SCORE_RANGE = (35.0, 80.0) # Between → APPROVED_WITH_CONDITIONS or PENDED

_CRITICAL_FLAGS_REJECT_THRESHOLD = 2  # ≥ 2 CRITICAL flags → REJECTED
_CRITICAL_FLAGS_PEND_THRESHOLD   = 1  # 1 CRITICAL flag → PENDED if manual review required

# Conditions applied by risk class
_RISK_CLASS_CONDITIONS = {
    "SUBSTANDARD": [
        {
            "condition_code": "EXCLUSION_PRE_EXISTING",
            "description": "Pre-existing conditions are excluded from coverage for the first 24 months",
            "exclusion_clause": "Clause 4.2(b): Exclusion of pre-existing conditions",
        }
    ],
}

_DECLINED_REJECTION_REASONS = [
    {
        "reason_code": "RISK_TOO_HIGH",
        "description": "The combined risk profile exceeds the maximum acceptable underwriting risk threshold"
    }
]


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def make_decision(
    structured_data: dict[str, Any],
    risk_profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Apply decision rules to produce the final underwriting decision.

    Args:
        structured_data: Normalized application data.
        risk_profile:    Output from risk_scoring_service or DB risk_profiles row.

    Returns:
        {
            "decision": "APPROVED" | "APPROVED_WITH_CONDITIONS" | "REJECTED" | "PENDED",
            "premium_adjustment": {...},
            "conditions": [...],
            "rejection_reasons": [...],
            "pend_reasons": [...],
            "rules_applied": [...],
        }
    """
    # Unpack risk profile
    risk_score = float(risk_profile.get("risk_score", 50))
    risk_class = risk_profile.get("risk_class", "STANDARD")
    risk_flags = risk_profile.get("risk_flags", [])
    manual_review = risk_profile.get("manual_review_required", False)
    loading = float(risk_profile.get("premium_loading_percent", 0))

    if isinstance(risk_flags, str):
        risk_flags = json.loads(risk_flags)

    critical_count = sum(1 for f in risk_flags if f.get("severity") == "CRITICAL")
    rules_applied: list[str] = []
    conditions: list[dict] = []
    rejection_reasons: list[dict] = []
    pend_reasons: list[str] = []

    # ------------------------------------------------------------------
    # Rule 1: Auto-reject DECLINED risk class
    # ------------------------------------------------------------------
    if risk_class == "DECLINED":
        rules_applied.append("RULE_DECLINED_CLASS: risk_class=DECLINED triggers automatic rejection")
        return {
            "decision": "REJECTED",
            "premium_adjustment": {},
            "conditions": [],
            "rejection_reasons": _DECLINED_REJECTION_REASONS,
            "pend_reasons": [],
            "rules_applied": rules_applied,
        }

    # ------------------------------------------------------------------
    # Rule 2: Auto-reject on critical flag threshold
    # ------------------------------------------------------------------
    if critical_count >= _CRITICAL_FLAGS_REJECT_THRESHOLD:
        rules_applied.append(
            f"RULE_CRITICAL_FLAGS: {critical_count} CRITICAL flags ≥ threshold {_CRITICAL_FLAGS_REJECT_THRESHOLD}"
        )
        critical_descriptions = [
            f["description"] for f in risk_flags if f.get("severity") == "CRITICAL"
        ]
        return {
            "decision": "REJECTED",
            "premium_adjustment": {},
            "conditions": [],
            "rejection_reasons": [
                {"reason_code": f["flag_code"], "description": f["description"]}
                for f in risk_flags if f.get("severity") == "CRITICAL"
            ],
            "pend_reasons": [],
            "rules_applied": rules_applied,
        }

    # ------------------------------------------------------------------
    # Rule 3: Auto-reject on score threshold
    # ------------------------------------------------------------------
    if risk_score >= _AUTO_REJECT_MIN_SCORE:
        rules_applied.append(
            f"RULE_SCORE_REJECT: risk_score={risk_score} ≥ threshold {_AUTO_REJECT_MIN_SCORE}"
        )
        return {
            "decision": "REJECTED",
            "premium_adjustment": {},
            "conditions": [],
            "rejection_reasons": _DECLINED_REJECTION_REASONS,
            "pend_reasons": [],
            "rules_applied": rules_applied,
        }

    # ------------------------------------------------------------------
    # Rule 4: Pend if manual review required with critical flag
    # ------------------------------------------------------------------
    if manual_review and critical_count >= _CRITICAL_FLAGS_PEND_THRESHOLD:
        rules_applied.append(
            "RULE_MANUAL_PEND: Manual review required with CRITICAL flags — pending for underwriter"
        )
        critical_flags_text = [
            f["description"] for f in risk_flags if f.get("severity") == "CRITICAL"
        ]
        pend_reasons = critical_flags_text + ["Requires human underwriter review"]
        return {
            "decision": "PENDED",
            "premium_adjustment": {},
            "conditions": [],
            "rejection_reasons": [],
            "pend_reasons": pend_reasons,
            "rules_applied": rules_applied,
        }

    # ------------------------------------------------------------------
    # Rule 5: Calculate premium with loading
    # ------------------------------------------------------------------
    coverage = structured_data.get("coverage_requested") or {}
    financial = structured_data.get("financial_info") or {}

    # Estimate base premium from sum_assured (simplified: sum_assured * rate)
    sum_assured = coverage.get("sum_assured") or 0
    base_premium = _estimate_base_premium(sum_assured, structured_data)
    final_premium = base_premium * (1 + loading / 100)

    premium_adjustment = {
        "base_premium": round(base_premium, 2),
        "loading_percent": loading,
        "final_premium": round(final_premium, 2),
        "adjustment_reason": f"Risk class: {risk_class}" if loading > 0 else None,
    }

    # ------------------------------------------------------------------
    # Rule 6: Apply conditions for SUBSTANDARD
    # ------------------------------------------------------------------
    if risk_class == "SUBSTANDARD":
        conditions = _RISK_CLASS_CONDITIONS.get("SUBSTANDARD", [])
        rules_applied.append("RULE_SUBSTANDARD_CONDITIONS: Risk class SUBSTANDARD — applying exclusion conditions")

    # ------------------------------------------------------------------
    # Rule 7: Final decision
    # ------------------------------------------------------------------
    if risk_score <= _AUTO_APPROVE_MAX_SCORE:
        if risk_class == "PREFERRED":
            rules_applied.append(f"RULE_APPROVE: risk_score={risk_score} ≤ {_AUTO_APPROVE_MAX_SCORE}, class=PREFERRED")
            decision = "APPROVED"
        else:
            rules_applied.append(f"RULE_APPROVE: risk_score={risk_score} ≤ {_AUTO_APPROVE_MAX_SCORE}")
            decision = "APPROVED" if not conditions else "APPROVED_WITH_CONDITIONS"
    else:
        if conditions:
            rules_applied.append(
                f"RULE_APPROVE_CONDITIONS: {_CONDITIONS_SCORE_RANGE[0]} < risk_score={risk_score} < {_CONDITIONS_SCORE_RANGE[1]}"
            )
            decision = "APPROVED_WITH_CONDITIONS"
        elif manual_review:
            rules_applied.append("RULE_PEND_MANUAL: Manual review required in borderline range")
            decision = "PENDED"
            pend_reasons = ["Borderline risk score requires underwriter review"]
        else:
            rules_applied.append(
                f"RULE_APPROVE_CONDITIONS: risk_score={risk_score} in conditional range"
            )
            decision = "APPROVED_WITH_CONDITIONS"

    return {
        "decision": decision,
        "premium_adjustment": premium_adjustment,
        "conditions": conditions,
        "rejection_reasons": rejection_reasons,
        "pend_reasons": pend_reasons,
        "rules_applied": rules_applied,
    }


def _estimate_base_premium(sum_assured: float, structured_data: dict) -> float:
    """
    Simplified actuarial premium estimation.
    Rate = base_rate * sum_assured / 1000
    Base rate varies by age and smoker status.
    """
    if sum_assured <= 0:
        return 0.0

    personal = structured_data.get("personal_info") or {}
    age = personal.get("age") or 35
    smoker = personal.get("smoker") or False

    # Annual rate per $1,000 sum assured (simplified)
    if age < 30:
        base_rate = 0.8
    elif age < 40:
        base_rate = 1.2
    elif age < 50:
        base_rate = 2.0
    elif age < 60:
        base_rate = 3.5
    else:
        base_rate = 5.5

    if smoker:
        base_rate *= 1.4

    return (sum_assured / 1000) * base_rate
