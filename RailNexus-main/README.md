# RailNexus

**Problem Statement:** SIH26027  
**Problem:** AI-powered Automatic Block Planning to maximize asset availability for train operations.

> This is a prototype using simulated railway operational data. It is not connected to Indian Railways production systems and does not represent signalling or safety rules.

## Overview

RailNexus is a lean, end-to-end demonstration of explainable maintenance block planning. It coordinates Engineering, Traction, and S&T work, checks a simulated train timetable, generates conflict-free windows, supports Control Office review, and records planned-versus-actual execution.

## Features

- Token-authenticated role-based access for Admin, Engineering, Traction, S&T, and Control Office
- Railway sections, corridor schematic, assets, trains, timetable, tasks, and requests
- Explainable 0–100 priority score with factor-by-factor reasons
- Deterministic train-aware block optimizer and multi-department grouping
- Conflict display, approval/modification/rejection, 30-minute delay replanning
- Read-only what-if comparison until an operator applies a conflict-free scenario
- Navigable weekly and monthly calendars, alerts, execution feedback, reports, and analytics
- Explicit explainable bottleneck detection and role-scoped dashboard/report data
- Simulated source adapters and a PostgreSQL-backed goods train forecast
- Idempotent simulated demo dataset covering critical, overdue, conflicting, completed, and delayed cases

## Architecture

```text
React + Vite + Tailwind
          |
     Django REST API
          |
 Planning services
          |
      PostgreSQL
```

Planning services are small Python classes: `PriorityEngine`, `ConflictDetector`, `BlockOptimizer`, `ReplanningService`, and `ScenarioSimulator`. The simulated local database represents future API-ready inputs conceptually associated with TMS, SMMS, TDMS, COA, Train Timetable, and Goods Train Forecast; no fake external calls are made.

## Project Structure

```text
railnexusWebsite/
├── backend/
│   ├── config/          # settings, API URLs, error handling
│   ├── accounts/        # user roles, authentication, permissions
│   ├── railway/         # sections, assets, trains, schedules, seed command
│   ├── maintenance/     # tasks, requests, alerts, execution
│   ├── planning/        # plans, conflicts, engines, API, tests
│   ├── analytics/       # dashboard and analytics APIs
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/  # reusable UI primitives
│   │   ├── layouts/     # authenticated operations shell
│   │   ├── pages/       # all user workflows
│   │   └── services/    # REST client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Tech Stack and Database

- Python 3.13, Django 5.2, Django REST Framework
- PostgreSQL 17 (Docker); Django ORM only
- React 19, Vite 7, Tailwind CSS 3, Recharts
- SQLite is supported only as a zero-dependency development/test fallback via `DB_ENGINE=sqlite`.

## AI-Assisted Planning Engine

This prototype does not train or claim an ML model. It uses documented configurable assumptions:

- Criticality: 25%
- Urgency: 20%
- Safety risk: 25%
- Asset availability impact: 20%
- Overdue factor: 10%

Inputs are rated 1–5 and normalized to 0–100. Bands are Critical (80+), High (65+), Medium (40+), and Low. The optimizer sorts by this score, groups same-section/same-date work, uses the longest grouped task as the block duration, and searches deterministic 30-minute windows while checking simulated train and existing block overlaps.

## Recommended Start (Docker)

Prerequisite: Docker Desktop.

```powershell
cd C:\railnexusWebsite
docker compose up --build
```

Open:

- Frontend: http://localhost:5174
- REST API: http://localhost:8001/api/
- Django admin: http://localhost:8001/admin/

PostgreSQL is exposed at `localhost:5433` (container port `5432`) with the development values in `docker-compose.yml`. Change these values before any non-local deployment.

## Manual Backend Setup

Start PostgreSQL and create a database/user matching `.env.example`, then:

```powershell
cd C:\railnexusWebsite\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Set the environment variables from .env in your shell.
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Development fallback without PostgreSQL:

```powershell
$env:DB_ENGINE="sqlite"
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

## Manual Frontend Setup

Node.js 20+ is required.

```powershell
cd C:\railnexusWebsite\frontend
npm install
npm run dev
```

Optional: set `VITE_API_URL=http://localhost:8000/api`.

## Demo Credentials

All demo accounts use password `RailNexus@2026`.

- `admin`
- `engineering`
- `traction`
- `snt`
- `control`

Use `control` for the full request → plan → approval → simulation → execution demonstration.

## API Summary

- `POST /api/auth/login/`, `POST /api/auth/logout/`, `GET /api/auth/me/`
- CRUD: `/api/sections/`, `/api/assets/`, `/api/trains/`, `/api/schedules/`
- CRUD: `/api/tasks/`, `/api/block-requests/`, `/api/block-plans/`
- CRUD: `/api/conflicts/`, `/api/execution/`, `/api/alerts/`
- `POST /api/planning/run/`
- `POST /api/planning/detect/`
- `POST /api/planning/replan/`
- `POST /api/planning/simulate/`
- `POST /api/block-plans/{id}/review/`
- `GET /api/dashboard/`, `GET /api/analytics/`, `GET /api/reports/`
- `GET /api/bottlenecks/`, `GET /api/calendar/?start=YYYY-MM-DD&end=YYYY-MM-DD`
- CRUD: `/api/goods-forecasts/`

The DRF browsable API is available after login/token authentication. Validation errors use appropriate HTTP status codes and consistent error envelopes.

## Suggested Demo Flow

1. Log in as `control`.
2. Inspect AI scores on Maintenance.
3. Create or view a Block Request.
4. Run Automatic Planner; observe grouped Engineering + S&T + Traction work and shifted train-conflicting windows.
5. Review displayed conflicts, resolve where appropriate, and approve or shift a plan.
6. View the weekly calendar.
7. Simulate a 30-minute train delay in What-If, compare before/after, then apply only a conflict-free scenario.
8. Use Replan to persist a revised window.
9. Record actual execution and inspect variance and Analytics.

## Testing

```powershell
cd C:\railnexusWebsite\backend
$env:DB_ENGINE="sqlite"
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

Frontend:

```powershell
cd C:\railnexusWebsite\frontend
npm run build
```

Tests cover priority scoring, train/block conflict detection, deterministic and asset-aware block generation, departmental grouping, forecast influence, bottlenecks, non-mutating simulation, role filtering, reports, calendar ranges, authentication, and review permissions.

## Limitations

- All railway operational data and metrics are simulated and generated locally.
- No production TMS, SMMS, TDMS, COA, timetable, or forecast adapter is connected.
- The optimizer is a transparent prototype heuristic, not a certified railway planning or signalling system.
- Section availability is simplified to a status; possession, topology, crew, rolling-stock, and safety-rule constraints are outside this prototype.
- Replanning models a user-triggered schedule delay, not real-time train movement.
- Token storage in browser local storage is suitable for this local demonstration, not a hardened production deployment.

## Future Integration

Define authenticated, railway-approved implementations behind a `RailwayDataProvider` contract for train schedules, assets, and maintenance tasks. Production work would also require formal operational-rule modelling, security hardening, audit history, adapter schema validation, approved identity management, observability, and railway safety assurance.
