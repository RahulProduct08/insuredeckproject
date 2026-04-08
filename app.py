"""app.py — Flask entry point for InsureDesk."""

import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

from database import init_db, get_db
from routes.clients import clients_bp
from routes.products import products_bp
from routes.policies import policies_bp
from routes.commissions import commissions_bp
from routes.activities import activities_bp
from routes.auth import auth_bp
from routes.agents import agents_bp
from routes.tasks import tasks_bp
from routes.analytics import analytics_bp
from routes.needs_analysis import needs_bp
from routes.hierarchy import hierarchy_bp
from routes.underwriting import underwriting_bp

# ── Startup ────────────────────────────────────────────────────────────────
init_db()

db = get_db()
_count = db.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
db.close()
if _count == 0:
    from seed import seed as run_seed
    run_seed()

# ── App ────────────────────────────────────────────────────────────────────
DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

app = Flask(__name__, static_folder=DIST, static_url_path="")
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "https://insuredeck.onrender.com"])

app.register_blueprint(clients_bp,     url_prefix="/api")
app.register_blueprint(products_bp,    url_prefix="/api")
app.register_blueprint(policies_bp,    url_prefix="/api")
app.register_blueprint(commissions_bp, url_prefix="/api")
app.register_blueprint(activities_bp,  url_prefix="/api")
app.register_blueprint(auth_bp)
app.register_blueprint(agents_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(needs_bp)
app.register_blueprint(hierarchy_bp)
app.register_blueprint(underwriting_bp, url_prefix="/api")


@app.route("/api/health")
def health():
    return {"status": "ok", "service": "InsureDesk API v2"}


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    file_path = os.path.join(DIST, path)
    if path and os.path.exists(file_path):
        return send_from_directory(DIST, path)
    return send_from_directory(DIST, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("RENDER") is None
    app.run(host="0.0.0.0", port=port, debug=debug)
