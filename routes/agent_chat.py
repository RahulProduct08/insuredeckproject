"""
routes/agent_chat.py — AI-DIE (AI Digital Insurance Engine) chat endpoints.

Endpoints:
    POST  /api/agent-chat/conversations              — Create a new chat session
    POST  /api/agent-chat/conversations/<id>/messages — Send a message, get AI-DIE reply
    GET   /api/agent-chat/conversations/<id>/messages — Fetch conversation history
"""

import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from database import get_db, row_to_dict
from tools.ai_die_chat import send_message

agent_chat_bp = Blueprint("agent_chat", __name__, url_prefix="/api/agent-chat")

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"

# Sliding window: fetch last N messages for context to avoid loading full history
CONVERSATION_CONTEXT_LIMIT = 20


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# POST /api/agent-chat/conversations — create session
# ---------------------------------------------------------------------------

@agent_chat_bp.route("/conversations", methods=["POST"])
def create_conversation():
    data = request.get_json(silent=True) or {}
    conversation_id = str(uuid.uuid4())
    agent_id = data.get("agent_id")
    session_label = data.get("session_label", f"Session {_now()[:10]}")

    db = get_db()
    try:
        db.execute(
            "INSERT INTO agent_conversations (id, agent_id, session_label, created_at) VALUES (?,?,?,?)",
            (conversation_id, agent_id, session_label, _now()),
        )
        db.commit()
    except Exception as e:
        db.close()
        return jsonify({"error": f"Failed to create conversation: {str(e)}"}), 500
    finally:
        db.close()

    return jsonify({"conversation_id": conversation_id, "session_label": session_label}), 201


# ---------------------------------------------------------------------------
# POST /api/agent-chat/conversations/<id>/messages — send message
# ---------------------------------------------------------------------------

@agent_chat_bp.route("/conversations/<conversation_id>/messages", methods=["POST"])
def send_chat_message(conversation_id):
    data = request.get_json(silent=True) or {}
    user_content = data.get("content", "").strip()
    if not user_content:
        return jsonify({"error": "content is required"}), 400

    db = get_db()
    try:
        # Verify conversation exists
        row = db.execute(
            "SELECT id FROM agent_conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "conversation not found"}), 404

        # Fetch last N messages for context (sliding window) to avoid loading full history
        history_rows = db.execute(
            "SELECT role, content FROM agent_messages WHERE conversation_id = ? "
            "ORDER BY created_at DESC LIMIT ? "
            "ORDER BY created_at ASC",
            (conversation_id, CONVERSATION_CONTEXT_LIMIT),
        ).fetchall()
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows]

        # Call AI-DIE
        try:
            reply = send_message(history, user_content)
        except (ValueError, Exception) as e:
            return jsonify({"error": f"AI service unavailable: {str(e)}"}), 503

        if not reply or not reply.strip():
            return jsonify({"error": "Empty response from AI service"}), 500

        # Persist both messages in single batch operation
        user_msg_id = str(uuid.uuid4())
        asst_msg_id = str(uuid.uuid4())
        now = _now()

        db.executemany(
            "INSERT INTO agent_messages (id, conversation_id, role, content, created_at) VALUES (?,?,?,?,?)",
            [
                (user_msg_id, conversation_id, ROLE_USER, user_content, now),
                (asst_msg_id, conversation_id, ROLE_ASSISTANT, reply, now),
            ],
        )
        db.commit()

    except Exception as e:
        return jsonify({"error": f"Failed to send message: {str(e)}"}), 500
    finally:
        db.close()

    return jsonify({"reply": reply}), 201


# ---------------------------------------------------------------------------
# GET /api/agent-chat/conversations/<id>/messages — fetch history
# ---------------------------------------------------------------------------

@agent_chat_bp.route("/conversations/<conversation_id>/messages", methods=["GET"])
def get_messages(conversation_id):
    db = get_db()
    try:
        row = db.execute(
            "SELECT id FROM agent_conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "conversation not found"}), 404

        rows = db.execute(
            "SELECT id, role, content, created_at FROM agent_messages "
            "WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
    except Exception as e:
        return jsonify({"error": f"Failed to fetch messages: {str(e)}"}), 500
    finally:
        db.close()

    return jsonify([row_to_dict(r) for r in rows]), 200
