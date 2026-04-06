"""
database.py — SQLite helper + schema for InsureDesk.
"""

import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "insurance_portal.db")

_JSON_COLUMNS = {"documents_checklist", "documents_attached", "metadata",
                 "eligibility_rules", "recommended_products", "answers"}


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
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
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        -- Agents (users of the portal)
        CREATE TABLE IF NOT EXISTS agents (
            agent_id       TEXT PRIMARY KEY,
            name           TEXT NOT NULL,
            email          TEXT NOT NULL UNIQUE,
            password_hash  TEXT NOT NULL,
            role           TEXT NOT NULL DEFAULT 'agent',
            npn            TEXT,
            license_states TEXT,
            phone          TEXT,
            is_active      INTEGER NOT NULL DEFAULT 1,
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clients (
            client_id            TEXT PRIMARY KEY,
            name                 TEXT NOT NULL,
            phone                TEXT NOT NULL,
            email                TEXT NOT NULL,
            age                  INTEGER,
            income               REAL,
            dependents           INTEGER DEFAULT 0,
            risk_appetite        TEXT DEFAULT 'moderate',
            stage                TEXT NOT NULL DEFAULT 'Lead',
            lead_source          TEXT DEFAULT 'Other',
            referred_by_client_id TEXT REFERENCES clients(client_id),
            lead_score           INTEGER DEFAULT 50,
            agent_id             TEXT REFERENCES agents(agent_id),
            is_active            INTEGER NOT NULL DEFAULT 1,
            created_at           TEXT NOT NULL,
            updated_at           TEXT NOT NULL
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
            agent_id            TEXT REFERENCES agents(agent_id),
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
            agent_id      TEXT REFERENCES agents(agent_id),
            recorded_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activities (
            activity_id   TEXT PRIMARY KEY,
            client_id     TEXT NOT NULL REFERENCES clients(client_id),
            policy_id     TEXT REFERENCES policies(policy_id),
            agent_id      TEXT REFERENCES agents(agent_id),
            activity_type TEXT NOT NULL,
            description   TEXT NOT NULL,
            metadata      TEXT NOT NULL DEFAULT '{}',
            timestamp     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            task_id      TEXT PRIMARY KEY,
            client_id    TEXT REFERENCES clients(client_id),
            policy_id    TEXT REFERENCES policies(policy_id),
            agent_id     TEXT REFERENCES agents(agent_id),
            title        TEXT NOT NULL,
            description  TEXT,
            priority     TEXT NOT NULL DEFAULT 'medium',
            status       TEXT NOT NULL DEFAULT 'open',
            due_date     TEXT,
            completed_at TEXT,
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id    TEXT REFERENCES agents(agent_id),
            table_name  TEXT NOT NULL,
            record_id   TEXT NOT NULL,
            field_name  TEXT NOT NULL,
            old_value   TEXT,
            new_value   TEXT,
            changed_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS needs_analyses (
            analysis_id          TEXT PRIMARY KEY,
            client_id            TEXT NOT NULL REFERENCES clients(client_id),
            agent_id             TEXT REFERENCES agents(agent_id),
            answers              TEXT NOT NULL DEFAULT '{}',
            recommended_products TEXT NOT NULL DEFAULT '[]',
            notes                TEXT,
            created_at           TEXT NOT NULL,
            updated_at           TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_policies_client    ON policies(client_id);
        CREATE INDEX IF NOT EXISTS idx_policies_status    ON policies(status);
        CREATE INDEX IF NOT EXISTS idx_policies_agent     ON policies(agent_id);
        CREATE INDEX IF NOT EXISTS idx_commissions_policy ON commissions(policy_id);
        CREATE INDEX IF NOT EXISTS idx_commissions_client ON commissions(client_id);
        CREATE INDEX IF NOT EXISTS idx_commissions_agent  ON commissions(agent_id);
        CREATE INDEX IF NOT EXISTS idx_activities_client  ON activities(client_id);
        CREATE INDEX IF NOT EXISTS idx_activities_policy  ON activities(policy_id);
        CREATE INDEX IF NOT EXISTS idx_activities_ts      ON activities(timestamp);
        CREATE INDEX IF NOT EXISTS idx_tasks_agent        ON tasks(agent_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status       ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_due          ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_audit_table        ON audit_log(table_name, record_id);
        CREATE INDEX IF NOT EXISTS idx_clients_agent      ON clients(agent_id);

        CREATE TABLE IF NOT EXISTS agent_hierarchy (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            upline_agent_id     TEXT    NOT NULL REFERENCES agents(agent_id),
            downline_agent_id   TEXT    NOT NULL REFERENCES agents(agent_id),
            override_percentage REAL    NOT NULL DEFAULT 0.0,
            hierarchy_level     INTEGER NOT NULL DEFAULT 1,
            is_active           INTEGER NOT NULL DEFAULT 1,
            created_at          TEXT    NOT NULL,
            CHECK (upline_agent_id != downline_agent_id),
            UNIQUE (upline_agent_id, downline_agent_id)
        );
        CREATE INDEX IF NOT EXISTS idx_hierarchy_downline ON agent_hierarchy(downline_agent_id);
        CREATE INDEX IF NOT EXISTS idx_hierarchy_upline   ON agent_hierarchy(upline_agent_id);

        CREATE TABLE IF NOT EXISTS commission_ledger (
            ledger_id        TEXT PRIMARY KEY,
            policy_id        TEXT NOT NULL REFERENCES policies(policy_id),
            agent_id         TEXT NOT NULL REFERENCES agents(agent_id),
            source_agent_id  TEXT NOT NULL REFERENCES agents(agent_id),
            earning_type     TEXT NOT NULL DEFAULT 'BASE',
            hierarchy_level  INTEGER NOT NULL DEFAULT 0,
            percentage       REAL    NOT NULL,
            amount           REAL    NOT NULL,
            visibility_scope TEXT    NOT NULL DEFAULT 'SELF',
            created_at       TEXT    NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ledger_policy  ON commission_ledger(policy_id);
        CREATE INDEX IF NOT EXISTS idx_ledger_agent   ON commission_ledger(agent_id);
        CREATE INDEX IF NOT EXISTS idx_ledger_source  ON commission_ledger(source_agent_id);

        CREATE TABLE IF NOT EXISTS commission_rules (
            rule_id             TEXT PRIMARY KEY,
            product_id          TEXT REFERENCES products(product_id),
            agent_role          TEXT,
            hierarchy_level     INTEGER NOT NULL DEFAULT 1,
            override_percentage REAL    NOT NULL,
            effective_from      TEXT    NOT NULL,
            effective_to        TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_rules_product ON commission_rules(product_id, hierarchy_level);
    """)

    conn.commit()
    conn.close()
    print(f"Database initialised at: {DB_PATH}")


if __name__ == "__main__":
    init_db()
