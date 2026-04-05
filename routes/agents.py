"""routes/agents.py — agent CRUD + profile management."""

import datetime
from flask import Blueprint, request, jsonify

from database import get_db, row_to_dict
from routes.auth import decode_token

agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")


def _current_agent(req):
    token = (req.headers.get("Authorization", "") or "").removeprefix("Bearer ")
    return decode_token(token)


@agents_bp.route("", methods=["GET"])
def list_agents():
    caller = _current_agent(request)
    db = get_db()
    rows = db.execute("SELECT * FROM agents WHERE is_active=1 ORDER BY name").fetchall()
    db.close()
    agents = [row_to_dict(r) for r in rows]
    for a in agents:
        a.pop("password_hash", None)
    return jsonify(agents)


@agents_bp.route("/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    db = get_db()
    row = db.execute("SELECT * FROM agents WHERE agent_id=?", (agent_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    agent = row_to_dict(row)
    agent.pop("password_hash", None)
    return jsonify(agent)


@agents_bp.route("/<agent_id>", methods=["PATCH"])
def update_agent(agent_id):
    data = request.get_json()
    allowed = {"name", "phone", "npn", "license_states"}
    patch = {k: v for k, v in data.items() if k in allowed}
    if not patch:
        return jsonify({"error": "Nothing to update"}), 400
    patch["updated_at"] = datetime.datetime.utcnow().isoformat()
    sets = ", ".join(f"{k}=?" for k in patch)
    db = get_db()
    db.execute(f"UPDATE agents SET {sets} WHERE agent_id=?", (*patch.values(), agent_id))
    db.commit()
    agent = row_to_dict(db.execute("SELECT * FROM agents WHERE agent_id=?", (agent_id,)).fetchone())
    db.close()
    agent.pop("password_hash", None)
    return jsonify(agent)
