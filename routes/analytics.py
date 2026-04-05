"""routes/analytics.py — KPIs, pipeline health, forecasts."""

import datetime
from flask import Blueprint, request, jsonify

from database import get_db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def _today():
    return datetime.date.today().isoformat()

def _month_start():
    d = datetime.date.today()
    return d.replace(day=1).isoformat()

def _year_start():
    return datetime.date.today().replace(month=1, day=1).isoformat()

def _days_from_now(n):
    return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()


@analytics_bp.route("/summary", methods=["GET"])
def summary():
    agent_id = request.args.get("agent_id")
    db = get_db()

    def _filter(base_where):
        if agent_id:
            return base_where + f" AND agent_id='{agent_id}'"
        return base_where

    # Policies issued MTD / YTD
    mtd = db.execute(f"SELECT COUNT(*), COALESCE(SUM(premium),0) FROM policies WHERE status='Issued' AND issued_at>='{_month_start()}'").fetchone()
    ytd = db.execute(f"SELECT COUNT(*), COALESCE(SUM(premium),0) FROM policies WHERE status='Issued' AND issued_at>='{_year_start()}'").fetchone()

    # Commissions
    comm_mtd = db.execute(f"SELECT COALESCE(SUM(amount),0) FROM commissions WHERE recorded_at>='{_month_start()}'").fetchone()[0]
    comm_ytd = db.execute(f"SELECT COALESCE(SUM(amount),0) FROM commissions WHERE recorded_at>='{_year_start()}'").fetchone()[0]

    # Pipeline counts by stage
    stages = db.execute("SELECT stage, COUNT(*) as cnt FROM clients GROUP BY stage").fetchall()
    pipeline = {r["stage"]: r["cnt"] for r in stages}

    # Renewals upcoming
    r30 = db.execute(f"SELECT COUNT(*), COALESCE(SUM(premium),0) FROM policies WHERE status='Issued' AND renewal_due_at BETWEEN '{_today()}' AND '{_days_from_now(30)}'").fetchone()
    r60 = db.execute(f"SELECT COUNT(*), COALESCE(SUM(premium),0) FROM policies WHERE status='Issued' AND renewal_due_at BETWEEN '{_today()}' AND '{_days_from_now(60)}'").fetchone()
    r90 = db.execute(f"SELECT COUNT(*), COALESCE(SUM(premium),0) FROM policies WHERE status='Issued' AND renewal_due_at BETWEEN '{_today()}' AND '{_days_from_now(90)}'").fetchone()

    # Top clients by total premium
    top_clients = db.execute("""
        SELECT c.name, COALESCE(SUM(p.premium),0) as total_premium, COUNT(p.policy_id) as policy_count
        FROM clients c
        LEFT JOIN policies p ON p.client_id=c.client_id AND p.status='Issued'
        GROUP BY c.client_id ORDER BY total_premium DESC LIMIT 5
    """).fetchall()

    # Activities last 7 days
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    act_counts = db.execute(f"SELECT activity_type, COUNT(*) as cnt FROM activities WHERE timestamp>='{week_ago}' GROUP BY activity_type").fetchall()

    # Monthly commissions (last 12 months)
    monthly = db.execute("""
        SELECT strftime('%Y-%m', recorded_at) as month, SUM(amount) as total
        FROM commissions
        WHERE recorded_at >= date('now', '-12 months')
        GROUP BY month ORDER BY month
    """).fetchall()

    # Pipeline conversion rates
    conversion = db.execute("""
        SELECT
            COUNT(CASE WHEN stage IN ('Proposal','Negotiation','Closed') THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as lead_to_proposal,
            COUNT(CASE WHEN stage = 'Closed' THEN 1 END) * 100.0 / NULLIF(COUNT(CASE WHEN stage IN ('Proposal','Negotiation','Closed') THEN 1 END), 0) as proposal_to_closed
        FROM clients
    """).fetchone()

    # Lead source breakdown
    lead_sources = db.execute("SELECT lead_source, COUNT(*) as cnt FROM clients WHERE lead_source IS NOT NULL GROUP BY lead_source ORDER BY cnt DESC").fetchall()

    db.close()

    return jsonify({
        "policies_mtd": {"count": mtd[0], "premium": mtd[1]},
        "policies_ytd": {"count": ytd[0], "premium": ytd[1]},
        "commissions_mtd": comm_mtd,
        "commissions_ytd": comm_ytd,
        "pipeline": pipeline,
        "renewals": {
            "30_days": {"count": r30[0], "premium": r30[1]},
            "60_days": {"count": r60[0], "premium": r60[1]},
            "90_days": {"count": r90[0], "premium": r90[1]},
        },
        "top_clients": [dict(r) for r in top_clients],
        "activity_breakdown": {r["activity_type"]: r["cnt"] for r in act_counts},
        "monthly_commissions": [dict(r) for r in monthly],
        "conversion": {
            "lead_to_proposal": round(conversion["lead_to_proposal"] or 0, 1),
            "proposal_to_closed": round(conversion["proposal_to_closed"] or 0, 1),
        },
        "lead_sources": [dict(r) for r in lead_sources],
    })
