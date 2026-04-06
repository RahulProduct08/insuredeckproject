"""routes/hierarchy.py — agent hierarchy graph + commission ledger engine."""

import datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from flask import Blueprint, request, jsonify

from database import get_db, row_to_dict
from routes.auth import decode_token

hierarchy_bp = Blueprint("hierarchy", __name__, url_prefix="/api/hierarchy")

MAX_LEVELS = 5


def _utcnow():
    return datetime.datetime.utcnow().isoformat()


def _current_agent(req):
    token = (req.headers.get("Authorization", "") or "").removeprefix("Bearer ")
    return decode_token(token)


def _insert_ledger(db, row):
    db.execute(
        """INSERT INTO commission_ledger
           (ledger_id, policy_id, agent_id, source_agent_id, earning_type,
            hierarchy_level, percentage, amount, visibility_scope, created_at)
           VALUES (:ledger_id, :policy_id, :agent_id, :source_agent_id, :earning_type,
                   :hierarchy_level, :percentage, :amount, :visibility_scope, :created_at)""",
        row,
    )


def _resolve_override_pct(db, product_id, level, fallback_pct):
    """Check commission_rules for product+level override; fall back to hierarchy edge value."""
    today = _utcnow()[:10]
    row = db.execute(
        """SELECT override_percentage FROM commission_rules
           WHERE product_id=? AND hierarchy_level=?
             AND effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
           ORDER BY effective_from DESC LIMIT 1""",
        (product_id, level, today, today),
    ).fetchone()
    return row["override_percentage"] if row else fallback_pct


def compute_and_insert_ledger(db, policy_id, writing_agent_id, product_id, premium, base_rate_percent):
    """BFS upward from writing_agent_id, inserting BASE + OVERRIDE ledger rows."""
    if not writing_agent_id:
        return
    premium_d = Decimal(str(premium))
    now = _utcnow()

    # BASE entry for writing agent
    base_amount = (premium_d * Decimal(str(base_rate_percent)) / 100).quantize(
        Decimal("0.0001"), ROUND_HALF_UP
    )
    _insert_ledger(
        db,
        {
            "ledger_id": str(uuid4()),
            "policy_id": policy_id,
            "agent_id": writing_agent_id,
            "source_agent_id": writing_agent_id,
            "earning_type": "BASE",
            "hierarchy_level": 0,
            "percentage": base_rate_percent,
            "amount": float(base_amount),
            "visibility_scope": "SELF",
            "created_at": now,
        },
    )

    # BFS upward through agent_hierarchy
    visited = {writing_agent_id}
    frontier = [(writing_agent_id, 0)]
    while frontier:
        current, depth = frontier.pop(0)
        if depth >= MAX_LEVELS:
            continue
        rows = db.execute(
            "SELECT upline_agent_id, override_percentage FROM agent_hierarchy "
            "WHERE downline_agent_id=? AND is_active=1",
            [current],
        ).fetchall()
        for row in rows:
            upline = row["upline_agent_id"]
            if upline in visited:
                continue
            visited.add(upline)
            pct = _resolve_override_pct(db, product_id, depth + 1, row["override_percentage"])
            amount = (premium_d * Decimal(str(pct)) / 100).quantize(
                Decimal("0.0001"), ROUND_HALF_UP
            )
            _insert_ledger(
                db,
                {
                    "ledger_id": str(uuid4()),
                    "policy_id": policy_id,
                    "agent_id": upline,
                    "source_agent_id": writing_agent_id,
                    "earning_type": "OVERRIDE",
                    "hierarchy_level": depth + 1,
                    "percentage": float(pct),
                    "amount": float(amount),
                    "visibility_scope": "DOWNLINE",
                    "created_at": now,
                },
            )
            frontier.append((upline, depth + 1))


def get_visible_agent_ids(viewer_id: str, db) -> list:
    """Returns viewer + all direct/indirect downlines they may see."""
    rows = db.execute(
        """
        WITH RECURSIVE downline_tree(agent_id) AS (
            SELECT downline_agent_id FROM agent_hierarchy
            WHERE upline_agent_id=? AND is_active=1
            UNION ALL
            SELECT ah.downline_agent_id FROM agent_hierarchy ah
            JOIN downline_tree dt ON ah.upline_agent_id=dt.agent_id
            WHERE ah.is_active=1
        )
        SELECT agent_id FROM downline_tree
        """,
        [viewer_id],
    ).fetchall()
    return [viewer_id] + [r["agent_id"] for r in rows]


