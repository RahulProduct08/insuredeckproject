"""routes/policies.py — Policy CRUD + FSM + eligibility validation."""

from __future__ import annotations

import uuid
import json
import datetime

from flask import Blueprint, jsonify, request

from database import get_db, row_to_dict

policies_bp = Blueprint("policies", __name__)

VALID_TRANSITIONS: dict[str, list[str]] = {
    "Draft":        ["Submitted"],
    "Submitted":    ["Underwriting", "Rejected"],
    "Underwriting": ["Approved", "Rejected"],
    "Approved":     ["Issued", "Rejected"],
    "Issued":       ["Lapsed"],
    "Rejected":     [],
    "Lapsed":       [],
}


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _log_activity(db, client_id, activity_type, description, policy_id=None, agent_id=None):
    db.execute("""
        INSERT INTO activities (activity_id, client_id, policy_id, agent_id,
            activity_type, description, metadata, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, '{}', ?)
    """, [str(uuid.uuid4()), client_id, policy_id, agent_id,
          activity_type, description, _utcnow()])


# GET /api/policies
@policies_bp.route("/policies", methods=["GET"])
def list_policies():
    status_filter = request.args.get("status")
    client_id = request.args.get("client_id")
    agent_id = request.args.get("agent_id")
    renewal_window = request.args.get("renewal_window")

    query = """
        SELECT p.*, c.name AS client_name, pr.name AS product_name
        FROM policies p
        JOIN clients c ON p.client_id=c.client_id
        JOIN products pr ON p.product_id=pr.product_id
        WHERE 1=1
    """
    params: list = []

    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",")]
        placeholders = ",".join("?" * len(statuses))
        query += f" AND p.status IN ({placeholders})"
        params += statuses
    if client_id:
        query += " AND p.client_id=?"
        params.append(client_id)
    if agent_id:
        query += " AND p.agent_id=?"
        params.append(agent_id)
    if renewal_window:
        try:
            days = int(renewal_window)
            today = datetime.date.today().isoformat()
            future = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
            query += " AND date(p.renewal_due_at) BETWEEN date(?) AND date(?)"
            params += [today, future]
        except ValueError:
            pass

    query += " ORDER BY p.updated_at DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# POST /api/policies
@policies_bp.route("/policies", methods=["POST"])
def create_policy():
    body = request.get_json(force=True) or {}

    client_id = body.get("client_id")
    product_id = body.get("product_id")
    premium = body.get("premium")

    if not client_id or not product_id or premium is None:
        return jsonify({"error": "client_id, product_id, and premium are required"}), 400

    db = get_db()

    client = row_to_dict(db.execute("SELECT * FROM clients WHERE client_id=?", [client_id]).fetchone())
    if not client:
        db.close()
        return jsonify({"error": "Client not found"}), 404

    product = row_to_dict(db.execute("SELECT * FROM products WHERE product_id=?", [product_id]).fetchone())
    if not product:
        db.close()
        return jsonify({"error": "Product not found"}), 404

    # Eligibility validation
    errors = []
    age = client.get("age")
    income = client.get("income")
    premium_f = float(premium)

    if age is not None:
        if product.get("min_age") and age < product["min_age"]:
            errors.append(f"Client age ({age}) below product minimum ({product['min_age']})")
        if product.get("max_age") and age > product["max_age"]:
            errors.append(f"Client age ({age}) exceeds product maximum ({product['max_age']})")
    if income is not None and product.get("min_income") and income < product["min_income"]:
        errors.append(f"Client income (${income:,.0f}) below product minimum (${product['min_income']:,.0f})")
    if premium_f < product.get("min_premium", 0):
        errors.append(f"Premium (${premium_f:,.2f}) below product minimum (${product['min_premium']:,.2f})")
    if premium_f > product.get("max_premium", 9_999_999):
        errors.append(f"Premium (${premium_f:,.2f}) exceeds product maximum (${product['max_premium']:,.2f})")

    if errors:
        db.close()
        return jsonify({"error": "Eligibility check failed", "details": errors}), 422

    docs = body.get("documents_checklist", ["ID Proof", "Income Proof", "Medical Report", "Signed Proposal Form"])
    policy_id = str(uuid.uuid4())
    now = _utcnow()
    agent_id = body.get("agent_id")

    db.execute("""
        INSERT INTO policies
          (policy_id, client_id, product_id, agent_id, premium, status,
           documents_checklist, documents_attached, issued_at, renewal_due_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'Draft', ?, '[]', NULL, NULL, ?, ?)
    """, [policy_id, client_id, product_id, agent_id, premium_f, json.dumps(docs), now, now])

    db.execute("""
        INSERT INTO policy_status_history (policy_id, from_status, to_status, changed_at)
        VALUES (?, NULL, 'Draft', ?)
    """, [policy_id, now])

    _log_activity(db, client_id, "policy_created",
                  f"Policy created for {product['name']}. Status: Draft.",
                  policy_id, agent_id)

    db.commit()
    row = db.execute("""
        SELECT p.*, c.name AS client_name, pr.name AS product_name
        FROM policies p
        JOIN clients c ON p.client_id=c.client_id
        JOIN products pr ON p.product_id=pr.product_id
        WHERE p.policy_id=?
    """, [policy_id]).fetchone()
    db.close()
    return jsonify(row_to_dict(row)), 201


