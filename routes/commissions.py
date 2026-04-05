"""
routes/commissions.py
---------------------
Commission read-only access + summary KPIs.
Commissions are auto-created by the policy transition endpoint on Issued.

Endpoints:
    GET    /api/commissions             list; ?event_type=&client_id=&policy_id=&agent_id=
    GET    /api/commissions/summary     KPI totals {total, sale_total, renewal_total, count}
    GET    /api/commissions/<id>        detail
"""

from flask import Blueprint, jsonify, request

from database import get_db, row_to_dict

commissions_bp = Blueprint("commissions", __name__)


# ---------------------------------------------------------------------------
# GET /api/commissions/summary  (must be before /<id> to avoid routing clash)
# ---------------------------------------------------------------------------
@commissions_bp.route("/commissions/summary", methods=["GET"])
def commission_summary():
    db = get_db()
    row = db.execute("""
        SELECT
            COALESCE(SUM(amount), 0)                                         AS total,
            COALESCE(SUM(CASE WHEN event_type='sale'    THEN amount END), 0) AS sale_total,
            COALESCE(SUM(CASE WHEN event_type='renewal' THEN amount END), 0) AS renewal_total,
            COUNT(*)                                                          AS count
        FROM commissions
    """).fetchone()
    db.close()
    return jsonify(dict(row))


# ---------------------------------------------------------------------------
# GET /api/commissions
# ---------------------------------------------------------------------------
@commissions_bp.route("/commissions", methods=["GET"])
def list_commissions():
    event_type = request.args.get("event_type")
    client_id = request.args.get("client_id")
    policy_id = request.args.get("policy_id")
    agent_id = request.args.get("agent_id")

    query = """
        SELECT cm.*, c.name AS client_name, pr.name AS product_name
        FROM commissions cm
        JOIN clients c ON cm.client_id = c.client_id
        JOIN products pr ON cm.product_id = pr.product_id
        WHERE 1=1
    """
    params: list = []

    if event_type:
        query += " AND cm.event_type = ?"
        params.append(event_type)
    if client_id:
        query += " AND cm.client_id = ?"
        params.append(client_id)
    if policy_id:
        query += " AND cm.policy_id = ?"
        params.append(policy_id)
    if agent_id:
        query += " AND cm.agent_id = ?"
        params.append(agent_id)

    query += " ORDER BY cm.recorded_at DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# ---------------------------------------------------------------------------
# GET /api/commissions/<id>
# ---------------------------------------------------------------------------
@commissions_bp.route("/commissions/<commission_id>", methods=["GET"])
def get_commission(commission_id: str):
    db = get_db()
    row = db.execute("""
        SELECT cm.*, c.name AS client_name, pr.name AS product_name
        FROM commissions cm
        JOIN clients c ON cm.client_id = c.client_id
        JOIN products pr ON cm.product_id = pr.product_id
        WHERE cm.commission_id=?
    """, [commission_id]).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Commission not found"}), 404
    return jsonify(row_to_dict(row))
