"""
commission_engine.py
--------------------
Calculates and records agent commission entries for the Insurance Agent Portal.

Data Model:
    CommissionConfig {
        product_id   : str
        rate_percent : float   (e.g. 10.0 = 10%)
        updated_at   : str
    }

    CommissionRecord {
        commission_id : str   (UUID)
        policy_id     : str
        event_type    : str   ("sale" | "renewal")
        amount        : float
        rate_percent  : float  (snapshot of rate at time of recording)
        premium       : float  (snapshot of premium at time of recording)
        agent_id      : str | None
        recorded_at   : str   (ISO datetime)
    }
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_commission_configs: dict[str, dict[str, Any]] = {}   # keyed by product_id
_commission_records: dict[str, dict[str, Any]] = {}   # keyed by commission_id

VALID_EVENT_TYPES: set[str] = {"sale", "renewal"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Configuration API
# ---------------------------------------------------------------------------

def set_commission_config(product_id: str, rate_percent: float) -> dict[str, Any]:
    """
    Set or update the commission rate for a product.

    Args:
        product_id:   ID of the product to configure.
        rate_percent: Commission rate as a percentage (e.g. 10.0 = 10%).
                      Must be between 0 and 100 inclusive.

    Returns:
        The commission config record.

    Raises:
        ValueError: If product_id is empty or rate_percent is out of range.
    """
    if not product_id:
        raise ValueError("product_id is required.")
    if not (0.0 <= rate_percent <= 100.0):
        raise ValueError(
            f"rate_percent must be between 0 and 100, got {rate_percent}."
        )

    config: dict[str, Any] = {
        "product_id": product_id,
        "rate_percent": float(rate_percent),
        "updated_at": _now(),
    }
    _commission_configs[product_id] = config
    return dict(config)


def get_commission_config(product_id: str) -> dict[str, Any]:
    """
    Retrieve the commission configuration for a product.

    Args:
        product_id: ID of the product.

    Returns:
        The commission config record.

    Raises:
        KeyError: If no config exists for the given product_id.
    """
    if product_id not in _commission_configs:
        raise KeyError(
            f"No commission configuration found for product '{product_id}'. "
            "Use set_commission_config() to define one."
        )
    return dict(_commission_configs[product_id])


# ---------------------------------------------------------------------------
# Calculation & Recording API
# ---------------------------------------------------------------------------

def calculate_commission(policy_id: str) -> float:
    """
    Calculate the commission amount for a policy based on its premium and
    the configured rate for its product.

    Formula: commission = (premium × rate_percent) / 100

    Args:
        policy_id: ID of the policy to calculate commission for.

    Returns:
        Calculated commission amount as a float, rounded to 2 decimal places.

    Raises:
        KeyError:   If policy is not found or no commission config exists
                    for the policy's product.
        ValueError: If policy premium is zero or negative.
    """
    from tools.policy_service import get_policy  # type: ignore[import]

    policy = get_policy(policy_id)
    product_id = policy["product_id"]
    premium = policy["premium"]

    if premium <= 0:
        raise ValueError(
            f"Policy '{policy_id}' has a non-positive premium ({premium}). "
            "Cannot calculate commission."
        )

    config = get_commission_config(product_id)
    rate = config["rate_percent"]

    commission_amount = round((premium * rate) / 100.0, 2)
    return commission_amount


def record_commission(
    policy_id: str,
    event_type: str,
    amount: float,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """
    Persist a commission entry for a policy event.

    Args:
        policy_id:   ID of the policy that generated the commission.
        event_type:  Type of event: "sale" or "renewal".
        amount:      Commission amount to record (must be >= 0).
        agent_id:    Optional agent identifier for multi-agent scenarios.

    Returns:
        The newly created commission record.

    Raises:
        ValueError: If event_type is invalid or amount is negative.
        KeyError:   If policy_id is not found.
    """
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(
            f"Invalid event_type '{event_type}'. Must be one of: {sorted(VALID_EVENT_TYPES)}"
        )
    if amount < 0:
        raise ValueError(f"Commission amount cannot be negative, got {amount}.")

    from tools.policy_service import get_policy  # type: ignore[import]

    policy = get_policy(policy_id)
    product_id = policy["product_id"]
    premium = policy["premium"]

    # Snapshot the rate at time of recording (best-effort; may not exist)
    rate_snapshot = 0.0
    try:
        config = get_commission_config(product_id)
        rate_snapshot = config["rate_percent"]
    except KeyError:
        pass  # Rate may have been deleted; record the amount as-is

    commission_id = str(uuid.uuid4())
    record: dict[str, Any] = {
        "commission_id": commission_id,
        "policy_id": policy_id,
        "product_id": product_id,
        "event_type": event_type,
        "amount": float(amount),
        "rate_percent": rate_snapshot,
        "premium": float(premium),
        "agent_id": agent_id,
        "recorded_at": _now(),
    }

    _commission_records[commission_id] = record
    return dict(record)


def get_commissions_by_policy(policy_id: str) -> list[dict[str, Any]]:
    """
    Return all commission records linked to a specific policy.

    Args:
        policy_id: ID of the policy.

    Returns:
        List of commission records sorted by recorded_at ascending.
    """
    if not policy_id:
        raise ValueError("policy_id is required.")

    result = [
        dict(r) for r in _commission_records.values()
        if r["policy_id"] == policy_id
    ]
    return sorted(result, key=lambda r: r["recorded_at"])


def get_agent_earnings(agent_id: str | None = None) -> dict[str, Any]:
    """
    Summarise commission earnings, optionally filtered by agent.

    Args:
        agent_id: If provided, filter to records belonging to this agent.
                  If None, aggregate across all agents/records.

    Returns:
        A summary dict containing:
            total_earnings  : float — total commission across all events
            sale_earnings   : float — commission from sale events only
            renewal_earnings: float — commission from renewal events only
            record_count    : int   — number of commission records included
            by_policy       : dict  — {policy_id: total_amount} breakdown
            agent_id        : str | None — the agent filter applied
    """
    records = [
        r for r in _commission_records.values()
        if agent_id is None or r.get("agent_id") == agent_id
    ]

    total = 0.0
    sale_total = 0.0
    renewal_total = 0.0
    by_policy: dict[str, float] = {}

    for r in records:
        amount = r["amount"]
        total += amount
        if r["event_type"] == "sale":
            sale_total += amount
        elif r["event_type"] == "renewal":
            renewal_total += amount

        pid = r["policy_id"]
        by_policy[pid] = round(by_policy.get(pid, 0.0) + amount, 2)

    return {
        "agent_id": agent_id,
        "total_earnings": round(total, 2),
        "sale_earnings": round(sale_total, 2),
        "renewal_earnings": round(renewal_total, 2),
        "record_count": len(records),
        "by_policy": by_policy,
    }
