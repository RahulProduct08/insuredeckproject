"""
workflow_runner.py
-------------------
Executes underwriting workflow SOPs step-by-step (WAT Framework v3).

The WorkflowRunner loads the markdown SOP for the current lifecycle stage
and coordinates tool calls in sequence, validating output at each step
and persisting state via the StateManager.

It does NOT contain business logic — it orchestrates tools.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from engine.validator import Validator
from state.state_manager import get_state_manager


_WORKFLOWS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows"
)


class WorkflowRunner:
    """
    Orchestrates a single underwriting workflow step.

    Each run() call maps to one lifecycle stage and delegates to the
    appropriate tool chain.
    """

    def __init__(self) -> None:
        self._validator = Validator()
        self._state_mgr = get_state_manager()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, workflow: str, application_id: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the named workflow for the given application.

        Args:
            workflow:       Workflow name matching a file in workflows/
                            (e.g., "intake_application", "risk_classification")
            application_id: The underwriting application ID
            **kwargs:       Additional inputs required by the workflow

        Returns:
            Structured result dict with status, workflow, data, and errors.
        """
        handler_map = {
            "intake_application":    self._run_intake,
            "data_aggregation":      self._run_data_aggregation,
            "risk_classification":   self._run_risk_classification,
            "underwriting_decision": self._run_decision,
            "requirements_management": self._run_requirements,
            "issuance":              self._run_issuance,
        }

        handler = handler_map.get(workflow)
        if handler is None:
            return self._err(workflow, application_id, f"Unknown workflow '{workflow}'")

        try:
            return handler(application_id, **kwargs)
        except Exception as exc:
            return self._err(workflow, application_id, str(exc))

    def get_workflow_sop(self, workflow: str) -> str | None:
        """Return the raw SOP markdown for a workflow (for reference/audit)."""
        path = os.path.join(_WORKFLOWS_DIR, f"{workflow}.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    # ------------------------------------------------------------------
    # Workflow: intake_application
    # ------------------------------------------------------------------

    def _run_intake(self, application_id: str, raw_input: dict | None = None, **_: Any) -> dict:
        """
        SOP: intake_application.md
        Convert raw input → structured application via llm_extractor.
        """
        from tools.llm_extractor import extract_structured_data
        from tools.llm_audit_explainer import log_audit_event

        raw_input = raw_input or {}

        # Step 1 — Fetch application record
        app = self._get_application(application_id)
        if app is None:
            return self._err("intake_application", application_id, "Application not found")

        # Step 2 — Call llm_extractor to normalize inputs
        extraction_result = extract_structured_data(raw_input)
        self._write_audit(application_id, raw_input, "llm_extractor", "extractor_v1",
                          extraction_result)

        # Step 3 — Validate against intake business rules
        structured = extraction_result.get("structured_data", {})
        validation = self._validator.check_intake_rules(structured)

        if not validation:
            # Mark incomplete fields but do not block — store for requirements workflow
            self._update_application(application_id, {
                "structured_data": json.dumps(structured),
                "raw_input": json.dumps(raw_input),
            })
            self._state_mgr.transition(application_id, "IN_PROGRESS")
            return self._ok("intake_application", application_id, {
                "status": "INCOMPLETE",
                "structured_data": structured,
                "validation_errors": validation.errors,
                "missing_fields": extraction_result.get("missing_fields", []),
            })

        # Step 4 — Store structured application
        self._update_application(application_id, {
            "structured_data": json.dumps(structured),
            "raw_input": json.dumps(raw_input),
        })

        # Step 5 — Set state = IN_PROGRESS
        self._state_mgr.transition(application_id, "IN_PROGRESS")

        return self._ok("intake_application", application_id, {
            "status": "COMPLETE",
            "structured_data": structured,
            "extraction_confidence": extraction_result.get("extraction_confidence"),
            "missing_fields": extraction_result.get("missing_fields", []),
        })

    # ------------------------------------------------------------------
    # Workflow: data_aggregation
    # ------------------------------------------------------------------

    def _run_data_aggregation(self, application_id: str, external_data: dict | None = None, **_: Any) -> dict:
        """
        SOP: data_aggregation.md
        Enrich application with external data + classify signals.
        """
        from tools.llm_classifier import classify_risk_signals

        external_data = external_data or {}

        app = self._get_application(application_id)
        if app is None:
            return self._err("data_aggregation", application_id, "Application not found")

        structured_data = app.get("structured_data") or {}
        if isinstance(structured_data, str):
            structured_data = json.loads(structured_data)

        # Step 2 — Merge external data into structured profile
        enriched_profile = {**structured_data, "external_data": external_data}

        # Step 3 — Call llm_classifier to extract signals
        classification_result = classify_risk_signals(enriched_profile)
        self._write_audit(application_id, enriched_profile, "llm_classifier", "classifier_v1",
                          classification_result)

        # Step 4 — Validate completeness
        if not classification_result.get("signals") and not external_data:
            self._state_mgr.transition(application_id, "PENDED")
            return self._ok("data_aggregation", application_id, {
                "status": "PENDED",
                "reason": "Insufficient data for risk signal extraction",
            })

        # Step 5 — Store enriched profile (merge into structured_data)
        enriched_profile["risk_signals"] = classification_result.get("signals", [])
        self._update_application(application_id, {
            "structured_data": json.dumps(enriched_profile),
        })

        # Step 6 — Set state = DATA_ENRICHED
        self._state_mgr.transition(application_id, "DATA_ENRICHED")

        return self._ok("data_aggregation", application_id, {
            "status": "ENRICHED",
            "signals_found": len(classification_result.get("signals", [])),
            "manual_review_recommended": classification_result.get("manual_review_recommended", False),
            "enriched_profile": enriched_profile,
        })

    # ------------------------------------------------------------------
    # Workflow: risk_classification
    # ------------------------------------------------------------------

    def _run_risk_classification(self, application_id: str, **_: Any) -> dict:
        """
        SOP: risk_classification.md
        Convert enriched data → risk score + risk class via rule engine + scoring service.
        """
        from tools.underwriting_rule_engine import evaluate_rules
        from tools.risk_scoring_service import calculate_risk_score

        app = self._get_application(application_id)
        if app is None:
            return self._err("risk_classification", application_id, "Application not found")

        structured_data = app.get("structured_data") or {}
        if isinstance(structured_data, str):
            structured_data = json.loads(structured_data)

        # Step 1 — Normalize inputs (already structured by intake + aggregation)

        # Step 2 — Call underwriting_rule_engine → flags
        rule_result = evaluate_rules(structured_data)
        self._write_audit(application_id, structured_data, "underwriting_rule_engine", None, rule_result)

        flags = rule_result.get("flags", [])

        # Step 3 — Call risk_scoring_service → score
        scoring_result = calculate_risk_score(structured_data, flags)
        self._write_audit(application_id, {"flags": flags}, "risk_scoring_service", None, scoring_result)

        risk_score = scoring_result.get("risk_score", 50)
        risk_class = scoring_result.get("risk_class", "STANDARD")
        manual_review = rule_result.get("manual_review_required", False)

        # Check classification business rules
        rule_check = self._validator.check_risk_classification_rules(structured_data, flags)
        if not rule_check:
            manual_review = True

        # Step 4 — Persist risk profile
        profile_id = self._create_risk_profile(
            application_id=application_id,
            risk_score=risk_score,
            risk_class=risk_class,
            risk_flags=flags,
            premium_loading=scoring_result.get("premium_loading_percent", 0),
            signals=scoring_result.get("signals", {}),
            manual_review=manual_review,
            review_reason=rule_result.get("review_reason"),
        )

        # Step 5 — Set state = RISK_CLASSIFIED
        self._state_mgr.transition(application_id, "RISK_CLASSIFIED")

        return self._ok("risk_classification", application_id, {
            "profile_id": profile_id,
            "risk_score": risk_score,
            "risk_class": risk_class,
            "risk_flags": flags,
            "manual_review_required": manual_review,
            "premium_loading_percent": scoring_result.get("premium_loading_percent", 0),
        })

    # ------------------------------------------------------------------
    # Workflow: underwriting_decision
    # ------------------------------------------------------------------

    def _run_decision(self, application_id: str, decided_by: str = "SYSTEM", **_: Any) -> dict:
        """
        SOP: underwriting_decision.md
        Run decision engine + generate audit explanation + persist decision.
        """
        from tools.decision_engine import make_decision
        from tools.llm_audit_explainer import generate_audit_explanation

        app = self._get_application(application_id)
        if app is None:
            return self._err("underwriting_decision", application_id, "Application not found")

        risk_profile = self._get_risk_profile(application_id)
        if risk_profile is None:
            return self._err(
                "underwriting_decision", application_id,
                "Risk profile not found — run risk_classification first"
            )

        structured_data = app.get("structured_data") or {}
        if isinstance(structured_data, str):
            structured_data = json.loads(structured_data)

        # Step 1 — Call decision_engine
        decision_result = make_decision(structured_data, risk_profile)
        self._write_audit(
            application_id,
            {"risk_profile": risk_profile},
            "decision_engine", None,
            decision_result
        )

        decision_value = decision_result.get("decision")
        premium_adjustment = decision_result.get("premium_adjustment", {})
        conditions = decision_result.get("conditions", [])
        rejection_reasons = decision_result.get("rejection_reasons", [])
        pend_reasons = decision_result.get("pend_reasons", [])
        rules_applied = decision_result.get("rules_applied", [])

        # Step 2 — Call llm_audit_explainer → reasoning
        audit_explanation = generate_audit_explanation(
            decision=decision_value,
            application_summary=structured_data,
            risk_profile=risk_profile,
            rules_applied=rules_applied,
        )
        self._write_audit(
            application_id,
            {"decision": decision_value},
            "llm_audit_explainer", "audit_v1",
            audit_explanation
        )

        # Validate decision output
        decision_doc = {
            "decision_id": str(uuid.uuid4()),
            "application_id": application_id,
            "decision": decision_value,
            "state": "DECISIONED",
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "decided_by": decided_by,
            "premium_adjustment": premium_adjustment,
            "conditions": conditions,
            "rejection_reasons": rejection_reasons,
            "pend_reasons": pend_reasons,
            "audit_trail": audit_explanation,
        }

        validation = self._validator.validate_decision(decision_doc)
        if not validation:
            return self._err(
                "underwriting_decision", application_id,
                f"Decision validation failed: {validation.errors}"
            )

        # Step 3 — Persist decision
        decision_id = self._create_decision(decision_doc)

        # Step 4 — Update application state
        state_map = {
            "APPROVED": "APPROVED",
            "APPROVED_WITH_CONDITIONS": "APPROVED",
            "REJECTED": "REJECTED",
            "PENDED": "PENDED",
        }
        new_state = state_map.get(decision_value, "DECISIONED")
        self._state_mgr.transition(application_id, "DECISIONED")
        if new_state != "DECISIONED":
            self._state_mgr.transition(application_id, new_state)

        return self._ok("underwriting_decision", application_id, {
            "decision_id": decision_id,
            "decision": decision_value,
            "premium_adjustment": premium_adjustment,
            "conditions": conditions,
            "rejection_reasons": rejection_reasons,
            "pend_reasons": pend_reasons,
            "audit_summary": audit_explanation.get("summary"),
        })

    # ------------------------------------------------------------------
    # Workflow: requirements_management
    # ------------------------------------------------------------------

    def _run_requirements(self, application_id: str, fulfilled_data: dict | None = None, **_: Any) -> dict:
        """
        SOP: requirements_management.md
        Identify missing requirements or accept fulfilled data, re-trigger flow.
        """
        from tools.requirement_engine import identify_requirements

        app = self._get_application(application_id)
        if app is None:
            return self._err("requirements_management", application_id, "Application not found")

        structured_data = app.get("structured_data") or {}
        if isinstance(structured_data, str):
            structured_data = json.loads(structured_data)

        # If fulfilled_data provided, merge and re-trigger
        if fulfilled_data:
            updated = {**structured_data, **fulfilled_data}
            self._update_application(application_id, {
                "structured_data": json.dumps(updated),
            })
            self._fulfill_requirements(application_id, list(fulfilled_data.keys()))
            self._state_mgr.transition(application_id, "IN_PROGRESS")
            return self._ok("requirements_management", application_id, {
                "action": "REQUIREMENTS_FULFILLED",
                "fulfilled_fields": list(fulfilled_data.keys()),
                "next_state": "IN_PROGRESS",
                "message": "Requirements fulfilled — re-trigger underwriting flow",
            })

        # Identify missing requirements
        risk_profile = self._get_risk_profile(application_id)
        risk_flags = risk_profile.get("risk_flags", []) if risk_profile else []
        if isinstance(risk_flags, str):
            risk_flags = json.loads(risk_flags)

        requirements = identify_requirements(structured_data, risk_flags)
        self._write_audit(
            application_id,
            {"structured_data": structured_data},
            "requirement_engine", None,
            requirements
        )

        # Persist requirements
        self._persist_requirements(application_id, requirements.get("requirements", []))

        return self._ok("requirements_management", application_id, {
            "action": "REQUIREMENTS_IDENTIFIED",
            "requirements": requirements.get("requirements", []),
            "blocking_requirements": requirements.get("blocking_requirements", []),
            "estimated_fulfillment_days": requirements.get("estimated_fulfillment_days"),
        })

    # ------------------------------------------------------------------
    # Workflow: issuance
    # ------------------------------------------------------------------

    def _run_issuance(self, application_id: str, **_: Any) -> dict:
        """
        SOP: issuance.md
        Convert approved application → issued policy.
        """
        from tools.policy_service import update_policy_status

        app = self._get_application(application_id)
        if app is None:
            return self._err("issuance", application_id, "Application not found")

        current_state = self._state_mgr.get_state(application_id)
        if current_state not in {"APPROVED"}:
            return self._err(
                "issuance", application_id,
                f"Cannot issue: application state is '{current_state}', expected APPROVED"
            )

        # Step 1 — Lock premium (fetch from decision)
        decision = self._get_decision(application_id)
        premium_adjustment = decision.get("premium_adjustment", {}) if decision else {}
        if isinstance(premium_adjustment, str):
            premium_adjustment = json.loads(premium_adjustment)

        # Step 2 — Update linked policy to Issued (if policy_id is set)
        policy_id = app.get("policy_id")
        if policy_id:
            try:
                update_policy_status(policy_id, "Issued")
            except Exception as exc:
                return self._err("issuance", application_id, f"Failed to issue policy: {exc}")

        # Step 3 — Set state = ISSUED
        self._state_mgr.transition(application_id, "ISSUED")

        return self._ok("issuance", application_id, {
            "policy_id": policy_id,
            "final_premium": premium_adjustment.get("final_premium"),
            "state": "ISSUED",
        })

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _get_application(self, application_id: str) -> dict | None:
        from database import get_db, row_to_dict
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM underwriting_applications WHERE application_id = ?",
                (application_id,)
            ).fetchone()
            return row_to_dict(row) if row else None
        finally:
            conn.close()

    def _update_application(self, application_id: str, updates: dict) -> None:
        from database import get_db
        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [application_id]
        conn = get_db()
        try:
            conn.execute(
                f"UPDATE underwriting_applications SET {set_clause} WHERE application_id = ?",
                values
            )
            conn.commit()
        finally:
            conn.close()

    def _get_risk_profile(self, application_id: str) -> dict | None:
        from database import get_db, row_to_dict
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM risk_profiles WHERE application_id = ? ORDER BY classified_at DESC LIMIT 1",
                (application_id,)
            ).fetchone()
            return row_to_dict(row) if row else None
        finally:
            conn.close()

    def _create_risk_profile(
        self, application_id: str, risk_score: float, risk_class: str,
        risk_flags: list, premium_loading: float, signals: dict,
        manual_review: bool, review_reason: str | None
    ) -> str:
        from database import get_db
        profile_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO risk_profiles
                   (profile_id, application_id, risk_score, risk_class, risk_flags,
                    premium_loading_percent, signals, manual_review_required,
                    review_reason, state, classified_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile_id, application_id, risk_score, risk_class,
                    json.dumps(risk_flags), premium_loading,
                    json.dumps(signals), int(manual_review),
                    review_reason, "RISK_CLASSIFIED", now,
                )
            )
            conn.commit()
        finally:
            conn.close()
        return profile_id

    def _get_decision(self, application_id: str) -> dict | None:
        from database import get_db, row_to_dict
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM underwriting_decisions WHERE application_id = ? ORDER BY decided_at DESC LIMIT 1",
                (application_id,)
            ).fetchone()
            return row_to_dict(row) if row else None
        finally:
            conn.close()

    def _create_decision(self, doc: dict) -> str:
        from database import get_db
        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO underwriting_decisions
                   (decision_id, application_id, decision, premium_adjustment,
                    conditions, rejection_reasons, pend_reasons, audit_trail,
                    state, decided_by, decided_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc["decision_id"], doc["application_id"], doc["decision"],
                    json.dumps(doc.get("premium_adjustment", {})),
                    json.dumps(doc.get("conditions", [])),
                    json.dumps(doc.get("rejection_reasons", [])),
                    json.dumps(doc.get("pend_reasons", [])),
                    json.dumps(doc.get("audit_trail", {})),
                    doc["state"], doc["decided_by"], doc["decided_at"],
                )
            )
            conn.commit()
        finally:
            conn.close()
        return doc["decision_id"]

    def _persist_requirements(self, application_id: str, requirements: list[dict]) -> None:
        from database import get_db
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db()
        try:
            for req in requirements:
                req_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT OR IGNORE INTO application_requirements
                       (requirement_id, application_id, field_name, description,
                        priority, document_type, reason, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        req_id, application_id,
                        req.get("field_name", ""), req.get("description", ""),
                        req.get("priority", "REQUIRED"), req.get("document_type"),
                        req.get("reason"), "PENDING", now,
                    )
                )
            conn.commit()
        finally:
            conn.close()

    def _fulfill_requirements(self, application_id: str, field_names: list[str]) -> None:
        from database import get_db
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db()
        try:
            for field_name in field_names:
                conn.execute(
                    """UPDATE application_requirements
                       SET status = 'FULFILLED', fulfilled_at = ?
                       WHERE application_id = ? AND field_name = ?""",
                    (now, application_id, field_name)
                )
            conn.commit()
        finally:
            conn.close()

    def _write_audit(
        self, application_id: str, input_data: dict,
        tool_called: str, prompt_version: str | None, output: dict
    ) -> None:
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
                    json.dumps(output), "VALID", now,
                )
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Result builders
    # ------------------------------------------------------------------

    def _ok(self, workflow: str, application_id: str, data: dict) -> dict:
        return {
            "status": "success",
            "workflow": workflow,
            "application_id": application_id,
            "data": data,
        }

    def _err(self, workflow: str, application_id: str, message: str) -> dict:
        return {
            "status": "error",
            "workflow": workflow,
            "application_id": application_id,
            "error": message,
        }
