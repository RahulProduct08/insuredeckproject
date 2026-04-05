"""
app.py
------
Flask application entry point for the Insurance Agent Portal.

In production (Render): serves both the REST API and the React static build.
In development: API only (Vite dev server proxies /api/* here).
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from database import init_db
from routes.clients import clients_bp
from routes.products import products_bp
from routes.policies import policies_bp
from routes.commissions import commissions_bp
from routes.activities import activities_bp

# Path to the React production build
DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

app = Flask(__name__, static_folder=DIST, static_url_path="")
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

# Register all blueprints
app.register_blueprint(clients_bp,    url_prefix="/api")
app.register_blueprint(products_bp,   url_prefix="/api")
app.register_blueprint(policies_bp,   url_prefix="/api")
app.register_blueprint(commissions_bp,url_prefix="/api")
app.register_blueprint(activities_bp, url_prefix="/api")


@app.route("/api/health")
def health():
    return {"status": "ok", "service": "Insurance Agent Portal API"}


# Serve React for all non-API routes (SPA fallback)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    file_path = os.path.join(DIST, path)
    if path and os.path.exists(file_path):
        return send_from_directory(DIST, path)
    return send_from_directory(DIST, "index.html")


if __name__ == "__main__":
    init_db()

    # Auto-seed on first run (empty database)
    from database import get_db
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    db.close()
    if count == 0:
        import seed  # noqa: F401

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("RENDER") is None  # no debug in production
    app.run(host="0.0.0.0", port=port, debug=debug)
