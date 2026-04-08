"""
state_manager.py
-----------------
Manages underwriting application lifecycle state with DB persistence.

State Model (WAT Framework v3):
  CREATED → IN_PROGRESS → DATA_ENRICHED → RISK_CLASSIFIED → DECISIONED
                                                               ↓        ↓        ↓
                                                          APPROVED  REJECTED  PENDED
                                                               ↓
                                                            ISSUED

No implicit transitions — every state change must be explicit.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "CREATED":          ["IN_PROGRESS"],
    "IN_PROGRESS":      ["DATA_ENRICHED", "PENDED"],
    "DATA_ENRICHED":    ["RISK_CLASSIFIED", "PENDED"],
    "RISK_CLASSIFIED":  ["DECISIONED", "PENDED"],
    "DECISIONED":       ["APPROVED", "APPROVED_WITH_CONDITIONS", "REJECTED", "PENDED"],
    "APPROVED":         ["ISSUED"],
    "APPROVED_WITH_CONDITIONS": ["ISSUED", "PENDED"],
    "PENDED":           ["IN_PROGRESS"],   # Re-trigger after requirements fulfilled
    "REJECTED":         [],
    "ISSUED":           [],
}

# Terminal states — no further transitions
_TERMINAL_STATES = {"REJECTED", "ISSUED"}

# All valid states
ALL_STATES = set(_ALLOWED_TRANSITIONS.keys())


class StateError(Exception):
    """Raised when an invalid state transition is attempted."""


class StateManager:
    """
    Manages lifecycle state for underwriting applications.

    Combines in-memory cache with DB persistence.
    Every transition is validated and logged.
    """

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}  # application_id → state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_state(self, application_id: str) -> Optional[str]:
        """Return current state for an application (checks DB if not cached)."""
        if application_id in self._cache:
            return self._cache[application_id]

        from database import get_db, row_to_dict
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT state FROM underwriting_applications WHERE application_id = ?",
                (application_id,)
            ).fetchone()
            if row:
                state = row["state"]
                self._cache[application_id] = state
                return state
            return None
        finally:
            conn.close()

    def set_state(self, application_id: str, state: str) -> str:
        """
        Force-set a state without transition validation.
        Use only for initial creation (CREATED).
        """
        if state not in ALL_STATES:
            raise StateError(f"Unknown state '{state}'. Valid: {sorted(ALL_STATES)}")

        self._persist(application_id, state)
        self._cache[application_id] = state
        return state

    def transition(self, application_id: str, new_state: str) -> str:
        """
        Transition an application to a new state.

        Validates the transition is allowed, persists to DB,
        and logs the change to underwriting_audit_logs.

        Raises:
            StateError: If the transition is not allowed.
        """
        current = self.get_state(application_id)
        if current is None:
            raise StateError(f"Application '{application_id}' not found.")

        if new_state not in ALL_STATES:
            raise StateError(f"Unknown target state '{new_state}'. Valid: {sorted(ALL_STATES)}")

        allowed = _ALLOWED_TRANSITIONS.get(current, [])
        if new_state not in allowed:
            raise StateError(
                f"Invalid transition for '{application_id}': "
                f"'{current}' → '{new_state}'. "
                f"Allowed from '{current}': {allowed}"
            )

        self._persist(application_id, new_state)
        self._log_transition(application_id, current, new_state)
        self._cache[application_id] = new_state
        return new_state

    def can_transition(self, application_id: str, new_state: str) -> bool:
        """Check if a transition is valid without executing it."""
        current = self.get_state(application_id)
        if current is None:
            return False
        return new_state in _ALLOWED_TRANSITIONS.get(current, [])

    def get_allowed_transitions(self, application_id: str) -> list[str]:
        """Return all valid next states for an application."""
        current = self.get_state(application_id)
        if current is None:
            return []
        return _ALLOWED_TRANSITIONS.get(current, [])

    def is_terminal(self, application_id: str) -> bool:
        """Return True if the application is in a terminal state."""
        current = self.get_state(application_id)
        return current in _TERMINAL_STATES

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _persist(self, application_id: str, state: str) -> None:
        """Write state to the DB."""
        from database import get_db
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db()
        try:
            conn.execute(
                "UPDATE underwriting_applications SET state = ?, updated_at = ? WHERE application_id = ?",
                (state, now, application_id)
            )
            conn.commit()
        finally:
            conn.close()

    def _log_transition(self, application_id: str, from_state: str, to_state: str) -> None:
        """Log state transition to underwriting_audit_logs."""
        import uuid
        from database import get_db
        now = datetime.now(timezone.utc).isoformat()
        log_id = str(uuid.uuid4())
        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO underwriting_audit_logs
                   (log_id, application_id, input, tool_called, prompt_version,
                    output, validation_status, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    log_id,
                    application_id,
                    json.dumps({"from_state": from_state}),
                    "StateManager.transition",
                    None,
                    json.dumps({"to_state": to_state}),
                    "VALID",
                    now,
                )
            )
            conn.commit()
        finally:
            conn.close()


# Module-level singleton
_state_manager = StateManager()


def get_state_manager() -> StateManager:
    """Return the shared StateManager instance."""
    return _state_manager
