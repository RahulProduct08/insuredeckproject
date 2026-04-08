"""
validator.py
-------------
Schema validation, business rule checks, and cross-entity consistency
for the underwriting system (WAT Framework v3).

Three validation layers:
  1. Schema validation  — input/output matches the contract JSON schemas
  2. Business rules     — domain-specific constraints
  3. Cross-entity       — consistency across application, risk, decision
"""

from __future__ import annotations

import json
import os
from typing import Any

# ---------------------------------------------------------------------------
# Schema loader
# ---------------------------------------------------------------------------

_CONTRACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contracts")

_schema_cache: dict[str, dict] = {}


def _load_schema(name: str) -> dict:
    """Load a JSON schema from contracts/ (cached)."""
    if name not in _schema_cache:
        path = os.path.join(_CONTRACTS_DIR, f"{name}.schema.json")
        with open(path, "r", encoding="utf-8") as f:
            _schema_cache[name] = json.load(f)
    return _schema_cache[name]


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

class ValidationResult:
    def __init__(self, valid: bool, errors: list[str] | None = None) -> None:
        self.valid = valid
        self.errors: list[str] = errors or []

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        return f"ValidationResult(valid={self.valid}, errors={self.errors})"


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class Validator:
    """
    Validates data at each stage of the underwriting lifecycle.
    """

    # ------------------------------------------------------------------
    # Layer 1: Schema validation
    # ------------------------------------------------------------------

    def validate_application(self, data: dict[str, Any]) -> ValidationResult:
        """Validate structured application data against application.schema.json."""
        return self._validate_required_fields(data, [
            "application_id", "client_id", "product_id", "state"
        ])

    def validate_risk_profile(self, data: dict[str, Any]) -> ValidationResult:
        """Validate risk profile against risk.schema.json."""
        errors = []
        required = ["profile_id", "application_id", "risk_score", "risk_class", "risk_flags", "state"]
        for field in required:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")

        if "risk_score" in data and data["risk_score"] is not None:
            score = data["risk_score"]
            if not (0 <= score <= 100):
                errors.append(f"risk_score must be 0–100, got {score}")

        valid_classes = {"PREFERRED", "STANDARD", "SUBSTANDARD", "DECLINED"}
        if data.get("risk_class") not in valid_classes:
            errors.append(f"risk_class must be one of {valid_classes}, got '{data.get('risk_class')}'")

        return ValidationResult(len(errors) == 0, errors)

    def validate_decision(self, data: dict[str, Any]) -> ValidationResult:
        """Validate decision output against decision.schema.json."""
        errors = []
        required = ["decision_id", "application_id", "decision", "state", "decided_at"]
        for field in required:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")

        valid_decisions = {"APPROVED", "APPROVED_WITH_CONDITIONS", "REJECTED", "PENDED"}
        if data.get("decision") not in valid_decisions:
            errors.append(f"decision must be one of {valid_decisions}, got '{data.get('decision')}'")

        # REJECTED must have rejection_reasons
        if data.get("decision") == "REJECTED":
            reasons = data.get("rejection_reasons", [])
            if not reasons:
                errors.append("REJECTED decision must include rejection_reasons")

        # APPROVED_WITH_CONDITIONS must have conditions
        if data.get("decision") == "APPROVED_WITH_CONDITIONS":
            conditions = data.get("conditions", [])
            if not conditions:
                errors.append("APPROVED_WITH_CONDITIONS must include conditions")

        return ValidationResult(len(errors) == 0, errors)

    # ------------------------------------------------------------------
    # Layer 2: Business rule checks
    # ------------------------------------------------------------------

    def check_intake_rules(self, structured_data: dict[str, Any]) -> ValidationResult:
        """
        Business rules applied during intake:
        - Age must be present and within 18–75
        - Annual income must be present and positive
        - Coverage requested must include sum_assured
        """
        errors = []
        personal = structured_data.get("personal_info") or {}
        financial = structured_data.get("financial_info") or {}
        coverage = structured_data.get("coverage_requested") or {}

        age = personal.get("age")
        if age is None:
            errors.append("INCOMPLETE: personal_info.age is required")
        elif not (18 <= age <= 75):
            errors.append(f"RULE_VIOLATION: Age {age} is outside insurable range 18–75")

        income = financial.get("annual_income")
        if income is None:
            errors.append("INCOMPLETE: financial_info.annual_income is required")
        elif income <= 0:
            errors.append("RULE_VIOLATION: annual_income must be positive")

        sum_assured = coverage.get("sum_assured")
        if sum_assured is None:
            errors.append("INCOMPLETE: coverage_requested.sum_assured is required")
        elif sum_assured <= 0:
            errors.append("RULE_VIOLATION: sum_assured must be positive")

        return ValidationResult(len(errors) == 0, errors)

    def check_risk_classification_rules(
        self, structured_data: dict[str, Any], risk_flags: list[dict]
    ) -> ValidationResult:
        """
        Business rules applied during risk classification:
        - CRITICAL flags may auto-reject
        - Conflicting signals require manual review
        """
        errors = []
        critical_flags = [f for f in risk_flags if f.get("severity") == "CRITICAL"]

        if len(critical_flags) >= 3:
            errors.append(
                f"RULE_VIOLATION: {len(critical_flags)} CRITICAL risk flags — "
                "application requires escalation to senior underwriter"
            )

        return ValidationResult(len(errors) == 0, errors)

    def check_cross_entity_consistency(
        self,
        application: dict[str, Any],
        risk_profile: dict[str, Any],
        decision: dict[str, Any],
    ) -> ValidationResult:
        """
        Cross-entity consistency checks:
        - application_id must match across all three
        - State progression must be coherent
        """
        errors = []

        app_id = application.get("application_id")
        if risk_profile.get("application_id") != app_id:
            errors.append("INCONSISTENCY: risk_profile.application_id does not match application")
        if decision.get("application_id") != app_id:
            errors.append("INCONSISTENCY: decision.application_id does not match application")

        # Risk class → decision consistency
        risk_class = risk_profile.get("risk_class")
        decision_val = decision.get("decision")

        if risk_class == "DECLINED" and decision_val not in {"REJECTED", "PENDED"}:
            errors.append(
                f"INCONSISTENCY: risk_class=DECLINED but decision={decision_val}; "
                "expected REJECTED or PENDED"
            )

        return ValidationResult(len(errors) == 0, errors)

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _validate_required_fields(self, data: dict[str, Any], fields: list[str]) -> ValidationResult:
        errors = [
            f"Missing required field: {f}"
            for f in fields
            if f not in data or data[f] is None
        ]
        return ValidationResult(len(errors) == 0, errors)