# ── Routes ────────────────────────────────────────────────────────────────────


@hierarchy_bp.route("/graph", methods=["GET"])
def get_graph():
    caller = _current_agent(request)
    db = get_db()

    # All agents (active)
    agents = [row_to_dict(r) for r in db.execute(
        "SELECT agent_id, name, role FROM agents WHERE is_active=1"
    ).fetchall()]

    is_admin = caller and caller.get("role") == "admin"
    viewer_id = caller["agent_id"] if caller else None

    visible_ids = None
    if not is_admin and viewer_id:
        visible_ids = get_visible_agent_ids(viewer_id, db)

    # Build nodes with optional earnings
    nodes = []
    for a in agents:
        node = {
            "agent_id": a["agent_id"],
            "name": a["name"],
            "role": a["role"],
            "earnings_visible": is_admin or (visible_ids is not None and a["agent_id"] in visible_ids),
        }
        if node["earnings_visible"]:
            row = db.execute(
                "SELECT COALESCE(SUM(amount),0) AS total FROM commission_ledger WHERE agent_id=?",
                [a["agent_id"]],
            ).fetchone()
            node["total_earnings"] = round(row["total"], 2) if row else 0.0
        nodes.append(node)

    # All active edges
    edges = [row_to_dict(r) for r in db.execute(
        "SELECT id, upline_agent_id, downline_agent_id, override_percentage, hierarchy_level "
        "FROM agent_hierarchy WHERE is_active=1"
    ).fetchall()]

    db.close()
    return jsonify({"nodes": nodes, "edges": edges})


@hierarchy_bp.route("/agent/<agent_id>", methods=["GET"])
def get_agent_hierarchy(agent_id):
    db = get_db()
    uplines = [row_to_dict(r) for r in db.execute(
        """SELECT ah.id, ah.upline_agent_id, a.name AS upline_name,
                  ah.override_percentage, ah.hierarchy_level
           FROM agent_hierarchy ah
           JOIN agents a ON a.agent_id=ah.upline_agent_id
           WHERE ah.downline_agent_id=? AND ah.is_active=1""",
        [agent_id],
    ).fetchall()]
    downlines = [row_to_dict(r) for r in db.execute(
        """SELECT ah.id, ah.downline_agent_id, a.name AS downline_name,
                  ah.override_percentage, ah.hierarchy_level
           FROM agent_hierarchy ah
           JOIN agents a ON a.agent_id=ah.downline_agent_id
           WHERE ah.upline_agent_id=? AND ah.is_active=1""",
        [agent_id],
    ).fetchall()]
    db.close()
    return jsonify({"uplines": uplines, "downlines": downlines})


@hierarchy_bp.route("/link", methods=["POST"])
def create_link():
    caller = _current_agent(request)
    if not caller or caller.get("role") != "admin":
        return jsonify({"error": "Admin required"}), 403

    data = request.get_json() or {}
    upline = data.get("upline_agent_id")
    downline = data.get("downline_agent_id")
    pct = data.get("override_percentage", 0.0)
    level = data.get("hierarchy_level", 1)

    if not upline or not downline:
        return jsonify({"error": "upline_agent_id and downline_agent_id required"}), 400
    if upline == downline:
        return jsonify({"error": "Self-reference not allowed"}), 400

    db = get_db()

    # Cycle check: would adding upline→downline create a cycle?
    # Check if upline is already reachable FROM downline (i.e., upline is a downline of downline)
    descendants = get_visible_agent_ids(downline, db)  # downline's own downlines
    if upline in descendants:
        db.close()
        return jsonify({"error": "This link would create a cycle"}), 400

    try:
        db.execute(
            "INSERT INTO agent_hierarchy (upline_agent_id, downline_agent_id, override_percentage, hierarchy_level, is_active, created_at) "
            "VALUES (?,?,?,?,1,?)",
            (upline, downline, pct, level, _utcnow()),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM agent_hierarchy WHERE upline_agent_id=? AND downline_agent_id=?",
            (upline, downline),
        ).fetchone()
        db.close()
        return jsonify(row_to_dict(row)), 201
    except Exception as e:
        db.close()
        if "UNIQUE" in str(e):
            return jsonify({"error": "Link already exists"}), 409
        return jsonify({"error": str(e)}), 400


