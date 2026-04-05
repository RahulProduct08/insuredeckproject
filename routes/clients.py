"""routes/clients.py — Client CRUD + pipeline + lead scoring."""

from __future__ import annotations

import uuid
import json
import datetime

from flask import Blueprint, jsonify, request

from database import get_db, row_to_dict

clients_bp = Blueprint("clients", __name__)

LEAD_SOURCES = ["Referral", "Online Ad", "Cold Call", "Event", "Website",
                "Social Media", "Existing Client", "Other"]


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _log_activity(db, client_id, activity_type, description, policy_id=None, agent_id=None):
    db.execute("""
        INSERT INTO activities (activity_id, client_id, policy_id, agent_id,
            activity_type, description, metadata, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, '{}', ?)
    """, [str(uuid.uuid4()), client_id, policy_id, agent_id,
          activity_type, description, _utcnow()])


def _log_audit(db, agent_id, table_name, record_id, field_name, old_value, new_value):
    db.execute("""
        INSERT INTO audit_log (agent_id, table_name, record_id, field_name,
            old_value, new_value, changed_at)
        VALUES (?,?,?,?,?,?,?)
    """, [agent_id, table_name, record_id, field_name,
          str(old_value) if old_value is not None else None,
          str(new_value) if new_value is not None else None,
          _utcnow()])


def _compute_lead_score(client: dict, db) -> int:
    """Score 1–100 based on profile completeness, activity, stage, policies."""
    score = 30

    # Profile completeness
    if client.get("age"):
        score += 8
    if client.get("income"):
        score += 8
    if client.get("dependents"):
        score += 5
    if client.get("risk_appetite") and client["risk_appetite"] != "moderate":
        score += 4

    # Lead source (referrals score higher)
    src = client.get("lead_source", "")
    if src == "Referral":
        score += 15
    elif src in ("Existing Client",):
        score += 10
    elif src in ("Website", "Online Ad"):
        score += 5

    # Stage progression
    stage_bonus = {"Lead": 0, "Qualified": 5, "Proposal": 10,
                   "Negotiation": 15, "Closed": 20}
    score += stage_bonus.get(client.get("stage", "Lead"), 0)

    # Policy count
    policy_count = db.execute(
        "SELECT COUNT(*) FROM policies WHERE client_id=?", [client["client_id"]]
    ).fetchone()[0]
    score += min(policy_count * 5, 15)

    return min(score, 100)


# GET /api/clients
@clients_bp.route("/clients", methods=["GET"])
def list_clients():
    stage = request.args.get("stage")
    search = request.args.get("search", "").strip()
    is_active = request.args.get("is_active")
    agent_id = request.args.get("agent_id")
    lead_source = request.args.get("lead_source")

    query = "SELECT * FROM clients WHERE 1=1"
    params: list = []

    if stage:
        query += " AND stage=?"
        params.append(stage)
    if is_active is not None:
        query += " AND is_active=?"
        params.append(1 if is_active.lower() in ("1", "true") else 0)
    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        like = f"%{search}%"
        params += [like, like, like]
    if agent_id:
        query += " AND agent_id=?"
        params.append(agent_id)
    if lead_source:
        query += " AND lead_source=?"
        params.append(lead_source)

    query += " ORDER BY lead_score DESC, updated_at DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# POST /api/clients
