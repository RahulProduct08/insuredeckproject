"""
routes/underwriting.py
-----------------------
REST API endpoints for the underwriting system (WAT Framework v3).

Endpoints:
    POST   /api/underwriting/applications              — Start underwriting application
    GET    /api/underwriting/applications/<id>         — Get application + state
    POST   /api/underwriting/applications/<id>/run     — Run full underwriting pipeline
    GET    /api/underwriting/applications/<id>/risk    — Get risk profile
    GET    /api/underwriting/applications/<id>/decision — Get decision + audit trail
    POST   /api/underwriting/applications/<id>/requirements — Submit fulfilled requirements
    GET    /api/underwriting/applications/<id>/audit   — Get full audit log
    GET    /api/underwriting/queue                     — Underwriter case queue
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

underwriting_bp = Blueprint("underwriting", __name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Helper: fetch application or 404
# ---------------------------------------------------------------------------

def _get_app_or_404(application_id: str):
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


# ---------------------------------------------------------------------------
# POST /api/underwriting/applications
# Create a new underwriting application
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/applications", methods=["POST"])
def create_application():
    """
    Start a new underwriting application.

    Body:
        client_id    (required)
        product_id   (required)
        policy_id    (optional) — link to existing policy in Draft/Submitted state
        raw_input    (optional) — forms, notes, documents
    """
    body = request.get_json(force=True) or {}

    client_id = body.get("client_id")
    product_id = body.get("product_id")

    if not client_id or not product_id:
        return jsonify({"error": "client_id and product_id are required"}), 400

    from database import get_db
    conn = get_db()
    try:
        # Validate client exists
        client = conn.execute(
            "SELECT client_id, is_active FROM clients WHERE client_id = ?", (client_id,)
        ).fetchone()
        if not client:
            return jsonify({"error": f"Client '{client_id}' not found"}), 404
        if not client["is_active"]:
            return jsonify({"error": f"Client '{client_id}' is inactive"}), 400

        # Validate product exists
        product = conn.execute(
            "SELECT product_id, is_active FROM products WHERE product_id = ?", (product_id,)
        ).fetchone()
        if not product:
            return jsonify({"error": f"Product '{product_id}' not found"}), 404

        application_id = str(uuid.uuid4())
        now = _now()
        policy_id = body.get("policy_id")
        raw_input = body.get("raw_input") or {}

        conn.execute(
            """INSERT INTO underwriting_applications
               (application_id, client_id, product_id, policy_id, state,
                raw_input, structured_data, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                application_id, client_id, product_id, policy_id,
                "CREATED",
                json.dumps(raw_input), json.dumps({}),
                now, now,
            )
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "application_id": application_id,
        "client_id": client_id,
        "product_id": product_id,
        "state": "CREATED",
        "created_at": now,
    }), 201


# ---------------------------------------------------------------------------
# GET /api/underwriting/applications/<id>
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/applications/<application_id>", methods=["GET"])
def get_application(application_id: str):
    """Get application record + current state summary."""
    from agent.orchestrator import Orchestrator
    orch = Orchestrator()
    result = orch.run("get_underwriting_status", application_id=application_id)
    if result["status"] == "error":
        return jsonify({"error": result["error"]}), 404
    return jsonify(result["data"]), 200


# ---------------------------------------------------------------------------
# POST /api/underwriting/applications/<id>/run
# Run the full underwriting pipeline
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/applications/<application_id>/run", methods=["POST"])
def run_underwriting(application_id: str):
    """
    Run the full underwriting pipeline:
    intake → data_aggregation → risk_classification → decision

    Body:
        raw_input      (optional) — additional input data
        external_data  (optional) — external data to enrich the application
        decided_by     (optional) — agent ID (default: "SYSTEM")
    """
    body = request.get_json(force=True) or {}

    app = _get_app_or_404(application_id)
    if app is None:
        return jsonify({"error": f"Application '{application_id}' not found"}), 404

    from agent.orchestrator import Orchestrator
    orch = Orchestrator()
    result = orch.run(
        "underwrite_application",
        application_id=application_id,
        raw_input=body.get("raw_input"),
        external_data=body.get("external_data"),
        decided_by=body.get("decided_by", "SYSTEM"),
    )

    if result["status"] == "error":
        return jsonify({"error": result["error"]}), 422

    return jsonify(result["data"]), 200


