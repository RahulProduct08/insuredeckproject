"""
routes/activities.py
--------------------
Activity log — system-generated events + manual agent notes.

System activities are written inline by other route handlers.
This endpoint is for manual notes and for reading the timeline.

Endpoints:
    GET    /api/activities          list; ?client_id=&policy_id=&activity_type=&limit=
    POST   /api/activities          create manual note
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from database import get_db, row_to_dict

activities_bp = Blueprint("activities", __name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# GET /api/activities
# ---------------------------------------------------------------------------
@activities_bp.route("/activities", methods=["GET"])
def list_activities():
    client_id = request.args.get("client_id")
    policy_id = request.args.get("policy_id")
    activity_type = request.args.get("activity_type")
    limit = int(request.args.get("limit", 50))

    query = "SELECT * FROM activities WHERE 1=1"
    params: list = []

    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    if policy_id:
        query += " AND policy_id = ?"
        params.append(policy_id)
    if activity_type:
        query += " AND activity_type = ?"
        params.append(activity_type)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    db = get_db()
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# ---------------------------------------------------------------------------
# POST /api/activities
# ---------------------------------------------------------------------------
@activities_bp.route("/activities", methods=["POST"])
def create_activity():
    body = request.get_json(force=True) or {}

    client_id = body.get("client_id")
    description = (body.get("description") or "").strip()
    activity_type = body.get("activity_type", "note")

    if not client_id or not description:
        return jsonify({"error": "client_id and description are required"}), 400

    db = get_db()

    # Validate client exists
    client = db.execute("SELECT client_id FROM clients WHERE client_id=?", [client_id]).fetchone()
    if not client:
        db.close()
        return jsonify({"error": "Client not found"}), 404

    policy_id = body.get("policy_id")
    if policy_id:
        pol = db.execute("SELECT policy_id FROM policies WHERE policy_id=?", [policy_id]).fetchone()
        if not pol:
            db.close()
            return jsonify({"error": "Policy not found"}), 404

    activity_id = str(uuid.uuid4())
    now = _utcnow()

    db.execute("""
        INSERT INTO activities
          (activity_id, client_id, policy_id, activity_type, description, metadata, timestamp)
        VALUES (?, ?, ?, ?, ?, '{}', ?)
    """, [activity_id, client_id, policy_id, activity_type, description, now])

    db.commit()
    row = db.execute("SELECT * FROM activities WHERE activity_id=?", [activity_id]).fetchone()
    db.close()
    return jsonify(row_to_dict(row)), 201
