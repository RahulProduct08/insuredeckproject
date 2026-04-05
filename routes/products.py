"""
routes/products.py
------------------
Product catalog CRUD.

Endpoints:
    GET    /api/products            list with optional ?is_active=
    POST   /api/products            create
    GET    /api/products/<id>       detail
    PUT    /api/products/<id>       update
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from database import get_db, row_to_dict

products_bp = Blueprint("products", __name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# GET /api/products
# ---------------------------------------------------------------------------
@products_bp.route("/products", methods=["GET"])
def list_products():
    is_active = request.args.get("is_active")

    query = "SELECT * FROM products WHERE 1=1"
    params: list = []

    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active.lower() in ("1", "true") else 0)

    query += " ORDER BY name ASC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([row_to_dict(r) for r in rows])


# ---------------------------------------------------------------------------
# POST /api/products
# ---------------------------------------------------------------------------
@products_bp.route("/products", methods=["POST"])
def create_product():
    body = request.get_json(force=True) or {}

    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    min_p = body.get("min_premium")
    max_p = body.get("max_premium")
    if min_p is None or max_p is None:
        return jsonify({"error": "min_premium and max_premium are required"}), 400

    product_id = str(uuid.uuid4())
    now = _utcnow()

    db = get_db()
    db.execute("""
        INSERT INTO products
          (product_id, name, description, min_premium, max_premium,
           min_age, max_age, min_income, commission_rate_percent, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, [
        product_id, name,
        body.get("description", ""),
        float(min_p), float(max_p),
        body.get("min_age", 0), body.get("max_age", 100),
        body.get("min_income", 0.0),
        body.get("commission_rate_percent", 10.0),
        now,
    ])
    db.commit()

    row = db.execute("SELECT * FROM products WHERE product_id=?", [product_id]).fetchone()
    db.close()
    return jsonify(row_to_dict(row)), 201


# ---------------------------------------------------------------------------
# GET /api/products/<id>
# ---------------------------------------------------------------------------
@products_bp.route("/products/<product_id>", methods=["GET"])
def get_product(product_id: str):
    db = get_db()
    row = db.execute("SELECT * FROM products WHERE product_id=?", [product_id]).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(row_to_dict(row))


# ---------------------------------------------------------------------------
# PUT /api/products/<id>
# ---------------------------------------------------------------------------
@products_bp.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id: str):
    db = get_db()
    existing = db.execute("SELECT * FROM products WHERE product_id=?", [product_id]).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "Product not found"}), 404

    body = request.get_json(force=True) or {}
    allowed = ["name", "description", "min_premium", "max_premium",
               "min_age", "max_age", "min_income", "commission_rate_percent", "is_active"]

    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        db.close()
        return jsonify(row_to_dict(existing))

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [product_id]

    db.execute(f"UPDATE products SET {set_clause} WHERE product_id = ?", values)
    db.commit()

    row = db.execute("SELECT * FROM products WHERE product_id=?", [product_id]).fetchone()
    db.close()
    return jsonify(row_to_dict(row))
