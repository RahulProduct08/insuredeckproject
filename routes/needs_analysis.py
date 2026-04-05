"""routes/needs_analysis.py — needs analysis worksheet + product recommendations."""

import uuid
import json
import datetime
from flask import Blueprint, request, jsonify

from database import get_db, row_to_dict

needs_bp = Blueprint("needs_analysis", __name__, url_prefix="/api/needs-analysis")


def _recommend_products(answers: dict, db) -> list:
    """Score products by suitability given answers."""
    age = answers.get("age", 30)
    income = answers.get("annual_income", 50000)
    has_dependents = answers.get("has_dependents", False)
    health_concern = answers.get("health_concern", False)
    vehicle = answers.get("has_vehicle", False)

    products = db.execute(
        "SELECT * FROM products WHERE is_active=1 AND min_age<=? AND max_age>=? AND min_income<=?",
        (age, age, income)
    ).fetchall()

    scored = []
    for p in products:
        prod = row_to_dict(p)
        score = 50
        name_lower = prod["name"].lower()
        if "life" in name_lower and has_dependents:
            score += 30
        if "health" in name_lower and health_concern:
            score += 25
        if "auto" in name_lower and vehicle:
            score += 25
        if "critical" in name_lower and age > 40:
            score += 20
        if "whole life" in name_lower and income > 80000:
            score += 15
        scored.append({**prod, "suitability_score": score})

    scored.sort(key=lambda x: x["suitability_score"], reverse=True)
    return scored[:3]


@needs_bp.route("/client/<client_id>", methods=["GET"])
def get_for_client(client_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM needs_analyses WHERE client_id=? ORDER BY created_at DESC",
        (client_id,)
    ).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


@needs_bp.route("", methods=["POST"])
def create_analysis():
    data = request.get_json()
    if not data.get("client_id"):
        return jsonify({"error": "client_id required"}), 400

    db = get_db()
    answers = data.get("answers", {})

    # Pull client data to supplement answers
    client = row_to_dict(db.execute("SELECT * FROM clients WHERE client_id=?", (data["client_id"],)).fetchone())
    if client:
        answers.setdefault("age", client.get("age"))
        answers.setdefault("annual_income", client.get("income"))
        answers.setdefault("has_dependents", (client.get("dependents") or 0) > 0)

    recommended = _recommend_products(answers, db)
    now = datetime.datetime.utcnow().isoformat()
    analysis_id = f"na-{uuid.uuid4().hex[:8]}"

    db.execute(
        """INSERT INTO needs_analyses (analysis_id, client_id, agent_id, answers,
           recommended_products, notes, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (analysis_id, data["client_id"], data.get("agent_id"),
         json.dumps(answers), json.dumps(recommended),
         data.get("notes"), now, now),
    )

    # Log activity
    act_id = f"act-{uuid.uuid4().hex[:8]}"
    db.execute(
        """INSERT INTO activities (activity_id, client_id, agent_id, activity_type, description, timestamp)
           VALUES (?,?,?,?,?,?)""",
        (act_id, data["client_id"], data.get("agent_id"),
         "needs_analysis", "Needs analysis worksheet completed", now),
    )

    db.commit()
    result = row_to_dict(db.execute("SELECT * FROM needs_analyses WHERE analysis_id=?", (analysis_id,)).fetchone())
    db.close()
    return jsonify(result), 201