@clients_bp.route("/clients", methods=["POST"])
def create_client():
    body = request.get_json(force=True) or {}

    name = (body.get("name") or "").strip()
    phone = (body.get("phone") or "").strip()
    email = (body.get("email") or "").strip()

    if not name or not phone or not email:
        return jsonify({"error": "name, phone, and email are required"}), 400

    db = get_db()

    # Dedup check
    existing = db.execute(
        "SELECT client_id FROM clients WHERE email=? OR (name=? AND age=?)",
        [email, name, body.get("age")]
    ).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "A client with this email or same name+age already exists",
                        "existing_id": existing["client_id"]}), 409

    client_id = str(uuid.uuid4())
    now = _utcnow()
    lead_source = body.get("lead_source", "Other")

    db.execute("""
        INSERT INTO clients
          (client_id, name, phone, email, age, income, dependents,
           risk_appetite, stage, lead_source, referred_by_client_id,
           lead_score, agent_id, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Lead', ?, ?, 30, ?, 1, ?, ?)
    """, [
        client_id, name, phone, email,
        body.get("age"), body.get("income"), body.get("dependents", 0),
        body.get("risk_appetite", "moderate"),
        lead_source, body.get("referred_by_client_id"),
        body.get("agent_id"), now, now,
    ])

    _log_activity(db, client_id, "note",
                  f"Client {name} added to portal via {lead_source}.",
                  agent_id=body.get("agent_id"))
    db.commit()

    # Recompute score
    row = row_to_dict(db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone())
    score = _compute_lead_score(row, db)
    db.execute("UPDATE clients SET lead_score=? WHERE client_id=?", [score, client_id])
    db.commit()

    row = row_to_dict(db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone())
    db.close()
    return jsonify(row), 201


# GET /api/clients/<id>
@clients_bp.route("/clients/<client_id>", methods=["GET"])
def get_client(client_id: str):
    db = get_db()
    row = db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(row_to_dict(row))


# PUT /api/clients/<id>
@clients_bp.route("/clients/<client_id>", methods=["PUT"])
def update_client(client_id: str):
    db = get_db()
    existing = db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "Client not found"}), 404

    body = request.get_json(force=True) or {}
    caller_agent = body.get("_agent_id")
    allowed = ["name", "phone", "email", "age", "income", "dependents",
               "risk_appetite", "stage", "lead_source", "referred_by_client_id", "is_active"]

    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        db.close()
        return jsonify(row_to_dict(existing))

    # Audit + activity logging for key fields
    if "stage" in updates and updates["stage"] != existing["stage"]:
        _log_activity(db, client_id, "note",
                      f"Stage: {existing['stage']} → {updates['stage']}",
                      agent_id=caller_agent)
        _log_audit(db, caller_agent, "clients", client_id, "stage",
                   existing["stage"], updates["stage"])

    for field in ["name", "email", "phone", "income", "age"]:
        if field in updates and str(updates[field]) != str(existing[field] or ""):
            _log_audit(db, caller_agent, "clients", client_id, field,
                       existing[field], updates[field])

    updates["updated_at"] = _utcnow()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    db.execute(f"UPDATE clients SET {set_clause} WHERE client_id=?",
               [*updates.values(), client_id])

    # Recompute lead score
    updated_row = row_to_dict(db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone())
    score = _compute_lead_score(updated_row, db)
    db.execute("UPDATE clients SET lead_score=? WHERE client_id=?", [score, client_id])

    db.commit()
    row = db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone()
    db.close()
    return jsonify(row_to_dict(row))


# GET /api/clients/<id>/policies
@clients_bp.route("/clients/<client_id>/policies", methods=["GET"])
def get_client_policies(client_id: str):
    db = get_db()
    rows = db.execute("""
        SELECT p.*, pr.name AS product_name, pr.commission_rate_percent
        FROM policies p
        JOIN products pr ON p.product_id=pr.product_id
        WHERE p.client_id=?
        ORDER BY p.updated_at DESC
    """, [client_id]).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# GET /api/clients/<id>/activities
@clients_bp.route("/clients/<client_id>/activities", methods=["GET"])
def get_client_activities(client_id: str):
    limit = int(request.args.get("limit", 100))
    db = get_db()
    rows = db.execute("""
        SELECT * FROM activities WHERE client_id=?
        ORDER BY timestamp DESC LIMIT ?
    """, [client_id, limit]).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# GET /api/clients/lead-sources
@clients_bp.route("/clients/lead-sources", methods=["GET"])
def lead_sources():
    return jsonify(LEAD_SOURCES)
