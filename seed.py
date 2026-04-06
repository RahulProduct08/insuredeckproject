"""seed.py — US-market demo data for InsureDesk."""

import sqlite3
import uuid
import json
import hashlib
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta

from database import DB_PATH, init_db


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()

def days_from_now(n: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=n)).isoformat()

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def backfill_ledger(conn) -> None:
    """Create commission_ledger entries from existing commissions rows.

    For each existing commission row (BASE), also walks the agent_hierarchy BFS
    to generate OVERRIDE rows for uplines.
    """
    conn.row_factory = sqlite3.Row
    today = datetime.now(timezone.utc).isoformat()[:10]

    rows = conn.execute(
        "SELECT commission_id, policy_id, product_id, agent_id, premium, rate_percent, recorded_at "
        "FROM commissions"
    ).fetchall()

    for row in rows:
        policy_id = row["policy_id"]
        writing_agent_id = row["agent_id"]
        product_id = row["product_id"]
        premium_d = Decimal(str(row["premium"]))
        rate = row["rate_percent"]
        created_at = row["recorded_at"]

        if not writing_agent_id:
            continue

        # BASE entry
        base_amount = (premium_d * Decimal(str(rate)) / 100).quantize(
            Decimal("0.0001"), ROUND_HALF_UP
        )
        conn.execute("""
            INSERT OR IGNORE INTO commission_ledger
            (ledger_id, policy_id, agent_id, source_agent_id, earning_type,
             hierarchy_level, percentage, amount, visibility_scope, created_at)
            VALUES (?,?,?,?,'BASE',0,?,?,'SELF',?)
        """, (str(uuid.uuid4()), policy_id, writing_agent_id, writing_agent_id,
              float(rate), float(base_amount), created_at))

        # BFS upward
        visited = {writing_agent_id}
        frontier = [(writing_agent_id, 0)]
        while frontier:
            current, depth = frontier.pop(0)
            if depth >= 5:
                continue
            upline_rows = conn.execute(
                "SELECT upline_agent_id, override_percentage FROM agent_hierarchy "
                "WHERE downline_agent_id=? AND is_active=1",
                [current],
            ).fetchall()
            for ur in upline_rows:
                upline = ur["upline_agent_id"]
                if upline in visited:
                    continue
                visited.add(upline)

                # Check commission_rules for product+level override
                rule = conn.execute(
                    """SELECT override_percentage FROM commission_rules
                       WHERE product_id=? AND hierarchy_level=?
                         AND effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
                       ORDER BY effective_from DESC LIMIT 1""",
                    (product_id, depth + 1, today, today),
                ).fetchone()
                pct = rule["override_percentage"] if rule else ur["override_percentage"]

                amount = (premium_d * Decimal(str(pct)) / 100).quantize(
                    Decimal("0.0001"), ROUND_HALF_UP
                )
                conn.execute("""
                    INSERT OR IGNORE INTO commission_ledger
                    (ledger_id, policy_id, agent_id, source_agent_id, earning_type,
                     hierarchy_level, percentage, amount, visibility_scope, created_at)
                    VALUES (?,?,?,?,'OVERRIDE',?,?,?,'DOWNLINE',?)
                """, (str(uuid.uuid4()), policy_id, upline, writing_agent_id,
                      depth + 1, float(pct), float(amount), created_at))
                frontier.append((upline, depth + 1))


