"""routes/tasks.py — task CRUD."""

import uuid
import datetime
from flask import Blueprint, request, jsonify

from database import get_db, row_to_dict

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")

_Q_LIST = """
    SELECT t.*, c.name as client_name
    FROM tasks t
    LEFT JOIN clients c ON t.client_id = c.client_id
"""


@tasks_bp.route("", methods=["GET"])
def list_tasks():
    agent_id = request.args.get("agent_id")
    status = request.args.get("status")
    db = get_db()
    q = _Q_LIST + " WHERE 1=1"
    params = []
    if agent_id:
        q += " AND t.agent_id=?"
        params.append(agent_id)
    if status:
        q += " AND t.status=?"
        params.append(status)
    q += " ORDER BY t.due_date ASC, t.priority DESC"
    rows = db.execute(q, params).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


@tasks_bp.route("", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data.get("title"):
        return jsonify({"error": "title required"}), 400
    now = datetime.datetime.utcnow().isoformat()
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    db = get_db()
    db.execute(
        """INSERT INTO tasks (task_id, client_id, policy_id, agent_id, title,
           description, priority, status, due_date, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (task_id, data.get("client_id"), data.get("policy_id"),
         data.get("agent_id"), data["title"], data.get("description"),
         data.get("priority", "medium"), "open",
         data.get("due_date"), now, now),
    )
    db.commit()
    task = row_to_dict(db.execute(_Q_LIST + " WHERE t.task_id=?", (task_id,)).fetchone())
    db.close()
    return jsonify(task), 201


@tasks_bp.route("/<task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json()
    allowed = {"title", "description", "priority", "status", "due_date"}
    patch = {k: v for k, v in data.items() if k in allowed}
    now = datetime.datetime.utcnow().isoformat()
    patch["updated_at"] = now
    if patch.get("status") == "completed":
        patch["completed_at"] = now
    sets = ", ".join(f"{k}=?" for k in patch)
    db = get_db()
    db.execute(f"UPDATE tasks SET {sets} WHERE task_id=?", (*patch.values(), task_id))
    db.commit()
    task = row_to_dict(db.execute(_Q_LIST + " WHERE t.task_id=?", (task_id,)).fetchone())
    db.close()
    return jsonify(task)


@tasks_bp.route("/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
    db.commit()
    db.close()
    return jsonify({"ok": True})