# GET /api/policies/<id>
@policies_bp.route("/policies/<policy_id>", methods=["GET"])
def get_policy(policy_id: str):
    db = get_db()
    row = db.execute("""
        SELECT p.*, c.name AS client_name, pr.name AS product_name, pr.commission_rate_percent
        FROM policies p
        JOIN clients c ON p.client_id=c.client_id
        JOIN products pr ON p.product_id=pr.product_id
        WHERE p.policy_id=?
    """, [policy_id]).fetchone()

    if not row:
        db.close()
        return jsonify({"error": "Policy not found"}), 404

    policy = row_to_dict(row)
    history = db.execute("""
        SELECT * FROM policy_status_history WHERE policy_id=? ORDER BY changed_at ASC
    """, [policy_id]).fetchall()
    policy["status_history"] = [dict(h) for h in history]
    db.close()
    return jsonify(policy)


# PUT /api/policies/<id>
@policies_bp.route("/policies/<policy_id>", methods=["PUT"])
def update_policy(policy_id: str):
    db = get_db()
    existing = db.execute("SELECT * FROM policies WHERE policy_id=?", [policy_id]).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "Policy not found"}), 404

    body = request.get_json(force=True) or {}
    allowed = ["premium", "documents_checklist", "documents_attached"]

    updates: dict = {}
    for k in allowed:
        if k in body:
            val = body[k]
            updates[k] = json.dumps(val) if isinstance(val, list) else val

    if not updates:
        db.close()
        return jsonify(row_to_dict(existing))

    updates["updated_at"] = _utcnow()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    db.execute(f"UPDATE policies SET {set_clause} WHERE policy_id=?",
               [*updates.values(), policy_id])
    db.commit()

    row = db.execute("""
        SELECT p.*, c.name AS client_name, pr.name AS product_name
        FROM policies p
        JOIN clients c ON p.client_id=c.client_id
        JOIN products pr ON p.product_id=pr.product_id
        WHERE p.policy_id=?
    """, [policy_id]).fetchone()
    db.close()
    return jsonify(row_to_dict(row))


# POST /api/policies/<id>/transition
@policies_bp.route("/policies/<policy_id>/transition", methods=["POST"])
def transition_policy(policy_id: str):
    body = request.get_json(force=True) or {}
    new_status = (body.get("new_status") or "").strip()
    agent_id = body.get("agent_id")

    if not new_status:
        return jsonify({"error": "new_status is required"}), 400

    db = get_db()
    policy = db.execute("SELECT * FROM policies WHERE policy_id=?", [policy_id]).fetchone()
    if not policy:
        db.close()
        return jsonify({"error": "Policy not found"}), 404

    current_status = policy["status"]
    client_id = policy["client_id"]
    product_id = policy["product_id"]
    premium = policy["premium"]

    allowed_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        db.close()
        return jsonify({"error": f"Invalid transition: {current_status} → {new_status}",
                        "allowed": allowed_next}), 400

    now = _utcnow()
    extra_updates = ""
    extra_params: list = []
    commission_record = None

    if new_status == "Issued":
        renewal_due_at = (datetime.datetime.now(datetime.timezone.utc) +
                          datetime.timedelta(days=365)).isoformat()
        extra_updates = ", issued_at=?, renewal_due_at=?"
        extra_params = [now, renewal_due_at]

        db.execute("UPDATE clients SET stage='Closed', updated_at=? WHERE client_id=?",
                   [now, client_id])

        product = db.execute("SELECT * FROM products WHERE product_id=?", [product_id]).fetchone()
        rate = product["commission_rate_percent"]
        commission_amount = round(float(premium) * rate / 100, 2)
        commission_id = str(uuid.uuid4())

        db.execute("""
            INSERT INTO commissions
              (commission_id, policy_id, product_id, client_id, event_type,
               amount, rate_percent, premium, agent_id, recorded_at)
            VALUES (?, ?, ?, ?, 'sale', ?, ?, ?, ?, ?)
        """, [commission_id, policy_id, product_id, client_id,
              commission_amount, rate, float(premium), agent_id, now])

        commission_record = {"commission_id": commission_id,
                             "event_type": "sale", "amount": commission_amount,
                             "rate_percent": rate}

        _log_activity(db, client_id, "commission_recorded",
                      f"Sale commission of ${commission_amount:,.2f} at {rate}%.",
                      policy_id, agent_id)

    elif new_status == "Rejected":
        client = db.execute("SELECT stage FROM clients WHERE client_id=?", [client_id]).fetchone()
        if client and client["stage"] in ("Closed", "Proposal", "Negotiation"):
            db.execute("UPDATE clients SET stage='Negotiation', updated_at=? WHERE client_id=?",
                       [now, client_id])
        _log_activity(db, client_id, "follow_up",
                      "Policy rejected. Review with client and consider alternatives.",
                      policy_id, agent_id)

    db.execute(f"""
        UPDATE policies SET status=?, updated_at=?{extra_updates} WHERE policy_id=?
    """, [new_status, now] + extra_params + [policy_id])

    db.execute("""
        INSERT INTO policy_status_history (policy_id, from_status, to_status, changed_at)
        VALUES (?, ?, ?, ?)
    """, [policy_id, current_status, new_status, now])

    _log_activity(db, client_id, "status_change",
                  f"Policy: {current_status} → {new_status}.", policy_id, agent_id)

    db.commit()
    db.close()

    return jsonify({"policy_id": policy_id, "previous_status": current_status,
                    "new_status": new_status, "commission_record": commission_record})
