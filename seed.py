"""
seed.py
-------
Populates the Insurance Agent Portal database with realistic test data.

Run once after database.py:
    python database.py
    python seed.py

Idempotent: skips if clients table already has rows.
"""

import sqlite3
import uuid
import json
from datetime import datetime, timezone, timedelta

from database import DB_PATH, init_db


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def days_from_now(n: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=n)).isoformat()


def seed() -> None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    # Idempotency check
    count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    if count > 0:
        print(f"Database already seeded ({count} clients found). Skipping.")
        conn.close()
        return

    now = utcnow()

    # ---------------------------------------------------------------
    # PRODUCTS (5)
    # ---------------------------------------------------------------
    products = [
        {
            "product_id": "prod-001",
            "name": "Term Life Shield",
            "description": "Pure term insurance providing high coverage at low premiums. Ideal for income replacement.",
            "min_premium": 8000.0,
            "max_premium": 50000.0,
            "min_age": 18,
            "max_age": 60,
            "min_income": 200000.0,
            "commission_rate_percent": 10.0,
            "is_active": 1,
            "created_at": now,
        },
        {
            "product_id": "prod-002",
            "name": "Health Guard Plus",
            "description": "Comprehensive health insurance covering hospitalisation, surgery, and critical illness.",
            "min_premium": 5000.0,
            "max_premium": 35000.0,
            "min_age": 18,
            "max_age": 65,
            "min_income": 150000.0,
            "commission_rate_percent": 8.0,
            "is_active": 1,
            "created_at": now,
        },
        {
            "product_id": "prod-003",
            "name": "Wealth Builder ULIP",
            "description": "Unit-linked insurance plan combining market-linked investments with life coverage.",
            "min_premium": 25000.0,
            "max_premium": 200000.0,
            "min_age": 25,
            "max_age": 55,
            "min_income": 600000.0,
            "commission_rate_percent": 12.0,
            "is_active": 1,
            "created_at": now,
        },
        {
            "product_id": "prod-004",
            "name": "Motor Comprehensive",
            "description": "Full motor vehicle insurance covering own damage, third-party liability, and theft.",
            "min_premium": 3000.0,
            "max_premium": 25000.0,
            "min_age": 18,
            "max_age": 70,
            "min_income": 0.0,
            "commission_rate_percent": 6.0,
            "is_active": 1,
            "created_at": now,
        },
        {
            "product_id": "prod-005",
            "name": "Critical Illness Rider",
            "description": "Lump-sum payout on diagnosis of 36 critical illnesses including cancer and heart attack.",
            "min_premium": 4000.0,
            "max_premium": 20000.0,
            "min_age": 18,
            "max_age": 55,
            "min_income": 100000.0,
            "commission_rate_percent": 9.0,
            "is_active": 1,
            "created_at": now,
        },
    ]

    conn.executemany("""
        INSERT INTO products
          (product_id, name, description, min_premium, max_premium,
           min_age, max_age, min_income, commission_rate_percent, is_active, created_at)
        VALUES
          (:product_id, :name, :description, :min_premium, :max_premium,
           :min_age, :max_age, :min_income, :commission_rate_percent, :is_active, :created_at)
    """, products)

    # ---------------------------------------------------------------
    # CLIENTS (10) — mix of pipeline stages
    # ---------------------------------------------------------------
    clients = [
        # 2 × Lead
        {
            "client_id": "cli-001", "name": "Aarav Mehta", "phone": "9876500001",
            "email": "aarav.mehta@email.com", "age": 28, "income": None,
            "dependents": 0, "risk_appetite": "moderate", "stage": "Lead",
            "is_active": 1, "created_at": days_ago(30), "updated_at": days_ago(30),
        },
        {
            "client_id": "cli-002", "name": "Priya Nair", "phone": "9876500002",
            "email": "priya.nair@email.com", "age": 35, "income": None,
            "dependents": 2, "risk_appetite": "low", "stage": "Lead",
            "is_active": 1, "created_at": days_ago(25), "updated_at": days_ago(25),
        },
        # 2 × Qualified
        {
            "client_id": "cli-003", "name": "Rohan Sharma", "phone": "9876500003",
            "email": "rohan.sharma@email.com", "age": 42, "income": 850000.0,
            "dependents": 3, "risk_appetite": "moderate", "stage": "Qualified",
            "is_active": 1, "created_at": days_ago(20), "updated_at": days_ago(18),
        },
        {
            "client_id": "cli-004", "name": "Ananya Rao", "phone": "9876500004",
            "email": "ananya.rao@email.com", "age": 31, "income": 480000.0,
            "dependents": 1, "risk_appetite": "moderate", "stage": "Qualified",
            "is_active": 1, "created_at": days_ago(18), "updated_at": days_ago(15),
        },
        # 2 × Proposal
        {
            "client_id": "cli-005", "name": "Vikram Singh", "phone": "9876500005",
            "email": "vikram.singh@email.com", "age": 48, "income": 1200000.0,
            "dependents": 2, "risk_appetite": "high", "stage": "Proposal",
            "is_active": 1, "created_at": days_ago(15), "updated_at": days_ago(10),
        },
        {
            "client_id": "cli-006", "name": "Meera Iyer", "phone": "9876500006",
            "email": "meera.iyer@email.com", "age": 38, "income": 650000.0,
            "dependents": 2, "risk_appetite": "moderate", "stage": "Proposal",
            "is_active": 1, "created_at": days_ago(12), "updated_at": days_ago(8),
        },
        # 2 × Negotiation
        {
            "client_id": "cli-007", "name": "Arjun Kapoor", "phone": "9876500007",
            "email": "arjun.kapoor@email.com", "age": 45, "income": 950000.0,
            "dependents": 3, "risk_appetite": "moderate", "stage": "Negotiation",
            "is_active": 1, "created_at": days_ago(10), "updated_at": days_ago(5),
        },
        {
            "client_id": "cli-008", "name": "Sunita Patel", "phone": "9876500008",
            "email": "sunita.patel@email.com", "age": 52, "income": 720000.0,
            "dependents": 1, "risk_appetite": "low", "stage": "Negotiation",
            "is_active": 1, "created_at": days_ago(8), "updated_at": days_ago(3),
        },
        # 2 × Closed
        {
            "client_id": "cli-009", "name": "Deepak Joshi", "phone": "9876500009",
            "email": "deepak.joshi@email.com", "age": 37, "income": 580000.0,
            "dependents": 2, "risk_appetite": "moderate", "stage": "Closed",
            "is_active": 1, "created_at": days_ago(60), "updated_at": days_ago(40),
        },
        {
            "client_id": "cli-010", "name": "Kavya Reddy", "phone": "9876500010",
            "email": "kavya.reddy@email.com", "age": 29, "income": 380000.0,
            "dependents": 0, "risk_appetite": "high", "stage": "Closed",
            "is_active": 1, "created_at": days_ago(90), "updated_at": days_ago(70),
        },
    ]

    conn.executemany("""
        INSERT INTO clients
          (client_id, name, phone, email, age, income, dependents,
           risk_appetite, stage, is_active, created_at, updated_at)
        VALUES
          (:client_id, :name, :phone, :email, :age, :income, :dependents,
           :risk_appetite, :stage, :is_active, :created_at, :updated_at)
    """, clients)

    # ---------------------------------------------------------------
    # POLICIES (9) — one per status bucket
    # ---------------------------------------------------------------
    default_docs = json.dumps(["ID Proof", "Income Proof", "Medical Report", "Signed Proposal Form"])

    policies = [
        # Draft — cli-007 (Negotiation)
        {
            "policy_id": "pol-001", "client_id": "cli-007", "product_id": "prod-001",
            "premium": 18000.0, "status": "Draft",
            "documents_checklist": default_docs, "documents_attached": "[]",
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(5), "updated_at": days_ago(5),
        },
        # Submitted — cli-008 (Negotiation)
        {
            "policy_id": "pol-002", "client_id": "cli-008", "product_id": "prod-002",
            "premium": 12000.0, "status": "Submitted",
            "documents_checklist": default_docs,
            "documents_attached": json.dumps(["ID Proof", "Income Proof"]),
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(7), "updated_at": days_ago(4),
        },
        # Underwriting — cli-005 (Proposal)
        {
            "policy_id": "pol-003", "client_id": "cli-005", "product_id": "prod-003",
            "premium": 60000.0, "status": "Underwriting",
            "documents_checklist": default_docs,
            "documents_attached": json.dumps(["ID Proof", "Income Proof", "Medical Report"]),
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(10), "updated_at": days_ago(6),
        },
        # Approved — cli-006 (Proposal)
        {
            "policy_id": "pol-004", "client_id": "cli-006", "product_id": "prod-001",
            "premium": 22000.0, "status": "Approved",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(12), "updated_at": days_ago(3),
        },
        # Issued #1 — cli-009 (Closed)
        {
            "policy_id": "pol-005", "client_id": "cli-009", "product_id": "prod-001",
            "premium": 15000.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(40), "renewal_due_at": days_from_now(325),
            "created_at": days_ago(60), "updated_at": days_ago(40),
        },
        # Issued #2 — cli-010 (Closed)
        {
            "policy_id": "pol-006", "client_id": "cli-010", "product_id": "prod-002",
            "premium": 8500.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(70), "renewal_due_at": days_from_now(295),
            "created_at": days_ago(90), "updated_at": days_ago(70),
        },
        # Issued #3 — cli-009 (second policy)
        {
            "policy_id": "pol-007", "client_id": "cli-009", "product_id": "prod-005",
            "premium": 6000.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(35), "renewal_due_at": days_from_now(330),
            "created_at": days_ago(55), "updated_at": days_ago(35),
        },
        # Rejected — cli-003 (Qualified, rolled back)
        {
            "policy_id": "pol-008", "client_id": "cli-003", "product_id": "prod-003",
            "premium": 75000.0, "status": "Rejected",
            "documents_checklist": default_docs,
            "documents_attached": json.dumps(["ID Proof", "Income Proof"]),
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(25), "updated_at": days_ago(18),
        },
        # Lapsed — cli-010 (second policy, renewal overdue)
        {
            "policy_id": "pol-009", "client_id": "cli-010", "product_id": "prod-004",
            "premium": 4500.0, "status": "Lapsed",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(395), "renewal_due_at": days_ago(30),
            "created_at": days_ago(400), "updated_at": days_ago(28),
        },
    ]

    conn.executemany("""
        INSERT INTO policies
          (policy_id, client_id, product_id, premium, status,
           documents_checklist, documents_attached,
           issued_at, renewal_due_at, created_at, updated_at)
        VALUES
          (:policy_id, :client_id, :product_id, :premium, :status,
           :documents_checklist, :documents_attached,
           :issued_at, :renewal_due_at, :created_at, :updated_at)
    """, policies)

    # Policy status history rows (simplified — terminal status only)
    status_history = [
        ("pol-001", None, "Draft", days_ago(5)),
        ("pol-002", None, "Draft", days_ago(7)),
        ("pol-002", "Draft", "Submitted", days_ago(4)),
        ("pol-003", None, "Draft", days_ago(10)),
        ("pol-003", "Draft", "Submitted", days_ago(9)),
        ("pol-003", "Submitted", "Underwriting", days_ago(6)),
        ("pol-004", None, "Draft", days_ago(12)),
        ("pol-004", "Draft", "Submitted", days_ago(11)),
        ("pol-004", "Submitted", "Underwriting", days_ago(9)),
        ("pol-004", "Underwriting", "Approved", days_ago(3)),
        ("pol-005", None, "Draft", days_ago(60)),
        ("pol-005", "Draft", "Submitted", days_ago(58)),
        ("pol-005", "Submitted", "Underwriting", days_ago(55)),
        ("pol-005", "Underwriting", "Approved", days_ago(50)),
        ("pol-005", "Approved", "Issued", days_ago(40)),
        ("pol-006", None, "Draft", days_ago(90)),
        ("pol-006", "Draft", "Submitted", days_ago(88)),
        ("pol-006", "Submitted", "Underwriting", days_ago(85)),
        ("pol-006", "Underwriting", "Approved", days_ago(80)),
        ("pol-006", "Approved", "Issued", days_ago(70)),
        ("pol-007", None, "Draft", days_ago(55)),
        ("pol-007", "Draft", "Submitted", days_ago(53)),
        ("pol-007", "Submitted", "Underwriting", days_ago(50)),
        ("pol-007", "Underwriting", "Approved", days_ago(45)),
        ("pol-007", "Approved", "Issued", days_ago(35)),
        ("pol-008", None, "Draft", days_ago(25)),
        ("pol-008", "Draft", "Submitted", days_ago(23)),
        ("pol-008", "Submitted", "Underwriting", days_ago(20)),
        ("pol-008", "Underwriting", "Rejected", days_ago(18)),
        ("pol-009", None, "Draft", days_ago(400)),
        ("pol-009", "Draft", "Submitted", days_ago(398)),
        ("pol-009", "Submitted", "Underwriting", days_ago(396)),
        ("pol-009", "Underwriting", "Approved", days_ago(393)),
        ("pol-009", "Approved", "Issued", days_ago(395)),
        ("pol-009", "Issued", "Lapsed", days_ago(28)),
    ]

    conn.executemany("""
        INSERT INTO policy_status_history (policy_id, from_status, to_status, changed_at)
        VALUES (?, ?, ?, ?)
    """, status_history)

    # ---------------------------------------------------------------
    # COMMISSIONS — for Issued and Lapsed policies
    # ---------------------------------------------------------------
    def make_commission(policy_id, product_id, client_id, premium, rate, event_type, recorded_at, agent_id="AGENT-001"):
        return {
            "commission_id": str(uuid.uuid4()),
            "policy_id": policy_id,
            "product_id": product_id,
            "client_id": client_id,
            "event_type": event_type,
            "amount": round(premium * rate / 100, 2),
            "rate_percent": rate,
            "premium": premium,
            "agent_id": agent_id,
            "recorded_at": recorded_at,
        }

    commissions = [
        # pol-005 (Issued, Term Life Shield 10%)
        make_commission("pol-005", "prod-001", "cli-009", 15000.0, 10.0, "sale", days_ago(40)),
        make_commission("pol-005", "prod-001", "cli-009", 15000.0, 10.0, "renewal", days_ago(5)),
        # pol-006 (Issued, Health Guard Plus 8%)
        make_commission("pol-006", "prod-002", "cli-010", 8500.0, 8.0, "sale", days_ago(70)),
        make_commission("pol-006", "prod-002", "cli-010", 8500.0, 8.0, "renewal", days_ago(10)),
        # pol-007 (Issued, Critical Illness Rider 9%)
        make_commission("pol-007", "prod-005", "cli-009", 6000.0, 9.0, "sale", days_ago(35)),
        # pol-009 (Lapsed, Motor Comprehensive 6%)
        make_commission("pol-009", "prod-004", "cli-010", 4500.0, 6.0, "sale", days_ago(395)),
        make_commission("pol-009", "prod-004", "cli-010", 4500.0, 6.0, "renewal", days_ago(30)),
    ]

    conn.executemany("""
        INSERT INTO commissions
          (commission_id, policy_id, product_id, client_id, event_type,
           amount, rate_percent, premium, agent_id, recorded_at)
        VALUES
          (:commission_id, :policy_id, :product_id, :client_id, :event_type,
           :amount, :rate_percent, :premium, :agent_id, :recorded_at)
    """, commissions)

    # ---------------------------------------------------------------
    # ACTIVITIES (25+)
    # ---------------------------------------------------------------
    def act(client_id, activity_type, description, policy_id=None, ts=None):
        return {
            "activity_id": str(uuid.uuid4()),
            "client_id": client_id,
            "policy_id": policy_id,
            "activity_type": activity_type,
            "description": description,
            "metadata": "{}",
            "timestamp": ts or utcnow(),
        }

    activities = [
        # Lead activities
        act("cli-001", "note", "New lead added from referral. Needs follow-up for financial profiling.", ts=days_ago(30)),
        act("cli-002", "call", "First call made. Client interested in health insurance. Awaiting income details.", ts=days_ago(25)),
        # Qualified activities
        act("cli-003", "note", "Client qualified. Annual income ₹8,50,000. 3 dependents.", ts=days_ago(20)),
        act("cli-004", "follow_up", "Needs assessment complete. Shortlisted Health Guard Plus.", ts=days_ago(15)),
        # Proposal activities
        act("cli-005", "meeting", "Proposal meeting held. Client keen on ULIP for wealth creation.", ts=days_ago(10)),
        act("cli-006", "follow_up", "Sent Term Life Shield proposal. Client reviewing.", ts=days_ago(8)),
        # Negotiation activities
        act("cli-007", "policy_created", "Policy pol-001 created for Term Life Shield. Status: Draft.", "pol-001", ts=days_ago(5)),
        act("cli-008", "policy_created", "Policy pol-002 created for Health Guard Plus. Status: Draft.", "pol-002", ts=days_ago(7)),
        act("cli-008", "status_change", "Policy pol-002 moved from Draft to Submitted.", "pol-002", ts=days_ago(4)),
        act("cli-005", "policy_created", "Policy pol-003 created for Wealth Builder ULIP. Status: Draft.", "pol-003", ts=days_ago(10)),
        act("cli-005", "status_change", "Policy pol-003 moved from Draft to Submitted.", "pol-003", ts=days_ago(9)),
        act("cli-005", "status_change", "Policy pol-003 moved from Submitted to Underwriting.", "pol-003", ts=days_ago(6)),
        act("cli-006", "policy_created", "Policy pol-004 created for Term Life Shield. Status: Draft.", "pol-004", ts=days_ago(12)),
        act("cli-006", "status_change", "Policy pol-004 moved from Underwriting to Approved.", "pol-004", ts=days_ago(3)),
        # Closed — cli-009
        act("cli-009", "policy_created", "Policy pol-005 created for Term Life Shield.", "pol-005", ts=days_ago(60)),
        act("cli-009", "status_change", "Policy pol-005 moved from Approved to Issued.", "pol-005", ts=days_ago(40)),
        act("cli-009", "commission_recorded", "Sale commission of ₹1,500.00 recorded for pol-005.", "pol-005", ts=days_ago(40)),
        act("cli-009", "policy_created", "Policy pol-007 created for Critical Illness Rider.", "pol-007", ts=days_ago(55)),
        act("cli-009", "status_change", "Policy pol-007 moved from Approved to Issued.", "pol-007", ts=days_ago(35)),
        act("cli-009", "commission_recorded", "Sale commission of ₹540.00 recorded for pol-007.", "pol-007", ts=days_ago(35)),
        act("cli-009", "commission_recorded", "Renewal commission of ₹1,500.00 recorded for pol-005.", "pol-005", ts=days_ago(5)),
        # Closed — cli-010
        act("cli-010", "policy_created", "Policy pol-006 created for Health Guard Plus.", "pol-006", ts=days_ago(90)),
        act("cli-010", "status_change", "Policy pol-006 moved from Approved to Issued.", "pol-006", ts=days_ago(70)),
        act("cli-010", "commission_recorded", "Sale commission of ₹680.00 recorded for pol-006.", "pol-006", ts=days_ago(70)),
        # Rejected
        act("cli-003", "policy_created", "Policy pol-008 created for Wealth Builder ULIP.", "pol-008", ts=days_ago(25)),
        act("cli-003", "status_change", "Policy pol-008 was Rejected. Review with client for alternatives.", "pol-008", ts=days_ago(18)),
        act("cli-003", "follow_up", "Rejection: underwriting flagged income-to-premium ratio. Consider Term Life Shield instead.", ts=days_ago(18)),
        # Lapsed
        act("cli-010", "status_change", "Policy pol-009 (Motor Comprehensive) has lapsed. Contact client for renewal.", "pol-009", ts=days_ago(28)),
        act("cli-010", "follow_up", "Renewal overdue on pol-009. Schedule call this week.", ts=days_ago(27)),
    ]

    conn.executemany("""
        INSERT INTO activities
          (activity_id, client_id, policy_id, activity_type, description, metadata, timestamp)
        VALUES
          (:activity_id, :client_id, :policy_id, :activity_type, :description, :metadata, :timestamp)
    """, activities)

    conn.commit()
    conn.close()
    print(f"Seed complete: 10 clients, 5 products, 9 policies, {len(commissions)} commissions, {len(activities)} activities.")


if __name__ == "__main__":
    seed()
