"""
routes/clients.py
-----------------
Client CRUD + pipeline-stage management.

Endpoints:
    GET    /api/clients                     list with optional ?stage=&search=&is_active=
    POST   /api/clients                     create
    GET    /api/clients/<id>                detail
    PUT    /api/clients/<id>                update
    GET    /api/clients/<id>/policies       client's policies
    GET    /api/clients/<id>/activities     client's activity timeline
"""

from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from database import get_db, row_to_dict

clients_bp = Blueprint("clients", __name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_activity(db, client_id: str, activity_type: str, description: str, policy_id: str | None = None) -> None:
    db.execute("""
        INSERT INTO activities (activity_id, client_id, policy_id, activity_type, description, metadata, timestamp)
        VALUES (?, ?, ?, ?, ?, '{}', ?)
    """, [str(uuid.uuid4()), client_id, policy_id, activity_type, description, _utcnow()])


# ---------------------------------------------------------------------------
# GET /api/clients
# ---------------------------------------------------------------------------
@clients_bp.route("/clients", methods=["GET"])
def list_clients():
    stage = request.args.get("stage")
    search = request.args.get("search", "").strip()
    is_active = request.args.get("is_active")

    query = "SELECT * FROM clients WHERE 1=1"
    params: list = []

    if stage:
        query += " AND stage = ?"
        params.append(stage)
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active.lower() in ("1", "true") else 0)
    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        like = f"%{search}%"
        params += [like, like, like]

    query += " ORDER BY updated_at DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    db.close()

    return jsonify([row_to_dict(r) for r in rows])


# ---------------------------------------------------------------------------
# POST /api/clients
# ---------------------------------------------------------------------------
@clients_bp.route("/clients", methods=["POST"])
def create_client():
    body = request.get_json(force=True) or {}

    name = (body.get("name") or "").strip()
    phone = (body.get("phone") or "").strip()
    email = (body.get("email") or "").strip()

    if not name or not phone or not email:
        return jsonify({"error": "name, phone, and email are required"}), 400

    client_id = str(uuid.uuid4())
    now = _utcnow()

    db = get_db()
    db.execute("""
        INSERT INTO clients
          (client_id, name, phone, email, age, income, dependents,
           risk_appetite, stage, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Lead', 1, ?, ?)
    """, [
        client_id, name, phone, email,
        body.get("age"), body.get("income"), body.get("dependents", 0),
        body.get("risk_appetite", "moderate"),
        now, now,
    ])

    _log_activity(db, client_id, "note", f"Client {name} added to portal.")
    db.commit()

    row = db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone()
    db.close()
    return jsonify(row_to_dict(row)), 201


# ---------------------------------------------------------------------------
# GET /api/clients/<id>
# ---------------------------------------------------------------------------
@clients_bp.route("/clients/<client_id>", methods=["GET"])
def get_client(client_id: str):
    db = get_db()
    row = db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(row_to_dict(row))


# ---------------------------------------------------------------------------
# PUT /api/clients/<id>
# ---------------------------------------------------------------------------
@clients_bp.route("/clients/<client_id>", methods=["PUT"])
def update_client(client_id: str):
    db = get_db()
    existing = db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "Client not found"}), 404

    body = request.get_json(force=True) or {}
    allowed = ["name", "phone", "email", "age", "income", "dependents",
               "risk_appetite", "stage", "is_active"]

    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        db.close()
        return jsonify(row_to_dict(existing))

    updates["updated_at"] = _utcnow()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [client_id]

    db.execute(f"UPDATE clients SET {set_clause} WHERE client_id = ?", values)

    if "stage" in updates:
        old_stage = existing["stage"]
        new_stage = updates["stage"]
        if old_stage != new_stage:
            _log_activity(db, client_id, "note", f"Pipeline stage changed: {old_stage} → {new_stage}.")

    db.commit()
    row = db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone()
    db.close()
    return jsonify(row_to_dict(row))


# ---------------------------------------------------------------------------
# GET /api/clients/<id>/policies
# ---------------------------------------------------------------------------
@clients_bp.route("/clients/<client_id>/policies", methods=["GET"])
def get_client_policies(client_id: str):
    db = get_db()
    rows = db.execute("""
        SELECT p.*, pr.name AS product_name, pr.commission_rate_percent
        FROM policies p
        JOIN products pr ON p.product_id = pr.product_id
        WHERE p.client_id = ?
        ORDER BY p.updated_at DESC
    """, [client_id]).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# ---------------------------------------------------------------------------
# GET /api/clients/<id>/activities
# ---------------------------------------------------------------------------
@clients_bp.route("/clients/<client_id>/activities", methods=["GET"])
def get_client_activities(client_id: str):
    limit = int(request.args.get("limit", 100))
    db = get_db()
    rows = db.execute("""
        SELECT * FROM activities
        WHERE client_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, [client_id, limit]).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])
