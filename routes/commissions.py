"""routes/commissions.py — Commission reads + forecasting."""

import datetime
from flask import Blueprint, jsonify, request
from database import get_db, row_to_dict

commissions_bp = Blueprint("commissions", __name__)


# GET /api/commissions/summary
@commissions_bp.route("/commissions/summary", methods=["GET"])
def commission_summary():
    db = get_db()
    row = db.execute("""
        SELECT
            COALESCE(SUM(amount), 0) AS total,
            COALESCE(SUM(CASE WHEN event_type='sale'    THEN amount END), 0) AS sale_total,
            COALESCE(SUM(CASE WHEN event_type='renewal' THEN amount END), 0) AS renewal_total,
            COUNT(*) AS count
        FROM commissions
    """).fetchone()
    db.close()
    return jsonify(dict(row))


# GET /api/commissions/forecast
@commissions_bp.route("/commissions/forecast", methods=["GET"])
def commission_forecast():
    """Forecast commissions for next 3/6/12 months."""
    db = get_db()
    today = datetime.date.today().isoformat()

    # Pipeline-weighted forecast: each stage has a probability
    stage_prob = {"Lead": 0.05, "Qualified": 0.15, "Proposal": 0.35,
                  "Negotiation": 0.60, "Closed": 1.0}

    pipeline = db.execute("""
        SELECT c.stage, p.premium, pr.commission_rate_percent
        FROM policies p
        JOIN clients c ON p.client_id=c.client_id
        JOIN products pr ON p.product_id=pr.product_id
        WHERE p.status NOT IN ('Issued', 'Rejected', 'Lapsed')
    """).fetchall()

    weighted_pipeline = sum(
        float(r["premium"]) * float(r["commission_rate_percent"]) / 100
        * stage_prob.get(r["stage"], 0.1)
        for r in pipeline
    )

    # Renewal forecast
    def renewal_commission(days):
        future = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
        rows = db.execute("""
            SELECT p.premium, pr.commission_rate_percent
            FROM policies p
            JOIN products pr ON p.product_id=pr.product_id
            WHERE p.status='Issued' AND date(p.renewal_due_at) BETWEEN date(?) AND date(?)
        """, [today, future]).fetchall()
        return sum(float(r["premium"]) * float(r["commission_rate_percent"]) / 100 * 0.85
                   for r in rows)

    # Monthly trend (last 12 months)
    monthly = db.execute("""
        SELECT strftime('%Y-%m', recorded_at) as month, SUM(amount) as total
        FROM commissions
        WHERE recorded_at >= date('now', '-12 months')
        GROUP BY month ORDER BY month
    """).fetchall()

    db.close()

    return jsonify({
        "pipeline_weighted": round(weighted_pipeline, 2),
        "renewal_30_days": round(renewal_commission(30), 2),
        "renewal_60_days": round(renewal_commission(60), 2),
        "renewal_90_days": round(renewal_commission(90), 2),
        "forecast_3_months": round(weighted_pipeline * 0.4 + renewal_commission(90), 2),
        "forecast_6_months": round(weighted_pipeline * 0.7 + renewal_commission(180), 2),
        "monthly_trend": [dict(r) for r in monthly],
    })


# GET /api/commissions
@commissions_bp.route("/commissions", methods=["GET"])
def list_commissions():
    event_type = request.args.get("event_type")
    client_id = request.args.get("client_id")
    policy_id = request.args.get("policy_id")
    agent_id = request.args.get("agent_id")

    query = """
        SELECT cm.*, c.name AS client_name, pr.name AS product_name
        FROM commissions cm
        JOIN clients c ON cm.client_id=c.client_id
        JOIN products pr ON cm.product_id=pr.product_id
        WHERE 1=1
    """
    params: list = []

    if event_type:
        query += " AND cm.event_type=?"
        params.append(event_type)
    if client_id:
        query += " AND cm.client_id=?"
        params.append(client_id)
    if policy_id:
        query += " AND cm.policy_id=?"
        params.append(policy_id)
    if agent_id:
        query += " AND cm.agent_id=?"
        params.append(agent_id)

    query += " ORDER BY cm.recorded_at DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# GET /api/commissions/<id>
@commissions_bp.route("/commissions/<commission_id>", methods=["GET"])
def get_commission(commission_id: str):
    db = get_db()
    row = db.execute("""
        SELECT cm.*, c.name AS client_name, pr.name AS product_name
        FROM commissions cm
        JOIN clients c ON cm.client_id=c.client_id
        JOIN products pr ON cm.product_id=pr.product_id
        WHERE cm.commission_id=?
    """, [commission_id]).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Commission not found"}), 404
    return jsonify(row_to_dict(row))
