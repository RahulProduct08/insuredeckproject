"""
activity_logger.py
------------------
Records and retrieves activity events across clients and policies
for the Insurance Agent Portal.

Data Model:
    Activity {
        activity_id   : str   (UUID)
        client_id     : str
        activity_type : str   (see ACTIVITY_TYPES)
        description   : str
        policy_id     : str | None
        timestamp     : str   (ISO datetime)
        metadata      : dict  (optional extra data)
    }

Supported activity_type values:
    follow_up             — Scheduled or completed follow-up contact
    policy_created        — A new policy record was created
    status_change         — A policy status transition occurred
    commission_recorded   — A commission entry was logged
    servicing             — Post-sale servicing interaction
    renewal_alert         — Policy renewal is approaching
    upsell_opportunity    — A new product opportunity was identified
    lapse_alert           — Policy has lapsed without renewal
    document_update       — Policy documents were updated
    claim_assistance      — Agent assisted with claim filing
    note                  — General freeform note
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_activities: dict[str, dict[str, Any]] = {}

ACTIVITY_TYPES: set[str] = {
    "follow_up",
    "policy_created",
    "status_change",
    "commission_recorded",
    "servicing",
    "renewal_alert",
    "upsell_opportunity",
    "lapse_alert",
    "document_update",
    "claim_assistance",
    "note",
    "policy_transition",   # internal — used by log_policy_transition
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_activity(
    client_id: str,
    activity_type: str,
    description: str,
    policy_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Record a new activity event for a client.

    Args:
        client_id:      ID of the client this activity belongs to.
        activity_type:  Category of the activity (see ACTIVITY_TYPES).
        description:    Human-readable description of what occurred.
        policy_id:      Optional ID of the related policy.
        metadata:       Optional dict for additional structured data.

    Returns:
        The newly created activity record.

    Raises:
        ValueError: If client_id, activity_type, or description is missing,
                    or if activity_type is not recognised.
    """
    if not client_id:
        raise ValueError("client_id is required.")
    if not description:
        raise ValueError("description is required.")
    if activity_type not in ACTIVITY_TYPES:
        raise ValueError(
            f"Unknown activity_type '{activity_type}'. "
            f"Valid types: {sorted(ACTIVITY_TYPES)}"
        )

    activity_id = str(uuid.uuid4())
    activity: dict[str, Any] = {
        "activity_id": activity_id,
        "client_id": client_id,
        "activity_type": activity_type,
        "description": description.strip(),
        "policy_id": policy_id,
        "timestamp": _now(),
        "metadata": metadata or {},
    }

    _activities[activity_id] = activity
    return dict(activity)


def get_client_timeline(client_id: str) -> list[dict[str, Any]]:
    """
    Return all activity records for a given client, in chronological order.

    Args:
        client_id: ID of the client whose timeline to retrieve.

    Returns:
        List of activity records sorted by timestamp ascending.
    """
    if not client_id:
        raise ValueError("client_id is required.")

    result = [
        dict(a) for a in _activities.values()
        if a["client_id"] == client_id
    ]
    return sorted(result, key=lambda a: a["timestamp"])


def log_policy_transition(
    policy_id: str,
    from_status: str,
    to_status: str,
    client_id: str | None = None,
) -> dict[str, Any]:
    """
    Record a policy status transition as a specialised activity event.

    This is a convenience wrapper around log_activity for policy state changes.
    Looks up the client_id from the policy_service if not provided.

    Args:
        policy_id:    ID of the policy that transitioned.
        from_status:  The previous policy status.
        to_status:    The new policy status.
        client_id:    Optional client ID. If omitted, resolved from policy record.

    Returns:
        The newly created activity record.

    Raises:
        ValueError: If policy_id is missing.
        KeyError:   If client_id cannot be resolved.
    """
    if not policy_id:
        raise ValueError("policy_id is required.")

    resolved_client_id = client_id

    if resolved_client_id is None:
        # Lazy import to avoid circular dependency at module load
        from tools.policy_service import get_policy  # type: ignore[import]
        policy = get_policy(policy_id)
        resolved_client_id = policy["client_id"]

    description = (
        f"Policy status changed: '{from_status}' → '{to_status}'."
    )

    return log_activity(
        client_id=resolved_client_id,
        activity_type="policy_transition",
        description=description,
        policy_id=policy_id,
        metadata={
            "from_status": from_status,
            "to_status": to_status,
        },
    )


def get_policy_activities(policy_id: str) -> list[dict[str, Any]]:
    """
    Return all activity records linked to a specific policy.

    Args:
        policy_id: ID of the policy to filter activities by.

    Returns:
        List of activity records sorted by timestamp ascending.
    """
    if not policy_id:
        raise ValueError("policy_id is required.")

    result = [
        dict(a) for a in _activities.values()
        if a.get("policy_id") == policy_id
    ]
    return sorted(result, key=lambda a: a["timestamp"])


def get_all_activities() -> list[dict[str, Any]]:
    """
    Return all recorded activity events, sorted by timestamp ascending.

    Returns:
        Full list of activity records across all clients and policies.
    """
    return sorted(
        (dict(a) for a in _activities.values()),
        key=lambda a: a["timestamp"],
    )
