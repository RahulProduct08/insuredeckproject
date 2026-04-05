"""
policy_service.py
-----------------
Manages insurance policy records for the Insurance Agent Portal.

Data Model:
    Policy {
        policy_id           : str   (UUID)
        client_id           : str
        product_id          : str
        premium             : float
        status              : str   (Draft | Submitted | Underwriting | Approved | Issued | Rejected)
        documents_checklist : list[str]
        documents_attached  : list[str]
        created_at          : str   (ISO datetime)
        updated_at          : str   (ISO datetime)
        status_history      : list[dict]   — each entry: {from, to, timestamp}
    }

Valid Status Transitions:
    Draft         → Submitted
    Submitted     → Underwriting
    Underwriting  → Approved | Rejected
    Approved      → Issued
    Rejected      → (terminal — agent must create a new policy)
    Issued        → (terminal within this service; renewal handled externally)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_policies: dict[str, dict[str, Any]] = {}

# Allowed status values
POLICY_STATUSES: list[str] = [
    "Draft",
    "Submitted",
    "Underwriting",
    "Approved",
    "Issued",
    "Rejected",
]

# Valid forward transitions
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "Draft":        ["Submitted"],
    "Submitted":    ["Underwriting"],
    "Underwriting": ["Approved", "Rejected"],
    "Approved":     ["Issued"],
    "Issued":       [],          # terminal (renewals are new events)
    "Rejected":     [],          # terminal within same policy
}

DEFAULT_DOCUMENTS_CHECKLIST: list[str] = [
    "ID Proof",
    "Income Proof",
    "Medical Report",
    "Signed Proposal Form",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _validate_status(status: str) -> None:
    """Raise ValueError if status is not a recognised policy status."""
    if status not in POLICY_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {POLICY_STATUSES}"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_policy(
    client_id: str,
    product_id: str,
    premium: float,
    documents_checklist: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a new policy record with status = 'Draft'.

    Args:
        client_id:           ID of the client who owns the policy.
        product_id:          ID of the insurance product.
        premium:             Agreed premium amount (must be > 0).
        documents_checklist: Optional list of required document names.
                             Defaults to DEFAULT_DOCUMENTS_CHECKLIST.

    Returns:
        The newly created policy record.

    Raises:
        ValueError: If premium is not positive or required IDs are missing.
    """
    if not client_id:
        raise ValueError("client_id is required.")
    if not product_id:
        raise ValueError("product_id is required.")
    if premium <= 0:
        raise ValueError(f"premium must be positive, got {premium}.")

    policy_id = str(uuid.uuid4())
    now = _now()

    policy: dict[str, Any] = {
        "policy_id": policy_id,
        "client_id": client_id,
        "product_id": product_id,
        "premium": float(premium),
        "status": "Draft",
        "documents_checklist": documents_checklist or list(DEFAULT_DOCUMENTS_CHECKLIST),
        "documents_attached": [],
        "created_at": now,
        "updated_at": now,
        "status_history": [
            {"from": None, "to": "Draft", "timestamp": now}
        ],
    }

    _policies[policy_id] = policy
    return dict(policy)


def update_policy_status(policy_id: str, new_status: str) -> dict[str, Any]:
    """
    Advance a policy to the next valid status.

    Validates the transition against the allowed state machine before applying.

    Args:
        policy_id:   ID of the policy to update.
        new_status:  Target status string.

    Returns:
        The updated policy record.

    Raises:
        KeyError:   If policy_id is not found.
        ValueError: If the requested transition is not permitted.
    """
    _validate_status(new_status)

    if policy_id not in _policies:
        raise KeyError(f"Policy '{policy_id}' not found.")

    policy = _policies[policy_id]
    current_status = policy["status"]
    allowed_next = _VALID_TRANSITIONS.get(current_status, [])

    if new_status not in allowed_next:
        raise ValueError(
            f"Invalid transition: '{current_status}' → '{new_status}'. "
            f"Allowed next states from '{current_status}': {allowed_next or ['(none — terminal state)']}"
        )

    now = _now()
    policy["status_history"].append({
        "from": current_status,
        "to": new_status,
        "timestamp": now,
    })
    policy["status"] = new_status
    policy["updated_at"] = now

    return dict(policy)


def get_policy(policy_id: str) -> dict[str, Any]:
    """
    Retrieve a policy record by its ID.

    Args:
        policy_id: ID of the policy to retrieve.

    Returns:
        A copy of the policy record.

    Raises:
        KeyError: If policy_id is not found.
    """
    if policy_id not in _policies:
        raise KeyError(f"Policy '{policy_id}' not found.")
    return dict(_policies[policy_id])


def get_policies_by_client(client_id: str) -> list[dict[str, Any]]:
    """
    Return all policies belonging to a given client.

    Args:
        client_id: ID of the client.

    Returns:
        List of policy records, sorted by creation date (newest first).
    """
    result = [
        dict(p) for p in _policies.values()
        if p["client_id"] == client_id
    ]
    return sorted(result, key=lambda p: p["created_at"], reverse=True)


def attach_documents(policy_id: str, documents: list[str]) -> dict[str, Any]:
    """
    Mark documents as attached to a policy.

    Only attaches documents that are present in the policy's checklist.
    Returns the updated policy with 'documents_attached' updated.

    Args:
        policy_id:  ID of the policy.
        documents:  List of document names to mark as attached.

    Returns:
        The updated policy record.

    Raises:
        KeyError:   If policy_id is not found.
        ValueError: If documents list is empty.
    """
    if not documents:
        raise ValueError("documents list cannot be empty.")

    if policy_id not in _policies:
        raise KeyError(f"Policy '{policy_id}' not found.")

    policy = _policies[policy_id]
    checklist = set(policy["documents_checklist"])
    existing_attached = set(policy["documents_attached"])

    newly_attached = []
    unrecognised = []

    for doc in documents:
        if doc in checklist:
            if doc not in existing_attached:
                newly_attached.append(doc)
        else:
            unrecognised.append(doc)

    policy["documents_attached"].extend(newly_attached)
    policy["updated_at"] = _now()

    # Surface unrecognised docs as a warning in the record
    if unrecognised:
        policy.setdefault("warnings", []).append(
            f"Documents not in checklist (ignored): {unrecognised}"
        )

    return dict(policy)
