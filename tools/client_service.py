"""
client_service.py
-----------------
Manages client records for the Insurance Agent Portal.

Data Model:
    Client {
        client_id   : str  (UUID)
        name        : str
        phone       : str
        email       : str
        financial_profile : dict
        stage       : str  (Lead | Qualified | Proposal | Negotiation | Closed)
        created_at  : str  (ISO datetime)
        updated_at  : str  (ISO datetime)
        is_active   : bool
    }
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_clients: dict[str, dict[str, Any]] = {}

# Valid pipeline stages in order
PIPELINE_STAGES: list[str] = [
    "Lead",
    "Qualified",
    "Proposal",
    "Negotiation",
    "Closed",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _validate_stage(stage: str) -> None:
    """Raise ValueError if stage is not a recognised pipeline stage."""
    if stage not in PIPELINE_STAGES:
        raise ValueError(
            f"Invalid stage '{stage}'. Must be one of: {PIPELINE_STAGES}"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_client(
    name: str,
    phone: str,
    email: str,
    financial_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a new client record with stage = 'Lead'.

    Args:
        name:               Full name of the client.
        phone:              Contact phone number.
        email:              Contact email address.
        financial_profile:  Optional dict containing income, age, dependents,
                            risk_appetite, existing_policies, etc.

    Returns:
        The newly created client record.

    Raises:
        ValueError: If name, phone, or email is empty.
    """
    if not name or not phone or not email:
        raise ValueError("name, phone, and email are required to create a client.")

    client_id = str(uuid.uuid4())
    now = _now()

    client: dict[str, Any] = {
        "client_id": client_id,
        "name": name.strip(),
        "phone": phone.strip(),
        "email": email.strip().lower(),
        "financial_profile": financial_profile or {},
        "stage": "Lead",
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }

    _clients[client_id] = client
    return dict(client)


def update_client(client_id: str, **updates: Any) -> dict[str, Any]:
    """
    Update one or more fields on an existing client record.

    Protected fields (client_id, created_at) cannot be overwritten.

    Args:
        client_id:  ID of the client to update.
        **updates:  Keyword arguments of fields to update.

    Returns:
        The updated client record.

    Raises:
        KeyError:   If client_id is not found.
        ValueError: If an attempt is made to modify a protected field.
    """
    if client_id not in _clients:
        raise KeyError(f"Client '{client_id}' not found.")

    protected = {"client_id", "created_at"}
    for key in updates:
        if key in protected:
            raise ValueError(f"Field '{key}' is protected and cannot be updated.")

    # Validate stage if being updated
    if "stage" in updates:
        _validate_stage(updates["stage"])

    client = _clients[client_id]
    client.update(updates)
    client["updated_at"] = _now()

    return dict(client)


def get_client(client_id: str) -> dict[str, Any]:
    """
    Retrieve a client record by its ID.

    Args:
        client_id:  ID of the client to retrieve.

    Returns:
        A copy of the client record.

    Raises:
        KeyError: If client_id is not found.
    """
    if client_id not in _clients:
        raise KeyError(f"Client '{client_id}' not found.")
    return dict(_clients[client_id])


def search_clients(
    name: str | None = None,
    phone: str | None = None,
    stage: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search clients by name (partial, case-insensitive), phone, or stage.

    At least one filter must be provided. Multiple filters are ANDed together.

    Args:
        name:   Partial name string to search for.
        phone:  Exact phone number to match.
        stage:  Pipeline stage to filter by.

    Returns:
        List of matching client records.

    Raises:
        ValueError: If no search criteria are provided.
    """
    if name is None and phone is None and stage is None:
        raise ValueError("At least one search criterion must be provided.")

    if stage is not None:
        _validate_stage(stage)

    results: list[dict[str, Any]] = []
    for client in _clients.values():
        if name is not None and name.lower() not in client["name"].lower():
            continue
        if phone is not None and client["phone"] != phone.strip():
            continue
        if stage is not None and client["stage"] != stage:
            continue
        results.append(dict(client))

    return results


def assign_pipeline_stage(client_id: str, stage: str) -> dict[str, Any]:
    """
    Move a client to a specified pipeline stage.

    Valid stages (in order): Lead → Qualified → Proposal → Negotiation → Closed

    Args:
        client_id:  ID of the client.
        stage:      Target pipeline stage.

    Returns:
        The updated client record.

    Raises:
        KeyError:   If client_id is not found.
        ValueError: If stage is not a valid pipeline stage.
    """
    _validate_stage(stage)

    if client_id not in _clients:
        raise KeyError(f"Client '{client_id}' not found.")

    client = _clients[client_id]
    client["stage"] = stage
    client["updated_at"] = _now()

    return dict(client)


def merge_clients(primary_id: str, duplicate_id: str) -> dict[str, Any]:
    """
    Merge a duplicate client record into the primary record.

    The primary record is retained and enriched with any non-empty fields
    from the duplicate. The duplicate record is deactivated (is_active=False).

    Args:
        primary_id:    ID of the primary (surviving) client record.
        duplicate_id:  ID of the duplicate client record to merge and deactivate.

    Returns:
        The updated primary client record.

    Raises:
        KeyError:   If either client_id is not found.
        ValueError: If primary_id and duplicate_id are the same.
    """
    if primary_id == duplicate_id:
        raise ValueError("primary_id and duplicate_id must be different.")

    if primary_id not in _clients:
        raise KeyError(f"Primary client '{primary_id}' not found.")
    if duplicate_id not in _clients:
        raise KeyError(f"Duplicate client '{duplicate_id}' not found.")

    primary = _clients[primary_id]
    duplicate = _clients[duplicate_id]

    # Enrich primary with non-empty fields from duplicate (do not overwrite existing data)
    mergeable_fields = ["phone", "email", "financial_profile"]
    for field in mergeable_fields:
        if not primary.get(field) and duplicate.get(field):
            primary[field] = duplicate[field]

    # Merge financial_profile dicts if both exist
    if duplicate.get("financial_profile") and isinstance(primary.get("financial_profile"), dict):
        merged_profile = {**duplicate["financial_profile"], **primary["financial_profile"]}
        primary["financial_profile"] = merged_profile

    # Deactivate the duplicate
    duplicate["is_active"] = False
    duplicate["updated_at"] = _now()
    duplicate["merged_into"] = primary_id

    primary["updated_at"] = _now()
    primary["merged_from"] = primary.get("merged_from", [])
    if isinstance(primary["merged_from"], list):
        primary["merged_from"].append(duplicate_id)

    return dict(primary)
