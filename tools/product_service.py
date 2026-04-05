"""
product_service.py
------------------
Manages insurance product catalogue for the Insurance Agent Portal.

Data Model:
    Product {
        product_id          : str  (UUID)
        name                : str
        description         : str
        min_premium         : float
        max_premium         : float
        eligibility_criteria: dict  (e.g. {"min_age": 18, "max_age": 65, "min_income": 300000})
        is_active           : bool
        created_at          : str  (ISO datetime)
    }

Note:
    A small seed catalogue is pre-loaded so that the system is usable
    immediately without any setup calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# In-memory store — pre-seeded with sample products
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_products: dict[str, dict[str, Any]] = {}


def _seed_products() -> None:
    """Load a default set of products into the in-memory store."""
    defaults = [
        {
            "name": "Term Life Shield",
            "description": "Pure term life insurance with high sum assured at low premium.",
            "min_premium": 5_000.0,
            "max_premium": 50_000.0,
            "eligibility_criteria": {"min_age": 18, "max_age": 60, "min_income": 200_000},
        },
        {
            "name": "Health Guard Plus",
            "description": "Comprehensive family health insurance with cashless hospitalisation.",
            "min_premium": 8_000.0,
            "max_premium": 40_000.0,
            "eligibility_criteria": {"min_age": 18, "max_age": 65, "min_income": 150_000},
        },
        {
            "name": "Wealth Builder ULIP",
            "description": "Unit-linked insurance plan combining investment and life cover.",
            "min_premium": 25_000.0,
            "max_premium": 500_000.0,
            "eligibility_criteria": {"min_age": 25, "max_age": 55, "min_income": 600_000},
        },
        {
            "name": "Motor Comprehensive",
            "description": "Full comprehensive cover for private vehicles.",
            "min_premium": 3_000.0,
            "max_premium": 30_000.0,
            "eligibility_criteria": {"min_age": 18, "max_age": 70, "min_income": 0},
        },
        {
            "name": "Critical Illness Rider",
            "description": "Lump sum payout on diagnosis of 34 critical illnesses.",
            "min_premium": 4_000.0,
            "max_premium": 20_000.0,
            "eligibility_criteria": {"min_age": 18, "max_age": 55, "min_income": 100_000},
        },
    ]
    for item in defaults:
        product_id = str(uuid.uuid4())
        _products[product_id] = {
            "product_id": product_id,
            "name": item["name"],
            "description": item["description"],
            "min_premium": item["min_premium"],
            "max_premium": item["max_premium"],
            "eligibility_criteria": item["eligibility_criteria"],
            "is_active": True,
            "created_at": _now(),
        }


_seed_products()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_product(product_id: str) -> dict[str, Any]:
    """
    Retrieve a product record by its ID.

    Args:
        product_id: ID of the product to retrieve.

    Returns:
        A copy of the product record.

    Raises:
        KeyError: If product_id is not found.
    """
    if product_id not in _products:
        raise KeyError(f"Product '{product_id}' not found.")
    return dict(_products[product_id])


def list_products(include_inactive: bool = False) -> list[dict[str, Any]]:
    """
    Return all products in the catalogue.

    Args:
        include_inactive: If True, include products with is_active=False.

    Returns:
        List of all product records, sorted by name.
    """
    result = [
        dict(p) for p in _products.values()
        if include_inactive or p["is_active"]
    ]
    return sorted(result, key=lambda p: p["name"])


def filter_products(
    min_premium: float | None = None,
    max_premium: float | None = None,
    eligibility_criteria: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Filter active products by premium range and/or eligibility criteria.

    Eligibility criteria matching is inclusive: a product is included if ALL
    provided criteria keys are satisfied. Supported criteria keys:
        - min_age    : client age >= product.eligibility_criteria["min_age"]
        - max_age    : client age <= product.eligibility_criteria["max_age"]
        - min_income : client income >= product.eligibility_criteria["min_income"]

    Args:
        min_premium:           Include products with max_premium >= min_premium.
        max_premium:           Include products with min_premium <= max_premium.
        eligibility_criteria:  Dict of client attributes to match against
                               each product's eligibility_criteria.

    Returns:
        List of matching active product records.
    """
    results: list[dict[str, Any]] = []

    for product in _products.values():
        if not product["is_active"]:
            continue

        # Premium range filter
        if min_premium is not None and product["max_premium"] < min_premium:
            continue
        if max_premium is not None and product["min_premium"] > max_premium:
            continue

        # Eligibility criteria filter
        if eligibility_criteria:
            criteria = product["eligibility_criteria"]
            client_age = eligibility_criteria.get("age")
            client_income = eligibility_criteria.get("income")

            if client_age is not None:
                if "min_age" in criteria and client_age < criteria["min_age"]:
                    continue
                if "max_age" in criteria and client_age > criteria["max_age"]:
                    continue

            if client_income is not None:
                if "min_income" in criteria and client_income < criteria["min_income"]:
                    continue

        results.append(dict(product))

    return sorted(results, key=lambda p: p["name"])


def check_product_client_fit(product_id: str, client_id: str) -> bool:
    """
    Determine whether a product is eligible for a given client.

    Eligibility is evaluated against the client's financial_profile stored
    in the client_service. This function imports client_service at call time
    to avoid circular imports.

    Criteria checked:
        - Client age is within product's [min_age, max_age] band.
        - Client income meets product's min_income threshold.
        - Product is active.

    Args:
        product_id: ID of the product to check.
        client_id:  ID of the client to evaluate.

    Returns:
        True if the client meets all eligibility criteria, False otherwise.

    Raises:
        KeyError: If product_id or client_id is not found.
    """
    # Lazy import to avoid circular dependency
    from tools.client_service import get_client  # type: ignore[import]

    product = get_product(product_id)
    client = get_client(client_id)

    if not product["is_active"]:
        return False

    profile = client.get("financial_profile", {})
    criteria = product["eligibility_criteria"]

    client_age = profile.get("age")
    client_income = profile.get("income")

    if client_age is not None:
        if "min_age" in criteria and client_age < criteria["min_age"]:
            return False
        if "max_age" in criteria and client_age > criteria["max_age"]:
            return False

    if client_income is not None:
        if "min_income" in criteria and client_income < criteria["min_income"]:
            return False

    return True


def add_product(
    name: str,
    description: str,
    min_premium: float,
    max_premium: float,
    eligibility_criteria: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Add a new product to the catalogue.

    Args:
        name:                   Product name.
        description:            Short description.
        min_premium:            Minimum premium amount.
        max_premium:            Maximum premium amount.
        eligibility_criteria:   Dict of eligibility rules.

    Returns:
        The newly created product record.

    Raises:
        ValueError: If min_premium > max_premium or name is empty.
    """
    if not name:
        raise ValueError("Product name cannot be empty.")
    if min_premium > max_premium:
        raise ValueError("min_premium cannot be greater than max_premium.")

    product_id = str(uuid.uuid4())
    product: dict[str, Any] = {
        "product_id": product_id,
        "name": name.strip(),
        "description": description.strip(),
        "min_premium": float(min_premium),
        "max_premium": float(max_premium),
        "eligibility_criteria": eligibility_criteria or {},
        "is_active": True,
        "created_at": _now(),
    }

    _products[product_id] = product
    return dict(product)
