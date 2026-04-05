# Insurance Agent Portal — Setup & Run Guide

## Prerequisites (install once)

### 1. Python 3.10+
Download from https://www.python.org/downloads/ — **check "Add Python to PATH"** during install.

### 2. Node.js 18+
Download from https://nodejs.org/ — choose the LTS version.

---

## First-Time Setup

Open a terminal in this project folder (`Test Claude`), then run:

```bash
# Install Python dependencies
pip install flask flask-cors

# Initialize the database (creates insurance_portal.db)
python database.py

# Seed with test data (10 clients, 5 products, 9 policies, commissions)
python seed.py

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## Run the Application

You need **two terminal windows** open in this project folder.

### Terminal 1 — Backend (Flask API)
```bash
python app.py
```
Runs on http://localhost:5000

### Terminal 2 — Frontend (React)
```bash
cd frontend
npm run dev
```
Runs on http://localhost:5173

**Open http://localhost:5173 in your browser.**

---

## What's Included

| Route | Page |
|---|---|
| `/pipeline` | Kanban board — drag clients between Lead → Qualified → Proposal → Closed |
| `/clients` | Client list with inline detail panel |
| `/clients/:id` | Client 360 — profile, policies, activity timeline |
| `/products` | Product catalog with edit |
| `/applications` | In-progress policies with status advance buttons |
| `/policies` | All issued (active) policies |
| `/renewals` | Policies due for renewal (configurable window) |
| `/commissions` | Earnings dashboard + commission table |

---

## Verify It Works

```bash
# Backend health check
curl http://localhost:5000/api/health

# List clients
curl http://localhost:5000/api/clients

# Commission summary
curl http://localhost:5000/api/commissions/summary
```

---

## Reset & Re-seed

```bash
# Delete the database and re-seed from scratch
del insurance_portal.db
python database.py
python seed.py
```

---

## Architecture

```
Backend (Flask + SQLite)
  app.py              — Flask entry point (port 5000)
  database.py         — Schema creation + DB helpers
  seed.py             — Test data population
  routes/
    clients.py        — GET/POST/PUT /api/clients
    products.py       — GET/POST/PUT /api/products
    policies.py       — GET/POST/PUT + transition /api/policies
    commissions.py    — GET /api/commissions + summary
    activities.py     — GET/POST /api/activities

Frontend (React + Vite + Tailwind + Zustand)
  frontend/src/
    api.js            — fetch wrapper for all endpoints
    store/useStore.js — Zustand global store
    components/       — Sidebar, DataTable, DetailPanel, StatusBadge, ActivityFeed
    pages/            — Pipeline, Clients, ClientDetail, Products,
                        Applications, Policies, Commissions, Renewals
```

## Existing Python Tools (untouched)
The original in-memory Python tools (`agent/`, `tools/`, `workflows/`) are left intact.
The Flask app does NOT use them — it speaks directly to SQLite.
You can still run `python agent/orchestrator.py` to demo the original logic.
