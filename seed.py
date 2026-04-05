"""
seed.py
-------
Populates the Insurance Agent Portal database with US-market test data.

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

    count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    if count > 0:
        print(f"Database already seeded ({count} clients found). Skipping.")
        conn.close()
        return

    now = utcnow()

    # ---------------------------------------------------------------
    # PRODUCTS (5) — US market
    # ---------------------------------------------------------------
    products = [
        {
            "product_id": "prod-001",
            "name": "Term Life Plus",
            "description": "Pure term life insurance providing high coverage at low premiums. Ideal for income replacement and mortgage protection.",
            "min_premium": 600.0,
            "max_premium": 5000.0,
            "min_age": 18,
            "max_age": 65,
            "min_income": 30000.0,
            "commission_rate_percent": 10.0,
            "is_active": 1,
            "created_at": now,
        },
        {
            "product_id": "prod-002",
            "name": "Health Shield PPO",
            "description": "Comprehensive PPO health plan covering hospitalization, surgery, specialist visits, and prescription drugs.",
            "min_premium": 400.0,
            "max_premium": 3500.0,
            "min_age": 18,
            "max_age": 64,
            "min_income": 25000.0,
            "commission_rate_percent": 8.0,
            "is_active": 1,
            "created_at": now,
        },
        {
            "product_id": "prod-003",
            "name": "Whole Life Advantage",
            "description": "Permanent whole life insurance with guaranteed cash value accumulation and lifelong death benefit.",
            "min_premium": 1800.0,
            "max_premium": 15000.0,
            "min_age": 25,
            "max_age": 60,
            "min_income": 60000.0,
            "commission_rate_percent": 12.0,
            "is_active": 1,
            "created_at": now,
        },
        {
            "product_id": "prod-004",
            "name": "Auto Comprehensive",
            "description": "Full auto insurance covering collision, comprehensive, liability, uninsured motorist, and roadside assistance.",
            "min_premium": 800.0,
            "max_premium": 3000.0,
            "min_age": 18,
            "max_age": 80,
            "min_income": 0.0,
            "commission_rate_percent": 6.0,
            "is_active": 1,
            "created_at": now,
        },
        {
            "product_id": "prod-005",
            "name": "Critical Illness Guard",
            "description": "Lump-sum payout on diagnosis of 30+ critical illnesses including cancer, heart attack, and stroke.",
            "min_premium": 350.0,
            "max_premium": 2000.0,
            "min_age": 18,
            "max_age": 60,
            "min_income": 20000.0,
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
    # CLIENTS (10) — US names, US phone format, USD incomes
    # ---------------------------------------------------------------
    clients = [
        # 2 × Lead
        {
            "client_id": "cli-001", "name": "James Carter", "phone": "(312) 555-0101",
            "email": "james.carter@gmail.com", "age": 29, "income": None,
            "dependents": 0, "risk_appetite": "moderate", "stage": "Lead",
            "is_active": 1, "created_at": days_ago(30), "updated_at": days_ago(30),
        },
        {
            "client_id": "cli-002", "name": "Sarah Mitchell", "phone": "(415) 555-0182",
            "email": "sarah.mitchell@outlook.com", "age": 36, "income": None,
            "dependents": 2, "risk_appetite": "low", "stage": "Lead",
            "is_active": 1, "created_at": days_ago(25), "updated_at": days_ago(25),
        },
        # 2 × Qualified
        {
            "client_id": "cli-003", "name": "Robert Thompson", "phone": "(713) 555-0247",
            "email": "robert.thompson@yahoo.com", "age": 44, "income": 95000.0,
            "dependents": 3, "risk_appetite": "moderate", "stage": "Qualified",
            "is_active": 1, "created_at": days_ago(20), "updated_at": days_ago(18),
        },
        {
            "client_id": "cli-004", "name": "Emily Davis", "phone": "(206) 555-0319",
            "email": "emily.davis@icloud.com", "age": 32, "income": 72000.0,
            "dependents": 1, "risk_appetite": "moderate", "stage": "Qualified",
            "is_active": 1, "created_at": days_ago(18), "updated_at": days_ago(15),
        },
        # 2 × Proposal
        {
            "client_id": "cli-005", "name": "Michael Rodriguez", "phone": "(305) 555-0456",
            "email": "m.rodriguez@gmail.com", "age": 50, "income": 145000.0,
            "dependents": 2, "risk_appetite": "high", "stage": "Proposal",
            "is_active": 1, "created_at": days_ago(15), "updated_at": days_ago(10),
        },
        {
            "client_id": "cli-006", "name": "Jennifer Walsh", "phone": "(617) 555-0523",
            "email": "j.walsh@outlook.com", "age": 39, "income": 88000.0,
            "dependents": 2, "risk_appetite": "moderate", "stage": "Proposal",
            "is_active": 1, "created_at": days_ago(12), "updated_at": days_ago(8),
        },
        # 2 × Negotiation
        {
            "client_id": "cli-007", "name": "David Kim", "phone": "(213) 555-0634",
            "email": "david.kim@gmail.com", "age": 46, "income": 112000.0,
            "dependents": 3, "risk_appetite": "moderate", "stage": "Negotiation",
            "is_active": 1, "created_at": days_ago(10), "updated_at": days_ago(5),
        },
        {
            "client_id": "cli-008", "name": "Patricia Johnson", "phone": "(602) 555-0789",
            "email": "p.johnson@yahoo.com", "age": 53, "income": 67000.0,
            "dependents": 1, "risk_appetite": "low", "stage": "Negotiation",
            "is_active": 1, "created_at": days_ago(8), "updated_at": days_ago(3),
        },
        # 2 × Closed
        {
            "client_id": "cli-009", "name": "Christopher Lee", "phone": "(404) 555-0812",
            "email": "chris.lee@gmail.com", "age": 38, "income": 78000.0,
            "dependents": 2, "risk_appetite": "moderate", "stage": "Closed",
            "is_active": 1, "created_at": days_ago(60), "updated_at": days_ago(40),
        },
        {
            "client_id": "cli-010", "name": "Amanda Foster", "phone": "(503) 555-0965",
            "email": "a.foster@icloud.com", "age": 30, "income": 54000.0,
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
    # POLICIES (13) — including several for the Renewals page
    # ---------------------------------------------------------------
    default_docs = json.dumps(["Government-Issued ID", "Proof of Income", "Medical Exam Report", "Signed Application Form"])

    policies = [
        # Draft — cli-007 (Negotiation)
        {
            "policy_id": "pol-001", "client_id": "cli-007", "product_id": "prod-001",
            "premium": 1200.0, "status": "Draft",
            "documents_checklist": default_docs, "documents_attached": "[]",
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(5), "updated_at": days_ago(5),
        },
        # Submitted — cli-008 (Negotiation)
        {
            "policy_id": "pol-002", "client_id": "cli-008", "product_id": "prod-002",
            "premium": 980.0, "status": "Submitted",
            "documents_checklist": default_docs,
            "documents_attached": json.dumps(["Government-Issued ID", "Proof of Income"]),
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(7), "updated_at": days_ago(4),
        },
        # Underwriting — cli-005 (Proposal)
        {
            "policy_id": "pol-003", "client_id": "cli-005", "product_id": "prod-003",
            "premium": 4200.0, "status": "Underwriting",
            "documents_checklist": default_docs,
            "documents_attached": json.dumps(["Government-Issued ID", "Proof of Income", "Medical Exam Report"]),
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(10), "updated_at": days_ago(6),
        },
        # Approved — cli-006 (Proposal)
        {
            "policy_id": "pol-004", "client_id": "cli-006", "product_id": "prod-001",
            "premium": 1550.0, "status": "Approved",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(12), "updated_at": days_ago(3),
        },
        # Issued #1 — cli-009, renews in 325 days (healthy)
        {
            "policy_id": "pol-005", "client_id": "cli-009", "product_id": "prod-001",
            "premium": 1100.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(40), "renewal_due_at": days_from_now(325),
            "created_at": days_ago(60), "updated_at": days_ago(40),
        },
        # Issued #2 — cli-010, renews in 295 days (healthy)
        {
            "policy_id": "pol-006", "client_id": "cli-010", "product_id": "prod-002",
            "premium": 720.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(70), "renewal_due_at": days_from_now(295),
            "created_at": days_ago(90), "updated_at": days_ago(70),
        },
        # Issued #3 — cli-009 second policy, renews in 330 days (healthy)
        {
            "policy_id": "pol-007", "client_id": "cli-009", "product_id": "prod-005",
            "premium": 480.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(35), "renewal_due_at": days_from_now(330),
            "created_at": days_ago(55), "updated_at": days_ago(35),
        },
        # Rejected — cli-003 (Qualified)
        {
            "policy_id": "pol-008", "client_id": "cli-003", "product_id": "prod-003",
            "premium": 5800.0, "status": "Rejected",
            "documents_checklist": default_docs,
            "documents_attached": json.dumps(["Government-Issued ID", "Proof of Income"]),
            "issued_at": None, "renewal_due_at": None,
            "created_at": days_ago(25), "updated_at": days_ago(18),
        },
        # Lapsed — cli-010, renewal overdue by 30 days
        {
            "policy_id": "pol-009", "client_id": "cli-010", "product_id": "prod-004",
            "premium": 1350.0, "status": "Lapsed",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(395), "renewal_due_at": days_ago(30),
            "created_at": days_ago(400), "updated_at": days_ago(28),
        },
        # --- RENEWALS WINDOW POLICIES ---
        # Issued — cli-004, renews in 18 days (urgent)
        {
            "policy_id": "pol-010", "client_id": "cli-004", "product_id": "prod-002",
            "premium": 860.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(347), "renewal_due_at": days_from_now(18),
            "created_at": days_ago(350), "updated_at": days_ago(347),
        },
        # Issued — cli-003, renews in 45 days (upcoming)
        {
            "policy_id": "pol-011", "client_id": "cli-003", "product_id": "prod-001",
            "premium": 1400.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(320), "renewal_due_at": days_from_now(45),
            "created_at": days_ago(325), "updated_at": days_ago(320),
        },
        # Issued — cli-006, renews in 72 days (upcoming)
        {
            "policy_id": "pol-012", "client_id": "cli-006", "product_id": "prod-005",
            "premium": 620.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(293), "renewal_due_at": days_from_now(72),
            "created_at": days_ago(298), "updated_at": days_ago(293),
        },
        # Issued — cli-007, renewal overdue by 5 days (past due)
        {
            "policy_id": "pol-013", "client_id": "cli-007", "product_id": "prod-004",
            "premium": 1680.0, "status": "Issued",
            "documents_checklist": default_docs, "documents_attached": default_docs,
            "issued_at": days_ago(370), "renewal_due_at": days_ago(5),
            "created_at": days_ago(375), "updated_at": days_ago(370),
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

    # Policy status history
    status_history = [
        ("pol-001", None,           "Draft",        days_ago(5)),
        ("pol-002", None,           "Draft",        days_ago(7)),
        ("pol-002", "Draft",        "Submitted",    days_ago(4)),
        ("pol-003", None,           "Draft",        days_ago(10)),
        ("pol-003", "Draft",        "Submitted",    days_ago(9)),
        ("pol-003", "Submitted",    "Underwriting", days_ago(6)),
        ("pol-004", None,           "Draft",        days_ago(12)),
        ("pol-004", "Draft",        "Submitted",    days_ago(11)),
        ("pol-004", "Submitted",    "Underwriting", days_ago(9)),
        ("pol-004", "Underwriting", "Approved",     days_ago(3)),
        ("pol-005", None,           "Draft",        days_ago(60)),
        ("pol-005", "Draft",        "Submitted",    days_ago(58)),
        ("pol-005", "Submitted",    "Underwriting", days_ago(55)),
        ("pol-005", "Underwriting", "Approved",     days_ago(50)),
        ("pol-005", "Approved",     "Issued",       days_ago(40)),
        ("pol-006", None,           "Draft",        days_ago(90)),
        ("pol-006", "Draft",        "Submitted",    days_ago(88)),
        ("pol-006", "Submitted",    "Underwriting", days_ago(85)),
        ("pol-006", "Underwriting", "Approved",     days_ago(80)),
        ("pol-006", "Approved",     "Issued",       days_ago(70)),
        ("pol-007", None,           "Draft",        days_ago(55)),
        ("pol-007", "Draft",        "Submitted",    days_ago(53)),
        ("pol-007", "Submitted",    "Underwriting", days_ago(50)),
        ("pol-007", "Underwriting", "Approved",     days_ago(45)),
        ("pol-007", "Approved",     "Issued",       days_ago(35)),
        ("pol-008", None,           "Draft",        days_ago(25)),
        ("pol-008", "Draft",        "Submitted",    days_ago(23)),
        ("pol-008", "Submitted",    "Underwriting", days_ago(20)),
        ("pol-008", "Underwriting", "Rejected",     days_ago(18)),
        ("pol-009", None,           "Draft",        days_ago(400)),
        ("pol-009", "Draft",        "Submitted",    days_ago(398)),
        ("pol-009", "Submitted",    "Underwriting", days_ago(396)),
        ("pol-009", "Underwriting", "Approved",     days_ago(393)),
        ("pol-009", "Approved",     "Issued",       days_ago(395)),
        ("pol-009", "Issued",       "Lapsed",       days_ago(28)),
        ("pol-010", None,           "Draft",        days_ago(350)),
        ("pol-010", "Draft",        "Submitted",    days_ago(348)),
        ("pol-010", "Submitted",    "Underwriting", days_ago(346)),
        ("pol-010", "Underwriting", "Approved",     days_ago(349)),
        ("pol-010", "Approved",     "Issued",       days_ago(347)),
        ("pol-011", None,           "Draft",        days_ago(325)),
        ("pol-011", "Draft",        "Submitted",    days_ago(323)),
        ("pol-011", "Submitted",    "Underwriting", days_ago(321)),
        ("pol-011", "Underwriting", "Approved",     days_ago(322)),
        ("pol-011", "Approved",     "Issued",       days_ago(320)),
        ("pol-012", None,           "Draft",        days_ago(298)),
        ("pol-012", "Draft",        "Submitted",    days_ago(296)),
        ("pol-012", "Submitted",    "Underwriting", days_ago(295)),
        ("pol-012", "Underwriting", "Approved",     days_ago(294)),
        ("pol-012", "Approved",     "Issued",       days_ago(293)),
        ("pol-013", None,           "Draft",        days_ago(375)),
        ("pol-013", "Draft",        "Submitted",    days_ago(373)),
        ("pol-013", "Submitted",    "Underwriting", days_ago(372)),
        ("pol-013", "Underwriting", "Approved",     days_ago(371)),
        ("pol-013", "Approved",     "Issued",       days_ago(370)),
    ]

    conn.executemany("""
        INSERT INTO policy_status_history (policy_id, from_status, to_status, changed_at)
        VALUES (?, ?, ?, ?)
    """, status_history)

    # ---------------------------------------------------------------
    # COMMISSIONS — USD amounts
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
        # pol-005 — Term Life Plus 10%
        make_commission("pol-005", "prod-001", "cli-009", 1100.0, 10.0, "sale",    days_ago(40)),
        make_commission("pol-005", "prod-001", "cli-009", 1100.0, 10.0, "renewal", days_ago(5)),
        # pol-006 — Health Shield PPO 8%
        make_commission("pol-006", "prod-002", "cli-010",  720.0,  8.0, "sale",    days_ago(70)),
        make_commission("pol-006", "prod-002", "cli-010",  720.0,  8.0, "renewal", days_ago(10)),
        # pol-007 — Critical Illness Guard 9%
        make_commission("pol-007", "prod-005", "cli-009",  480.0,  9.0, "sale",    days_ago(35)),
        # pol-009 — Auto Comprehensive 6% (lapsed)
        make_commission("pol-009", "prod-004", "cli-010", 1350.0,  6.0, "sale",    days_ago(395)),
        make_commission("pol-009", "prod-004", "cli-010", 1350.0,  6.0, "renewal", days_ago(30)),
        # pol-010 — Health Shield PPO 8%
        make_commission("pol-010", "prod-002", "cli-004",  860.0,  8.0, "sale",    days_ago(347)),
        # pol-011 — Term Life Plus 10%
        make_commission("pol-011", "prod-001", "cli-003", 1400.0, 10.0, "sale",    days_ago(320)),
        # pol-012 — Critical Illness Guard 9%
        make_commission("pol-012", "prod-005", "cli-006",  620.0,  9.0, "sale",    days_ago(293)),
        # pol-013 — Auto Comprehensive 6%
        make_commission("pol-013", "prod-004", "cli-007", 1680.0,  6.0, "sale",    days_ago(370)),
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
    # ACTIVITIES
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
        # Lead
        act("cli-001", "note",      "New lead from referral. Interested in term life. Needs follow-up for financial profiling.", ts=days_ago(30)),
        act("cli-002", "call",      "Initial call completed. Sarah is interested in health coverage for her family. Requested a quote.", ts=days_ago(25)),
        # Qualified
        act("cli-003", "note",      "Qualified. Annual income $95,000. 3 dependents. Exploring whole life options.", ts=days_ago(20)),
        act("cli-004", "follow_up", "Needs assessment complete. Shortlisted Health Shield PPO. Sending quote this week.", ts=days_ago(15)),
        # Proposal
        act("cli-005", "meeting",   "Proposal meeting held in Miami. Michael interested in Whole Life Advantage for estate planning.", ts=days_ago(10)),
        act("cli-006", "follow_up", "Sent Term Life Plus proposal via email. Jennifer is reviewing with her financial advisor.", ts=days_ago(8)),
        # Negotiation
        act("cli-007", "policy_created", "Application pol-001 created for Term Life Plus. Status: Draft.", "pol-001", ts=days_ago(5)),
        act("cli-008", "policy_created", "Application pol-002 created for Health Shield PPO. Status: Draft.", "pol-002", ts=days_ago(7)),
        act("cli-008", "status_change",  "Application pol-002 submitted to carrier. Awaiting underwriting review.", "pol-002", ts=days_ago(4)),
        act("cli-005", "policy_created", "Application pol-003 created for Whole Life Advantage. Status: Draft.", "pol-003", ts=days_ago(10)),
        act("cli-005", "status_change",  "pol-003 submitted to carrier.", "pol-003", ts=days_ago(9)),
        act("cli-005", "status_change",  "pol-003 moved to Underwriting. Medical exam scheduled.", "pol-003", ts=days_ago(6)),
        act("cli-006", "policy_created", "Application pol-004 created for Term Life Plus. Status: Draft.", "pol-004", ts=days_ago(12)),
        act("cli-006", "status_change",  "pol-004 cleared underwriting and moved to Approved. Ready to issue.", "pol-004", ts=days_ago(3)),
        # Closed — cli-009
        act("cli-009", "policy_created",      "Application pol-005 created for Term Life Plus.", "pol-005", ts=days_ago(60)),
        act("cli-009", "status_change",        "pol-005 issued. Policy active. Coverage begins today.", "pol-005", ts=days_ago(40)),
        act("cli-009", "commission_recorded",  "Sale commission of $110.00 recorded for pol-005.", "pol-005", ts=days_ago(40)),
        act("cli-009", "policy_created",       "Application pol-007 created for Critical Illness Guard.", "pol-007", ts=days_ago(55)),
        act("cli-009", "status_change",        "pol-007 issued. Critical Illness Guard policy active.", "pol-007", ts=days_ago(35)),
        act("cli-009", "commission_recorded",  "Sale commission of $43.20 recorded for pol-007.", "pol-007", ts=days_ago(35)),
        act("cli-009", "commission_recorded",  "Renewal commission of $110.00 recorded for pol-005.", "pol-005", ts=days_ago(5)),
        # Closed — cli-010
        act("cli-010", "policy_created",      "Application pol-006 created for Health Shield PPO.", "pol-006", ts=days_ago(90)),
        act("cli-010", "status_change",        "pol-006 issued. Health Shield PPO policy active.", "pol-006", ts=days_ago(70)),
        act("cli-010", "commission_recorded",  "Sale commission of $57.60 recorded for pol-006.", "pol-006", ts=days_ago(70)),
        # Rejected
        act("cli-003", "policy_created", "Application pol-008 created for Whole Life Advantage.", "pol-008", ts=days_ago(25)),
        act("cli-003", "status_change",  "pol-008 rejected. Underwriting flagged income-to-premium ratio. Exploring Term Life Plus as alternative.", "pol-008", ts=days_ago(18)),
        act("cli-003", "follow_up",      "Scheduled call with Robert to discuss Term Life Plus as an alternative option.", ts=days_ago(17)),
        # Lapsed
        act("cli-010", "status_change",  "pol-009 (Auto Comprehensive) lapsed. Renewal overdue. Contact Amanda immediately.", "pol-009", ts=days_ago(28)),
        act("cli-010", "follow_up",      "Left voicemail for Amanda re: lapsed auto policy. Follow up Thursday.", ts=days_ago(27)),
        # Renewals window activities
        act("cli-004", "policy_created",      "Application pol-010 created for Health Shield PPO.", "pol-010", ts=days_ago(350)),
        act("cli-004", "status_change",        "pol-010 issued. Health Shield PPO active.", "pol-010", ts=days_ago(347)),
        act("cli-004", "commission_recorded",  "Sale commission of $68.80 recorded for pol-010.", "pol-010", ts=days_ago(347)),
        act("cli-004", "follow_up",            "pol-010 renewal due in 18 days. Called Emily — she confirmed renewal intent.", "pol-010", ts=days_ago(2)),
        act("cli-003", "policy_created",      "Application pol-011 created for Term Life Plus.", "pol-011", ts=days_ago(325)),
        act("cli-003", "status_change",        "pol-011 issued. Term Life Plus active.", "pol-011", ts=days_ago(320)),
        act("cli-003", "commission_recorded",  "Sale commission of $140.00 recorded for pol-011.", "pol-011", ts=days_ago(320)),
        act("cli-006", "policy_created",      "Application pol-012 created for Critical Illness Guard.", "pol-012", ts=days_ago(298)),
        act("cli-006", "status_change",        "pol-012 issued. Critical Illness Guard active.", "pol-012", ts=days_ago(293)),
        act("cli-006", "commission_recorded",  "Sale commission of $55.80 recorded for pol-012.", "pol-012", ts=days_ago(293)),
        act("cli-007", "policy_created",      "Application pol-013 created for Auto Comprehensive.", "pol-013", ts=days_ago(375)),
        act("cli-007", "status_change",        "pol-013 issued. Auto Comprehensive active.", "pol-013", ts=days_ago(370)),
        act("cli-007", "commission_recorded",  "Sale commission of $100.80 recorded for pol-013.", "pol-013", ts=days_ago(370)),
        act("cli-007", "follow_up",            "pol-013 renewal is 5 days past due. Urgent: reach out to David Kim today.", "pol-013", ts=days_ago(4)),
    ]

    conn.executemany("""
        INSERT INTO activities
          (activity_id, client_id, policy_id, activity_type, description, metadata, timestamp)
        VALUES
          (:activity_id, :client_id, :policy_id, :activity_type, :description, :metadata, :timestamp)
    """, activities)

    conn.commit()
    conn.close()
    print(f"Seed complete: 10 clients, 5 products, {len(policies)} policies, {len(commissions)} commissions, {len(activities)} activities.")


if __name__ == "__main__":
    seed()
