"""routes/auth.py — login, register, token refresh."""

import uuid
import hashlib
import datetime
from flask import Blueprint, request, jsonify, g
import jwt

from database import get_db, row_to_dict

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

SECRET = "insuredesk-jwt-secret-2024"  # In prod: read from env var


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def make_token(agent: dict) -> str:
    payload = {
        "agent_id": agent["agent_id"],
        "role": agent["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return None


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    required = ["name", "email", "password"]
    if not all(data.get(k) for k in required):
        return jsonify({"error": "name, email, password required"}), 400

    db = get_db()
    existing = db.execute("SELECT agent_id FROM agents WHERE email=?", (data["email"],)).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "Email already registered"}), 409

    now = datetime.datetime.utcnow().isoformat()
    agent_id = f"agent-{uuid.uuid4().hex[:8]}"
    db.execute(
        """INSERT INTO agents (agent_id, name, email, password_hash, role, npn,
           license_states, phone, is_active, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,1,?,?)""",
        (agent_id, data["name"], data["email"], _hash(data["password"]),
         data.get("role", "agent"), data.get("npn"), data.get("license_states"),
         data.get("phone"), now, now),
    )
    db.commit()
    agent = row_to_dict(db.execute("SELECT * FROM agents WHERE agent_id=?", (agent_id,)).fetchone())
    db.close()
    agent.pop("password_hash", None)
    return jsonify({"token": make_token(agent), "agent": agent}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    db = get_db()
    row = db.execute("SELECT * FROM agents WHERE email=?", (data.get("email", ""),)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Invalid credentials"}), 401
    agent = row_to_dict(row)
    if agent["password_hash"] != _hash(data.get("password", "")):
        return jsonify({"error": "Invalid credentials"}), 401
    agent.pop("password_hash", None)
    return jsonify({"token": make_token(agent), "agent": agent})


@auth_bp.route("/me", methods=["GET"])
def me():
    token = (request.headers.get("Authorization", "") or "").removeprefix("Bearer ")
    payload = decode_token(token)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    agent = row_to_dict(db.execute("SELECT * FROM agents WHERE agent_id=?", (payload["agent_id"],)).fetchone())
    db.close()
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    agent.pop("password_hash", None)
    return jsonify(agent)
