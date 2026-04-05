"""
database.py
-----------
SQLite connection helper and schema initialisation for the Insurance Agent Portal.

Usage:
    from database import get_db, init_db, row_to_dict, DB_PATH

    # In Flask routes:
    db = get_db()
    rows = db.execute("SELECT * FROM clients").fetchall()
    clients = [row_to_dict(r) for r in rows]
    db.close()
"""

import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "insurance_portal.db")

# Columns that contain JSON-encoded text — auto-decoded by row_to_dict()
_JSON_COLUMNS = {"documents_checklist", "documents_attached", "metadata", "eligibility_rules"}


def get_db() -> sqlite3.Connection:
    """Return a WAL-mode, foreign-key-enforced SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict, auto-decoding known JSON columns."""
    if row is None:
        return None
    d = dict(row)
    for col in _JSON_COLUMNS:
        if col in d and isinstance(d[col], str):
            try:
                d[col] = json.loads(d[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def init_db() -> None:
    """Create all tables and indexes (idempotent — uses IF NOT EXISTS)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id     TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            phone         TEXT NOT NULL,
            email         TEXT NOT NULL,
            age           INTEGER,
            income        REAL,
            dependents    INTEGER DEFAULT 0,
            risk_appetite TEXT DEFAULT 'moderate',
            stage         TEXT NOT NULL DEFAULT 'Lead',
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id              TEXT PRIMARY KEY,
            name                    TEXT NOT NULL,
            description             TEXT,
            min_premium             REAL NOT NULL,
            max_premium             REAL NOT NULL,
            min_age                 INTEGER DEFAULT 0,
            max_age                 INTEGER DEFAULT 100,
            min_income              REAL DEFAULT 0,
            commission_rate_percent REAL NOT NULL DEFAULT 10.0,
            is_active               INTEGER NOT NULL DEFAULT 1,
            created_at              TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS policies (
            policy_id           TEXT PRIMARY KEY,
            client_id           TEXT NOT NULL REFERENCES clients(client_id),
            product_id          TEXT NOT NULL REFERENCES products(product_id),
            premium             REAL NOT NULL,
            status              TEXT NOT NULL DEFAULT 'Draft',
            documents_checklist TEXT NOT NULL DEFAULT '[]',
            documents_attached  TEXT NOT NULL DEFAULT '[]',
            issued_at           TEXT,
            renewal_due_at      TEXT,
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS policy_status_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id   TEXT NOT NULL REFERENCES policies(policy_id),
            from_status TEXT,
            to_status   TEXT NOT NULL,
            changed_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS commissions (
            commission_id TEXT PRIMARY KEY,
            policy_id     TEXT NOT NULL REFERENCES policies(policy_id),
            product_id    TEXT NOT NULL REFERENCES products(product_id),
            client_id     TEXT NOT NULL REFERENCES clients(client_id),
            event_type    TEXT NOT NULL,
            amount        REAL NOT NULL,
            rate_percent  REAL NOT NULL,
            premium       REAL NOT NULL,
            agent_id      TEXT,
            recorded_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activities (
            activity_id   TEXT PRIMARY KEY,
            client_id     TEXT NOT NULL REFERENCES clients(client_id),
            policy_id     TEXT REFERENCES policies(policy_id),
            activity_type TEXT NOT NULL,
            description   TEXT NOT NULL,
            metadata      TEXT NOT NULL DEFAULT '{}',
            timestamp     TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_policies_client    ON policies(client_id);
        CREATE INDEX IF NOT EXISTS idx_policies_status    ON policies(status);
        CREATE INDEX IF NOT EXISTS idx_commissions_policy ON commissions(policy_id);
        CREATE INDEX IF NOT EXISTS idx_commissions_client ON commissions(client_id);
        CREATE INDEX IF NOT EXISTS idx_activities_client  ON activities(client_id);
        CREATE INDEX IF NOT EXISTS idx_activities_policy  ON activities(policy_id);
        CREATE INDEX IF NOT EXISTS idx_activities_ts      ON activities(timestamp);
    """)

    conn.commit()
    conn.close()
    print(f"Database initialised at: {DB_PATH}")


if __name__ == "__main__":
    init_db()