# ---------------------------------------------------------------------------
# GET /api/underwriting/applications/<id>/risk
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/applications/<application_id>/risk", methods=["GET"])
def get_risk_profile(application_id: str):
    """Get the risk profile for an application."""
    from database import get_db, row_to_dict
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM risk_profiles WHERE application_id = ? ORDER BY classified_at DESC LIMIT 1",
            (application_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Risk profile not found — run risk classification first"}), 404
        return jsonify(row_to_dict(row)), 200
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# GET /api/underwriting/applications/<id>/decision
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/applications/<application_id>/decision", methods=["GET"])
def get_decision(application_id: str):
    """Get the underwriting decision + audit trail for an application."""
    from database import get_db, row_to_dict
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM underwriting_decisions WHERE application_id = ? ORDER BY decided_at DESC LIMIT 1",
            (application_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Decision not found — run underwriting pipeline first"}), 404
        return jsonify(row_to_dict(row)), 200
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# POST /api/underwriting/applications/<id>/requirements
# Submit fulfilled requirements or get outstanding ones
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/applications/<application_id>/requirements", methods=["GET", "POST"])
def requirements(application_id: str):
    """
    GET  — Return outstanding requirements for this application.
    POST — Submit fulfilled data to satisfy requirements.

    POST body:
        fulfilled_data (optional) — dict of field_name → value
    """
    app = _get_app_or_404(application_id)
    if app is None:
        return jsonify({"error": f"Application '{application_id}' not found"}), 404

    if request.method == "GET":
        from database import get_db, row_to_dict
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM application_requirements WHERE application_id = ? ORDER BY created_at",
                (application_id,)
            ).fetchall()
            return jsonify([row_to_dict(r) for r in rows]), 200
        finally:
            conn.close()

    # POST — fulfill requirements
    body = request.get_json(force=True) or {}
    fulfilled_data = body.get("fulfilled_data")

    from agent.orchestrator import Orchestrator
    orch = Orchestrator()
    result = orch.run(
        "fulfill_requirements",
        application_id=application_id,
        fulfilled_data=fulfilled_data,
    )

    if result["status"] == "error":
        return jsonify({"error": result["error"]}), 422

    return jsonify(result["data"]), 200


# ---------------------------------------------------------------------------
# GET /api/underwriting/applications/<id>/audit
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/applications/<application_id>/audit", methods=["GET"])
def get_audit_log(application_id: str):
    """Get the full audit log for an underwriting application."""
    from database import get_db, row_to_dict
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM underwriting_audit_logs WHERE application_id = ? ORDER BY timestamp",
            (application_id,)
        ).fetchall()
        return jsonify([row_to_dict(r) for r in rows]), 200
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# POST /api/underwriting/applications/<id>/issue
# Issue the policy for an approved application
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/applications/<application_id>/issue", methods=["POST"])
def issue_policy(application_id: str):
    """Issue the policy for an APPROVED underwriting application."""
    app = _get_app_or_404(application_id)
    if app is None:
        return jsonify({"error": f"Application '{application_id}' not found"}), 404

    from agent.orchestrator import Orchestrator
    orch = Orchestrator()
    result = orch.run("issue_policy_uw", application_id=application_id)

    if result["status"] == "error":
        return jsonify({"error": result["error"]}), 422

    return jsonify(result["data"]), 200


# ---------------------------------------------------------------------------
# GET /api/underwriting/queue
# Underwriter case queue — PENDED and borderline cases
# ---------------------------------------------------------------------------

@underwriting_bp.route("/underwriting/queue", methods=["GET"])
def underwriter_queue():
    """
    Return the underwriter case queue:
    Applications in PENDED state or requiring manual review.
    """
    from database import get_db, row_to_dict
    conn = get_db()
    try:
        # PENDED applications
        pended = conn.execute(
            """SELECT ua.application_id, ua.client_id, ua.product_id, ua.state,
                      ua.created_at, ua.updated_at,
                      rp.risk_score, rp.risk_class, rp.manual_review_required
               FROM underwriting_applications ua
               LEFT JOIN risk_profiles rp ON rp.application_id = ua.application_id
               WHERE ua.state IN ('PENDED')
               ORDER BY ua.updated_at DESC
               LIMIT 100"""
        ).fetchall()

        # Manual review cases (RISK_CLASSIFIED with manual_review_required = 1)
        manual_review = conn.execute(
            """SELECT ua.application_id, ua.client_id, ua.product_id, ua.state,
                      ua.created_at, ua.updated_at,
                      rp.risk_score, rp.risk_class, rp.manual_review_required,
                      rp.review_reason
               FROM underwriting_applications ua
               JOIN risk_profiles rp ON rp.application_id = ua.application_id
               WHERE ua.state = 'RISK_CLASSIFIED' AND rp.manual_review_required = 1
               ORDER BY rp.risk_score DESC
               LIMIT 100"""
        ).fetchall()

        return jsonify({
            "pended": [row_to_dict(r) for r in pended],
            "manual_review": [row_to_dict(r) for r in manual_review],
            "total": len(pended) + len(manual_review),
        }), 200
    finally:
        conn.close()