@hierarchy_bp.route("/link/<int:link_id>", methods=["DELETE"])
def delete_link(link_id):
    caller = _current_agent(request)
    if not caller or caller.get("role") != "admin":
        return jsonify({"error": "Admin required"}), 403

    db = get_db()
    db.execute(
        "UPDATE agent_hierarchy SET is_active=0 WHERE id=?", [link_id]
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@hierarchy_bp.route("/commissions", methods=["GET"])
def get_ledger():
    caller = _current_agent(request)
    if not caller:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    is_admin = caller.get("role") == "admin"

    if is_admin:
        visible_ids = None  # unrestricted
    else:
        visible_ids = get_visible_agent_ids(caller["agent_id"], db)

    params = []
    where_clauses = []

    if visible_ids is not None:
        placeholders = ",".join("?" * len(visible_ids))
        where_clauses.append(f"cl.agent_id IN ({placeholders})")
        params.extend(visible_ids)

    agent_filter = request.args.get("agent_id")
    if agent_filter:
        where_clauses.append("cl.agent_id=?")
        params.append(agent_filter)

    policy_filter = request.args.get("policy_id")
    if policy_filter:
        where_clauses.append("cl.policy_id=?")
        params.append(policy_filter)

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = db.execute(
        f"""SELECT cl.*, a.name AS agent_name, sa.name AS source_agent_name,
                   p.client_id, c.name AS client_name
            FROM commission_ledger cl
            JOIN agents a  ON a.agent_id=cl.agent_id
            JOIN agents sa ON sa.agent_id=cl.source_agent_id
            JOIN policies p ON p.policy_id=cl.policy_id
            JOIN clients c  ON c.client_id=p.client_id
            {where}
            ORDER BY cl.created_at DESC""",
        params,
    ).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


@hierarchy_bp.route("/commissions/flow/<policy_id>", methods=["GET"])
def get_ledger_flow(policy_id):
    caller = _current_agent(request)
    if not caller:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    is_admin = caller.get("role") == "admin"
    visible_ids = None if is_admin else get_visible_agent_ids(caller["agent_id"], db)

    rows = db.execute(
        """SELECT cl.ledger_id, cl.agent_id, a.name AS agent_name,
                  cl.earning_type, cl.hierarchy_level, cl.percentage,
                  cl.amount, cl.visibility_scope, cl.source_agent_id
           FROM commission_ledger cl
           JOIN agents a ON a.agent_id=cl.agent_id
           WHERE cl.policy_id=?
           ORDER BY cl.hierarchy_level ASC""",
        [policy_id],
    ).fetchall()
    db.close()

    flow = []
    for r in rows:
        item = {
            "ledger_id": r["ledger_id"],
            "agent_id": r["agent_id"],
            "agent_name": r["agent_name"],
            "earning_type": r["earning_type"],
            "hierarchy_level": r["hierarchy_level"],
            "percentage": r["percentage"],
            "visibility_scope": r["visibility_scope"],
        }
        # Only include amount if caller can see it
        if visible_ids is None or r["agent_id"] in visible_ids:
            item["amount"] = r["amount"]
        flow.append(item)

    return jsonify(flow)


@hierarchy_bp.route("/commissions/summary", methods=["GET"])
def get_ledger_summary():
    caller = _current_agent(request)
    if not caller:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    is_admin = caller.get("role") == "admin"
    viewer_id = caller["agent_id"]

    if is_admin:
        base_total = db.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM commission_ledger WHERE earning_type='BASE'"
        ).fetchone()["t"]
        override_total = db.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM commission_ledger WHERE earning_type='OVERRIDE'"
        ).fetchone()["t"]
    else:
        base_total = db.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM commission_ledger WHERE earning_type='BASE' AND agent_id=?",
            [viewer_id],
        ).fetchone()["t"]
        override_total = db.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM commission_ledger WHERE earning_type='OVERRIDE' AND agent_id=?",
            [viewer_id],
        ).fetchone()["t"]

    db.close()
    return jsonify({
        "base_total": round(base_total, 2),
        "override_total": round(override_total, 2),
        "grand_total": round(base_total + override_total, 2),
    })