def seed() -> None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    if count > 0:
        print(f"Already seeded ({count} clients). Skipping.")
        conn.close()
        return

    now = utcnow()

    # ── AGENTS ──────────────────────────────────────────────────────────────
    agents = [
        {
            "agent_id": "agent-001",
            "name": "Alex Morgan",
            "email": "admin@insuredesk.com",
            "password_hash": _hash("admin123"),
            "role": "admin",
            "npn": "12345678",
            "license_states": "CA,TX,FL,NY,IL",
            "phone": "(312) 555-0001",
            "is_active": 1,
            "created_at": days_ago(180),
            "updated_at": days_ago(10),
        },
        {
            "agent_id": "agent-002",
            "name": "Jordan Rivera",
            "email": "agent@insuredesk.com",
            "password_hash": _hash("agent123"),
            "role": "agent",
            "npn": "87654321",
            "license_states": "CA,TX,FL",
            "phone": "(415) 555-0002",
            "is_active": 1,
            "created_at": days_ago(90),
            "updated_at": days_ago(5),
        },
        {
            "agent_id": "agent-003",
            "name": "Rachel Chen",
            "email": "rachel.chen@insuredesk.com",
            "password_hash": _hash("agent123"),
            "role": "agent",
            "npn": "11223344",
            "license_states": "CA,NY,WA",
            "phone": "(206) 555-0003",
            "is_active": 1,
            "created_at": days_ago(120),
            "updated_at": days_ago(7),
        },
        {
            "agent_id": "agent-004",
            "name": "Marcus Webb",
            "email": "marcus.webb@insuredesk.com",
            "password_hash": _hash("agent123"),
            "role": "agent",
            "npn": "55667788",
            "license_states": "CA,TX",
            "phone": "(213) 555-0004",
            "is_active": 1,
            "created_at": days_ago(60),
            "updated_at": days_ago(4),
        },
        {
            "agent_id": "agent-005",
            "name": "Sofia Park",
            "email": "sofia.park@insuredesk.com",
            "password_hash": _hash("agent123"),
            "role": "agent",
            "npn": "99001122",
            "license_states": "CA,FL,NY",
            "phone": "(305) 555-0005",
            "is_active": 1,
            "created_at": days_ago(45),
            "updated_at": days_ago(2),
        },
    ]

    conn.executemany("""
        INSERT INTO agents (agent_id, name, email, password_hash, role, npn,
            license_states, phone, is_active, created_at, updated_at)
        VALUES (:agent_id, :name, :email, :password_hash, :role, :npn,
            :license_states, :phone, :is_active, :created_at, :updated_at)
    """, agents)

    # ── PRODUCTS ─────────────────────────────────────────────────────────────
    products = [
        {"product_id": "prod-001", "name": "Term Life Plus",
         "description": "Pure term life insurance providing high coverage at low premiums. Ideal for income replacement and mortgage protection.",
         "min_premium": 600.0, "max_premium": 5000.0, "min_age": 18, "max_age": 65,
         "min_income": 30000.0, "commission_rate_percent": 10.0, "is_active": 1, "created_at": now},
        {"product_id": "prod-002", "name": "Health Shield PPO",
         "description": "Comprehensive PPO health plan covering hospitalization, surgery, specialist visits, and prescription drugs.",
         "min_premium": 400.0, "max_premium": 3500.0, "min_age": 18, "max_age": 64,
         "min_income": 25000.0, "commission_rate_percent": 8.0, "is_active": 1, "created_at": now},
        {"product_id": "prod-003", "name": "Whole Life Advantage",
         "description": "Permanent whole life insurance with guaranteed cash value accumulation and lifelong death benefit.",
         "min_premium": 1800.0, "max_premium": 15000.0, "min_age": 25, "max_age": 60,
         "min_income": 60000.0, "commission_rate_percent": 12.0, "is_active": 1, "created_at": now},
        {"product_id": "prod-004", "name": "Auto Comprehensive",
         "description": "Full auto insurance covering collision, comprehensive, liability, uninsured motorist, and roadside assistance.",
         "min_premium": 800.0, "max_premium": 3000.0, "min_age": 18, "max_age": 80,
         "min_income": 0.0, "commission_rate_percent": 6.0, "is_active": 1, "created_at": now},
        {"product_id": "prod-005", "name": "Critical Illness Guard",
         "description": "Lump-sum payout on diagnosis of 30+ critical illnesses including cancer, heart attack, and stroke.",
         "min_premium": 350.0, "max_premium": 2000.0, "min_age": 18, "max_age": 60,
         "min_income": 20000.0, "commission_rate_percent": 9.0, "is_active": 1, "created_at": now},
    ]

    conn.executemany("""
        INSERT INTO products (product_id, name, description, min_premium, max_premium,
            min_age, max_age, min_income, commission_rate_percent, is_active, created_at)
        VALUES (:product_id, :name, :description, :min_premium, :max_premium,
            :min_age, :max_age, :min_income, :commission_rate_percent, :is_active, :created_at)
    """, products)

    # ── CLIENTS ───────────────────────────────────────────────────────────────
    clients = [
        {"client_id": "cli-001", "name": "James Carter", "phone": "(312) 555-0101",
         "email": "james.carter@gmail.com", "age": 29, "income": None,
         "dependents": 0, "risk_appetite": "moderate", "stage": "Lead",
         "lead_source": "Cold Call", "lead_score": 38, "agent_id": "agent-001",
         "is_active": 1, "created_at": days_ago(30), "updated_at": days_ago(30)},
        {"client_id": "cli-002", "name": "Sarah Mitchell", "phone": "(415) 555-0182",
         "email": "sarah.mitchell@outlook.com", "age": 36, "income": None,
         "dependents": 2, "risk_appetite": "low", "stage": "Lead",
         "lead_source": "Online Ad", "lead_score": 40, "agent_id": "agent-002",
         "is_active": 1, "created_at": days_ago(25), "updated_at": days_ago(25)},
        {"client_id": "cli-003", "name": "Robert Thompson", "phone": "(713) 555-0247",
         "email": "robert.thompson@yahoo.com", "age": 44, "income": 95000.0,
         "dependents": 3, "risk_appetite": "moderate", "stage": "Qualified",
         "lead_source": "Referral", "lead_score": 72, "agent_id": "agent-001",
         "is_active": 1, "created_at": days_ago(20), "updated_at": days_ago(18)},
        {"client_id": "cli-004", "name": "Emily Davis", "phone": "(206) 555-0319",
         "email": "emily.davis@icloud.com", "age": 32, "income": 72000.0,
         "dependents": 1, "risk_appetite": "moderate", "stage": "Qualified",
         "lead_source": "Website", "lead_score": 60, "agent_id": "agent-002",
         "is_active": 1, "created_at": days_ago(18), "updated_at": days_ago(15)},
        {"client_id": "cli-005", "name": "Michael Rodriguez", "phone": "(305) 555-0456",
         "email": "m.rodriguez@gmail.com", "age": 50, "income": 145000.0,
         "dependents": 2, "risk_appetite": "high", "stage": "Proposal",
         "lead_source": "Referral", "lead_score": 80, "agent_id": "agent-001",
         "is_active": 1, "created_at": days_ago(15), "updated_at": days_ago(10)},
        {"client_id": "cli-006", "name": "Jennifer Walsh", "phone": "(617) 555-0523",
         "email": "j.walsh@outlook.com", "age": 39, "income": 88000.0,
         "dependents": 2, "risk_appetite": "moderate", "stage": "Proposal",
         "lead_source": "Event", "lead_score": 65, "agent_id": "agent-002",
         "is_active": 1, "created_at": days_ago(12), "updated_at": days_ago(8)},
        {"client_id": "cli-007", "name": "David Kim", "phone": "(213) 555-0634",
         "email": "david.kim@gmail.com", "age": 46, "income": 112000.0,
         "dependents": 3, "risk_appetite": "moderate", "stage": "Negotiation",
         "lead_source": "Referral", "lead_score": 78, "agent_id": "agent-001",
         "is_active": 1, "created_at": days_ago(10), "updated_at": days_ago(5)},
        {"client_id": "cli-008", "name": "Patricia Johnson", "phone": "(602) 555-0789",
         "email": "p.johnson@yahoo.com", "age": 53, "income": 67000.0,
         "dependents": 1, "risk_appetite": "low", "stage": "Negotiation",
         "lead_source": "Social Media", "lead_score": 63, "agent_id": "agent-002",
         "is_active": 1, "created_at": days_ago(8), "updated_at": days_ago(3)},
        {"client_id": "cli-009", "name": "Christopher Lee", "phone": "(404) 555-0812",
         "email": "chris.lee@gmail.com", "age": 38, "income": 78000.0,
         "dependents": 2, "risk_appetite": "moderate", "stage": "Closed",
         "lead_source": "Existing Client", "lead_score": 85, "agent_id": "agent-001",
         "is_active": 1, "created_at": days_ago(60), "updated_at": days_ago(40)},
        {"client_id": "cli-010", "name": "Amanda Foster", "phone": "(503) 555-0965",
         "email": "a.foster@icloud.com", "age": 30, "income": 54000.0,
         "dependents": 0, "risk_appetite": "high", "stage": "Closed",
         "lead_source": "Online Ad", "lead_score": 75, "agent_id": "agent-002",
         "is_active": 1, "created_at": days_ago(90), "updated_at": days_ago(70)},
    ]

    conn.executemany("""
        INSERT INTO clients (client_id, name, phone, email, age, income, dependents,
            risk_appetite, stage, lead_source, lead_score, agent_id, is_active, created_at, updated_at)
        VALUES (:client_id, :name, :phone, :email, :age, :income, :dependents,
            :risk_appetite, :stage, :lead_source, :lead_score, :agent_id, :is_active, :created_at, :updated_at)
    """, clients)

    # ── POLICIES ─────────────────────────────────────────────────────────────
    default_docs = json.dumps(["Government-Issued ID", "Proof of Income", "Medical Exam Report", "Signed Application Form"])

    policies = [
        {"policy_id": "pol-001", "client_id": "cli-007", "product_id": "prod-001", "agent_id": "agent-001",
         "premium": 1200.0, "status": "Draft", "documents_checklist": default_docs, "documents_attached": "[]",
         "issued_at": None, "renewal_due_at": None, "created_at": days_ago(5), "updated_at": days_ago(5)},
        {"policy_id": "pol-002", "client_id": "cli-008", "product_id": "prod-002", "agent_id": "agent-002",
         "premium": 980.0, "status": "Submitted", "documents_checklist": default_docs,
         "documents_attached": json.dumps(["Government-Issued ID", "Proof of Income"]),
         "issued_at": None, "renewal_due_at": None, "created_at": days_ago(7), "updated_at": days_ago(4)},
        {"policy_id": "pol-003", "client_id": "cli-005", "product_id": "prod-003", "agent_id": "agent-001",
         "premium": 4200.0, "status": "Underwriting", "documents_checklist": default_docs,
         "documents_attached": json.dumps(["Government-Issued ID", "Proof of Income", "Medical Exam Report"]),
         "issued_at": None, "renewal_due_at": None, "created_at": days_ago(10), "updated_at": days_ago(6)},
        {"policy_id": "pol-004", "client_id": "cli-006", "product_id": "prod-001", "agent_id": "agent-002",
         "premium": 1550.0, "status": "Approved", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": None, "renewal_due_at": None,
         "created_at": days_ago(12), "updated_at": days_ago(3)},
        {"policy_id": "pol-005", "client_id": "cli-009", "product_id": "prod-001", "agent_id": "agent-001",
         "premium": 1100.0, "status": "Issued", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": days_ago(40), "renewal_due_at": days_from_now(325),
         "created_at": days_ago(60), "updated_at": days_ago(40)},
        {"policy_id": "pol-006", "client_id": "cli-010", "product_id": "prod-002", "agent_id": "agent-002",
         "premium": 720.0, "status": "Issued", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": days_ago(70), "renewal_due_at": days_from_now(295),
         "created_at": days_ago(90), "updated_at": days_ago(70)},
        {"policy_id": "pol-007", "client_id": "cli-009", "product_id": "prod-005", "agent_id": "agent-001",
         "premium": 480.0, "status": "Issued", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": days_ago(35), "renewal_due_at": days_from_now(330),
         "created_at": days_ago(55), "updated_at": days_ago(35)},
        {"policy_id": "pol-008", "client_id": "cli-003", "product_id": "prod-003", "agent_id": "agent-001",
         "premium": 5800.0, "status": "Rejected", "documents_checklist": default_docs,
         "documents_attached": json.dumps(["Government-Issued ID", "Proof of Income"]),
         "issued_at": None, "renewal_due_at": None, "created_at": days_ago(25), "updated_at": days_ago(18)},
        {"policy_id": "pol-009", "client_id": "cli-010", "product_id": "prod-004", "agent_id": "agent-002",
         "premium": 1350.0, "status": "Lapsed", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": days_ago(395), "renewal_due_at": days_ago(30),
         "created_at": days_ago(400), "updated_at": days_ago(28)},
        # Renewals window
        {"policy_id": "pol-010", "client_id": "cli-004", "product_id": "prod-002", "agent_id": "agent-002",
         "premium": 860.0, "status": "Issued", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": days_ago(347), "renewal_due_at": days_from_now(18),
         "created_at": days_ago(350), "updated_at": days_ago(347)},
        {"policy_id": "pol-011", "client_id": "cli-003", "product_id": "prod-001", "agent_id": "agent-001",
         "premium": 1400.0, "status": "Issued", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": days_ago(320), "renewal_due_at": days_from_now(45),
         "created_at": days_ago(325), "updated_at": days_ago(320)},
        {"policy_id": "pol-012", "client_id": "cli-006", "product_id": "prod-005", "agent_id": "agent-002",
         "premium": 620.0, "status": "Issued", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": days_ago(293), "renewal_due_at": days_from_now(72),
         "created_at": days_ago(298), "updated_at": days_ago(293)},
        {"policy_id": "pol-013", "client_id": "cli-007", "product_id": "prod-004", "agent_id": "agent-001",
         "premium": 1680.0, "status": "Issued", "documents_checklist": default_docs,
         "documents_attached": default_docs, "issued_at": days_ago(370), "renewal_due_at": days_ago(5),
         "created_at": days_ago(375), "updated_at": days_ago(370)},
    ]

    conn.executemany("""
        INSERT INTO policies (policy_id, client_id, product_id, agent_id, premium, status,
            documents_checklist, documents_attached, issued_at, renewal_due_at, created_at, updated_at)
        VALUES (:policy_id, :client_id, :product_id, :agent_id, :premium, :status,
            :documents_checklist, :documents_attached, :issued_at, :renewal_due_at, :created_at, :updated_at)
    """, policies)

    # Policy status history
    history = [
        ("pol-001", None, "Draft", days_ago(5)),
        ("pol-002", None, "Draft", days_ago(7)), ("pol-002", "Draft", "Submitted", days_ago(4)),
        ("pol-003", None, "Draft", days_ago(10)), ("pol-003", "Draft", "Submitted", days_ago(9)),
        ("pol-003", "Submitted", "Underwriting", days_ago(6)),
        ("pol-004", None, "Draft", days_ago(12)), ("pol-004", "Draft", "Submitted", days_ago(11)),
        ("pol-004", "Submitted", "Underwriting", days_ago(9)), ("pol-004", "Underwriting", "Approved", days_ago(3)),
        ("pol-005", None, "Draft", days_ago(60)), ("pol-005", "Draft", "Submitted", days_ago(58)),
        ("pol-005", "Submitted", "Underwriting", days_ago(55)), ("pol-005", "Underwriting", "Approved", days_ago(50)),
        ("pol-005", "Approved", "Issued", days_ago(40)),
        ("pol-006", None, "Draft", days_ago(90)), ("pol-006", "Draft", "Submitted", days_ago(88)),
        ("pol-006", "Submitted", "Underwriting", days_ago(85)), ("pol-006", "Underwriting", "Approved", days_ago(80)),
        ("pol-006", "Approved", "Issued", days_ago(70)),
        ("pol-007", None, "Draft", days_ago(55)), ("pol-007", "Draft", "Submitted", days_ago(53)),
        ("pol-007", "Submitted", "Underwriting", days_ago(50)), ("pol-007", "Underwriting", "Approved", days_ago(45)),
        ("pol-007", "Approved", "Issued", days_ago(35)),
        ("pol-008", None, "Draft", days_ago(25)), ("pol-008", "Draft", "Submitted", days_ago(23)),
        ("pol-008", "Submitted", "Underwriting", days_ago(20)), ("pol-008", "Underwriting", "Rejected", days_ago(18)),
        ("pol-009", None, "Draft", days_ago(400)), ("pol-009", "Draft", "Submitted", days_ago(398)),
        ("pol-009", "Submitted", "Underwriting", days_ago(396)), ("pol-009", "Underwriting", "Approved", days_ago(393)),
        ("pol-009", "Approved", "Issued", days_ago(395)), ("pol-009", "Issued", "Lapsed", days_ago(28)),
        ("pol-010", None, "Draft", days_ago(350)), ("pol-010", "Draft", "Submitted", days_ago(348)),
        ("pol-010", "Submitted", "Underwriting", days_ago(346)), ("pol-010", "Underwriting", "Approved", days_ago(349)),
        ("pol-010", "Approved", "Issued", days_ago(347)),
        ("pol-011", None, "Draft", days_ago(325)), ("pol-011", "Draft", "Submitted", days_ago(323)),
        ("pol-011", "Submitted", "Underwriting", days_ago(321)), ("pol-011", "Underwriting", "Approved", days_ago(322)),
        ("pol-011", "Approved", "Issued", days_ago(320)),
        ("pol-012", None, "Draft", days_ago(298)), ("pol-012", "Draft", "Submitted", days_ago(296)),
        ("pol-012", "Submitted", "Underwriting", days_ago(295)), ("pol-012", "Underwriting", "Approved", days_ago(294)),
        ("pol-012", "Approved", "Issued", days_ago(293)),
        ("pol-013", None, "Draft", days_ago(375)), ("pol-013", "Draft", "Submitted", days_ago(373)),
        ("pol-013", "Submitted", "Underwriting", days_ago(372)), ("pol-013", "Underwriting", "Approved", days_ago(371)),
        ("pol-013", "Approved", "Issued", days_ago(370)),
    ]
    conn.executemany(
        "INSERT INTO policy_status_history (policy_id, from_status, to_status, changed_at) VALUES (?,?,?,?)",
        history)

    # ── COMMISSIONS ──────────────────────────────────────────────────────────
    def mc(pol_id, prod_id, cli_id, premium, rate, event, ts, agent_id="agent-001"):
        return {"commission_id": str(uuid.uuid4()), "policy_id": pol_id, "product_id": prod_id,
                "client_id": cli_id, "event_type": event, "amount": round(premium * rate / 100, 2),
                "rate_percent": rate, "premium": premium, "agent_id": agent_id, "recorded_at": ts}

    commissions = [
        mc("pol-005", "prod-001", "cli-009", 1100.0, 10.0, "sale",    days_ago(40)),
        mc("pol-005", "prod-001", "cli-009", 1100.0, 10.0, "renewal", days_ago(5)),
        mc("pol-006", "prod-002", "cli-010",  720.0,  8.0, "sale",    days_ago(70), "agent-002"),
        mc("pol-006", "prod-002", "cli-010",  720.0,  8.0, "renewal", days_ago(10), "agent-002"),
        mc("pol-007", "prod-005", "cli-009",  480.0,  9.0, "sale",    days_ago(35)),
        mc("pol-009", "prod-004", "cli-010", 1350.0,  6.0, "sale",    days_ago(395), "agent-002"),
        mc("pol-009", "prod-004", "cli-010", 1350.0,  6.0, "renewal", days_ago(30), "agent-002"),
        mc("pol-010", "prod-002", "cli-004",  860.0,  8.0, "sale",    days_ago(347), "agent-002"),
        mc("pol-011", "prod-001", "cli-003", 1400.0, 10.0, "sale",    days_ago(320)),
        mc("pol-012", "prod-005", "cli-006",  620.0,  9.0, "sale",    days_ago(293), "agent-002"),
        mc("pol-013", "prod-004", "cli-007", 1680.0,  6.0, "sale",    days_ago(370)),
    ]
    conn.executemany("""
        INSERT INTO commissions (commission_id, policy_id, product_id, client_id, event_type,
            amount, rate_percent, premium, agent_id, recorded_at)
        VALUES (:commission_id, :policy_id, :product_id, :client_id, :event_type,
            :amount, :rate_percent, :premium, :agent_id, :recorded_at)
    """, commissions)

    # ── TASKS ─────────────────────────────────────────────────────────────────
    tasks = [
        {"task_id": "task-001", "client_id": "cli-007", "policy_id": "pol-013", "agent_id": "agent-001",
         "title": "Follow up on overdue renewal — David Kim", "priority": "high", "status": "open",
         "due_date": days_ago(3), "completed_at": None, "description": "pol-013 Auto Comprehensive is 5 days past renewal. Call David today.",
         "created_at": days_ago(6), "updated_at": days_ago(6)},
        {"task_id": "task-002", "client_id": "cli-004", "policy_id": "pol-010", "agent_id": "agent-002",
         "title": "Renewal check-in — Emily Davis", "priority": "high", "status": "open",
         "due_date": days_from_now(3), "completed_at": None, "description": "Health Shield PPO renews in 18 days. Confirm intent and prepare renewal docs.",
         "created_at": days_ago(2), "updated_at": days_ago(2)},
        {"task_id": "task-003", "client_id": "cli-006", "policy_id": "pol-004", "agent_id": "agent-002",
         "title": "Issue pol-004 — Jennifer Walsh approved", "priority": "high", "status": "open",
         "due_date": utcnow()[:10], "completed_at": None, "description": "Term Life Plus application approved. Issue the policy and collect first premium.",
         "created_at": days_ago(1), "updated_at": days_ago(1)},
        {"task_id": "task-004", "client_id": "cli-005", "policy_id": "pol-003", "agent_id": "agent-001",
         "title": "Underwriting follow-up — Michael Rodriguez", "priority": "medium", "status": "open",
         "due_date": days_from_now(2), "completed_at": None, "description": "pol-003 has been in underwriting 6 days. Check status with carrier.",
         "created_at": days_ago(3), "updated_at": days_ago(3)},
        {"task_id": "task-005", "client_id": "cli-001", "policy_id": None, "agent_id": "agent-001",
         "title": "Income profile call — James Carter", "priority": "medium", "status": "open",
         "due_date": days_from_now(1), "completed_at": None, "description": "James has no income on file. Call to complete financial profile before proposing a product.",
         "created_at": days_ago(5), "updated_at": days_ago(5)},
        {"task_id": "task-006", "client_id": "cli-002", "policy_id": None, "agent_id": "agent-002",
         "title": "Send health coverage quotes — Sarah Mitchell", "priority": "medium", "status": "open",
         "due_date": days_from_now(2), "completed_at": None, "description": "Sarah requested a quote for family health coverage. Send Health Shield PPO comparison.",
         "created_at": days_ago(4), "updated_at": days_ago(4)},
        {"task_id": "task-007", "client_id": "cli-003", "policy_id": "pol-011", "agent_id": "agent-001",
         "title": "Renewal reminder — Robert Thompson (45 days)", "priority": "low", "status": "open",
         "due_date": days_from_now(14), "completed_at": None, "description": "pol-011 renews in 45 days. Send renewal reminder email and schedule call.",
         "created_at": days_ago(1), "updated_at": days_ago(1)},
        {"task_id": "task-008", "client_id": "cli-009", "policy_id": None, "agent_id": "agent-001",
         "title": "Cross-sell Auto Comprehensive — Christopher Lee", "priority": "low", "status": "completed",
         "due_date": days_ago(10), "completed_at": days_ago(8), "description": "Chris has life + critical illness. Discuss auto coverage.",
         "created_at": days_ago(15), "updated_at": days_ago(8)},
    ]
    conn.executemany("""
        INSERT INTO tasks (task_id, client_id, policy_id, agent_id, title, description,
            priority, status, due_date, completed_at, created_at, updated_at)
        VALUES (:task_id, :client_id, :policy_id, :agent_id, :title, :description,
            :priority, :status, :due_date, :completed_at, :created_at, :updated_at)
    """, tasks)

    # ── ACTIVITIES ────────────────────────────────────────────────────────────
    def act(cli_id, atype, desc, pol_id=None, agent_id="agent-001", ts=None):
        return {"activity_id": str(uuid.uuid4()), "client_id": cli_id, "policy_id": pol_id,
                "agent_id": agent_id, "activity_type": atype, "description": desc,
                "metadata": "{}", "timestamp": ts or utcnow()}

    activities = [
        act("cli-001", "note",      "New lead via cold call. Interested in term life. No income on file yet.", ts=days_ago(30)),
        act("cli-002", "call",      "Initial call complete. Sarah wants family health coverage. Requested quote.", agent_id="agent-002", ts=days_ago(25)),
        act("cli-003", "note",      "Qualified. Income $95k, 3 dependents. Exploring whole life.", ts=days_ago(20)),
        act("cli-004", "follow_up", "Needs assessment done. Shortlisted Health Shield PPO. Sending quote.", agent_id="agent-002", ts=days_ago(15)),
        act("cli-005", "meeting",   "Proposal meeting in Miami. Michael keen on Whole Life for estate planning.", ts=days_ago(10)),
        act("cli-006", "follow_up", "Sent Term Life Plus proposal. Jennifer reviewing with financial advisor.", agent_id="agent-002", ts=days_ago(8)),
        act("cli-007", "policy_created", "pol-001 created: Term Life Plus. Status: Draft.", pol_id="pol-001", ts=days_ago(5)),
        act("cli-008", "policy_created", "pol-002 created: Health Shield PPO. Status: Draft.", pol_id="pol-002", agent_id="agent-002", ts=days_ago(7)),
        act("cli-008", "status_change",  "pol-002 submitted. Awaiting underwriting.", pol_id="pol-002", agent_id="agent-002", ts=days_ago(4)),
        act("cli-005", "policy_created", "pol-003 created: Whole Life Advantage. Status: Draft.", pol_id="pol-003", ts=days_ago(10)),
        act("cli-005", "status_change",  "pol-003 submitted.", pol_id="pol-003", ts=days_ago(9)),
        act("cli-005", "status_change",  "pol-003 in Underwriting. Medical exam scheduled.", pol_id="pol-003", ts=days_ago(6)),
        act("cli-006", "policy_created", "pol-004 created: Term Life Plus. Status: Draft.", pol_id="pol-004", agent_id="agent-002", ts=days_ago(12)),
        act("cli-006", "status_change",  "pol-004 Approved. Ready to issue.", pol_id="pol-004", agent_id="agent-002", ts=days_ago(3)),
        act("cli-009", "policy_created",     "pol-005 created: Term Life Plus.", pol_id="pol-005", ts=days_ago(60)),
        act("cli-009", "status_change",      "pol-005 issued. Coverage active.", pol_id="pol-005", ts=days_ago(40)),
        act("cli-009", "commission_recorded","Sale commission $110.00 recorded for pol-005.", pol_id="pol-005", ts=days_ago(40)),
        act("cli-009", "policy_created",     "pol-007 created: Critical Illness Guard.", pol_id="pol-007", ts=days_ago(55)),
        act("cli-009", "status_change",      "pol-007 issued. Critical Illness Guard active.", pol_id="pol-007", ts=days_ago(35)),
        act("cli-009", "commission_recorded","Sale commission $43.20 recorded for pol-007.", pol_id="pol-007", ts=days_ago(35)),
        act("cli-009", "commission_recorded","Renewal commission $110.00 for pol-005.", pol_id="pol-005", ts=days_ago(5)),
        act("cli-010", "policy_created",     "pol-006 created: Health Shield PPO.", pol_id="pol-006", agent_id="agent-002", ts=days_ago(90)),
        act("cli-010", "status_change",      "pol-006 issued. Health Shield PPO active.", pol_id="pol-006", agent_id="agent-002", ts=days_ago(70)),
        act("cli-010", "commission_recorded","Sale commission $57.60 for pol-006.", pol_id="pol-006", agent_id="agent-002", ts=days_ago(70)),
        act("cli-003", "policy_created",     "pol-008 created: Whole Life Advantage.", pol_id="pol-008", ts=days_ago(25)),
        act("cli-003", "status_change",      "pol-008 rejected — income/premium ratio flagged. Exploring Term Life as alternative.", pol_id="pol-008", ts=days_ago(18)),
        act("cli-010", "status_change",      "pol-009 lapsed. Renewal 30 days overdue. Contact Amanda immediately.", pol_id="pol-009", agent_id="agent-002", ts=days_ago(28)),
        act("cli-004", "policy_created",     "pol-010 created: Health Shield PPO.", pol_id="pol-010", agent_id="agent-002", ts=days_ago(350)),
        act("cli-004", "status_change",      "pol-010 issued.", pol_id="pol-010", agent_id="agent-002", ts=days_ago(347)),
        act("cli-004", "follow_up",          "pol-010 renews in 18 days. Emily confirmed renewal intent.", pol_id="pol-010", agent_id="agent-002", ts=days_ago(2)),
        act("cli-003", "policy_created",     "pol-011 created: Term Life Plus.", pol_id="pol-011", ts=days_ago(325)),
        act("cli-003", "status_change",      "pol-011 issued.", pol_id="pol-011", ts=days_ago(320)),
        act("cli-006", "policy_created",     "pol-012 created: Critical Illness Guard.", pol_id="pol-012", agent_id="agent-002", ts=days_ago(298)),
        act("cli-006", "status_change",      "pol-012 issued.", pol_id="pol-012", agent_id="agent-002", ts=days_ago(293)),
        act("cli-007", "policy_created",     "pol-013 created: Auto Comprehensive.", pol_id="pol-013", ts=days_ago(375)),
        act("cli-007", "status_change",      "pol-013 issued.", pol_id="pol-013", ts=days_ago(370)),
        act("cli-007", "follow_up",          "pol-013 renewal 5 days PAST DUE. Urgent: reach David Kim today.", pol_id="pol-013", ts=days_ago(4)),
    ]

    conn.executemany("""
        INSERT INTO activities (activity_id, client_id, policy_id, agent_id,
            activity_type, description, metadata, timestamp)
        VALUES (:activity_id, :client_id, :policy_id, :agent_id,
            :activity_type, :description, :metadata, :timestamp)
    """, activities)

    # ── AGENT HIERARCHY ──────────────────────────────────────────────────────
    # Edges: downline → upline direction
    # agent-001 (Alex/MGA) ← agent-002 (Jordan), 5% override
    # agent-001 (Alex/MGA) ← agent-003 (Rachel), 5% override
    # agent-003 (Rachel)   ← agent-004 (Marcus), 3% override
    # agent-003 (Rachel)   ← agent-005 (Sofia),  3% override
    hierarchy_edges = [
        {"upline_agent_id": "agent-001", "downline_agent_id": "agent-002",
         "override_percentage": 5.0, "hierarchy_level": 1, "is_active": 1, "created_at": days_ago(80)},
        {"upline_agent_id": "agent-001", "downline_agent_id": "agent-003",
         "override_percentage": 5.0, "hierarchy_level": 1, "is_active": 1, "created_at": days_ago(110)},
        {"upline_agent_id": "agent-003", "downline_agent_id": "agent-004",
         "override_percentage": 3.0, "hierarchy_level": 1, "is_active": 1, "created_at": days_ago(55)},
        {"upline_agent_id": "agent-003", "downline_agent_id": "agent-005",
         "override_percentage": 3.0, "hierarchy_level": 1, "is_active": 1, "created_at": days_ago(40)},
    ]
    conn.executemany("""
        INSERT INTO agent_hierarchy (upline_agent_id, downline_agent_id, override_percentage,
            hierarchy_level, is_active, created_at)
        VALUES (:upline_agent_id, :downline_agent_id, :override_percentage,
            :hierarchy_level, :is_active, :created_at)
    """, hierarchy_edges)

    # ── COMMISSION RULES ─────────────────────────────────────────────────────
    # Product-specific overrides for prod-003 (Whole Life Advantage)
    commission_rules = [
        {"rule_id": str(uuid.uuid4()), "product_id": "prod-003", "agent_role": None,
         "hierarchy_level": 1, "override_percentage": 4.0,
         "effective_from": days_ago(180)[:10], "effective_to": None},
        {"rule_id": str(uuid.uuid4()), "product_id": "prod-003", "agent_role": None,
         "hierarchy_level": 2, "override_percentage": 2.5,
         "effective_from": days_ago(180)[:10], "effective_to": None},
    ]
    conn.executemany("""
        INSERT INTO commission_rules (rule_id, product_id, agent_role, hierarchy_level,
            override_percentage, effective_from, effective_to)
        VALUES (:rule_id, :product_id, :agent_role, :hierarchy_level,
            :override_percentage, :effective_from, :effective_to)
    """, commission_rules)

    # ── LEDGER BACKFILL ──────────────────────────────────────────────────────
    backfill_ledger(conn)

    conn.commit()
    conn.close()
    print(f"Seed complete: 5 agents, 10 clients, 5 products, {len(policies)} policies, "
          f"{len(commissions)} commissions, {len(tasks)} tasks, {len(activities)} activities, "
          f"{len(hierarchy_edges)} hierarchy edges.")


if __name__ == "__main__":
    seed()
