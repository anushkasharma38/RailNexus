<img width="950" height="443" alt="image" src="https://github.com/user-attachments/assets/2f93a4e7-c90d-48a2-a4b0-f559e575ab5c" />
# 🚆 RailNexus

### AI-Powered Automatic Block Planning for Railway Operations

> A deterministic and explainable railway operations prototype designed to optimize block planning, maintenance scheduling, and train movement while improving asset availability.

[![SIH 2026](https://img.shields.io/badge/Smart%20India%20Hackathon-2026-blue)](https://www.sih.gov.in/)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB)](https://react.dev/)
[![Backend](https://img.shields.io/badge/Backend-Django-092E20)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-336791)](https://www.postgresql.org/)
[![Deployment](https://img.shields.io/badge/Deployment-Vercel%20%7C%20Render-black)](https://vercel.com/)
[![Security](https://img.shields.io/badge/Security-MLSecOps-red)](#-security)

---

## 📌 Overview

**RailNexus** is an AI-assisted railway operations planning system developed for **Smart India Hackathon 2026**.

The system focuses on automatic block planning and maintenance scheduling while considering train movement, maintenance requirements, route constraints, asset availability, and operational priorities.

Instead of relying on manual planning alone, RailNexus provides a structured and explainable approach to generating operational plans.

### 🎯 Problem Statement

Railway maintenance and block planning involve multiple constraints such as:

- Train movement
- Maintenance requirements
- Track availability
- Asset availability
- Operational priorities
- Time windows
- Potential conflicts

Manual coordination of these factors can become complex as the number of trains, routes, and maintenance activities increases.

RailNexus addresses this challenge through an integrated digital planning platform.

---

## 💡 Our Solution

RailNexus combines a modern web dashboard with backend scheduling and decision-support logic.

The system:

1. Collects railway operational data.
2. Evaluates train and maintenance requirements.
3. Calculates priority scores.
4. Identifies potential conflicts.
5. Generates train-aware planning recommendations.
6. Provides an explainable view of the resulting decisions.
7. Presents the information through an operations dashboard.

---

## ✨ Key Features

### 🚆 Automatic Block Planning
Generate block planning recommendations while considering railway operational constraints.

### 🛠️ Maintenance Planning
Plan maintenance activities within suitable operational windows.

### ⚠️ Conflict Detection
Identify scheduling conflicts between train movements and planned maintenance blocks.

### 📊 Explainable Priority Scoring
Provide understandable priority factors behind scheduling decisions instead of presenting unexplained outputs.

### 🚄 Train-Aware Scheduling
Consider train movement and operational requirements while generating planning recommendations.

### 📈 Operations Dashboard
Centralized dashboard for monitoring railway operations, maintenance activities, planning information, and system status.

### 🔐 Secure Authentication
Protected operations dashboard with authenticated access to operational functionality.

### 🛡️ MLSecOps Integration
Security practices are incorporated throughout the ML/AI workflow, including:

- Input validation
- API protection
- Authentication
- Suspicious activity monitoring
- Secure deployment practices

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │      User / Admin    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │   Vite + Tailwind    │
                    └──────────┬───────────┘
                               │ REST API
                               ▼
                    ┌──────────────────────┐
                    │   Django Backend     │
                    │   Django REST API    │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌────────────┐   ┌──────────────┐   ┌─────────────┐
      │ Planning   │   │ Maintenance  │   │ Analytics   │
      │ Engine     │   │ Module       │   │ Module      │
      └────────────┘   └──────────────┘   └─────────────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ PostgreSQL Database  │
                    └──────────────────────┘
🧰 Technology Stack
Frontend
React.js
Vite
Tailwind CSS
JavaScript
REST API integration
Backend
Python
Django
Django REST Framework
Token Authentication
Database
PostgreSQL
Neon PostgreSQL
AI / Planning
Priority-based decision logic
Explainable scheduling
Constraint-aware planning
Train-aware block planning
Security
Authentication
API protection
Input validation
MLSecOps practices
CORS and CSRF protection
Deployment
Frontend: Vercel
Backend: Render
Database: Neon
📂 Project Structure
RailNexus/
│
├── backend/
│   ├── accounts/
│   ├── analytics/
│   ├── config/
│   ├── maintenance/
│   ├── planning/
│   ├── railway/
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── docker-compose.yml
├── .gitignore
└── README.md
⚙️ Installation & Setup
1. Clone the Repository
git clone https://github.com/anushkasharma38/RailNexus.git
cd RailNexus
🔧 Backend Setup
2. Navigate to Backend
cd backend
3. Create Virtual Environment
python -m venv venv
Windows
venv\Scripts\activate
Linux / macOS
source venv/bin/activate
4. Install Dependencies
pip install -r requirements.txt
5. Configure Environment Variables

Create a .env file inside the backend directory.

Example:

DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=postgres

POSTGRES_DB=railnexus
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173

Never commit real passwords, API keys, database credentials, or secret keys to GitHub.

6. Run Migrations
python manage.py migrate
7. Seed Demo Data
python manage.py seed_demo_data
8. Start Backend
python manage.py runserver

Backend:

http://127.0.0.1:8000
🎨 Frontend Setup

Open another terminal.

9. Navigate to Frontend
cd frontend
10. Install Dependencies
npm install
11. Configure API URL

Create:

frontend/.env

Add:

VITE_API_URL=http://localhost:8000/api
12. Start Frontend
npm run dev

Frontend:

http://localhost:5173
🔐 Security

Security is treated as an integral part of the RailNexus development and deployment workflow.

MLSecOps

RailNexus follows MLSecOps-oriented practices to improve security across the application and ML/decision-support workflow.

The implementation focuses on:

Input
  ↓
Validation
  ↓
Authentication
  ↓
API Protection
  ↓
Decision / ML Workflow
  ↓
Monitoring
  ↓
Secure Deployment

Sensitive configuration such as:

Database passwords
Django secret keys
API credentials
Deployment secrets

is managed through environment variables rather than being hard-coded into the source code.

🌐 Live Demo
RailNexus

Frontend:

https://rail-nexus-nu.vercel.app

Backend API:

https://railnexus-v5i5.onrender.com

The backend is hosted on a free-tier service and may take some time to wake up after a period of inactivity.

🖥️ Demo Workflow

The current prototype demonstrates the following workflow:

Operations Login
       ↓
Operations Dashboard
       ↓
Railway Data
       ↓
Train & Route Analysis
       ↓
Maintenance Requirements
       ↓
Priority Calculation
       ↓
Conflict Detection
       ↓
Automatic Block Planning
       ↓
Explainable Operational Plan
🏆 Smart India Hackathon 2026

Problem Statement ID: SIH26027

Problem Statement:

AI-powered Automatic Block Planning to maximize asset availability for Train Operations on Indian Railways

Theme: Transportation & Logistics

Category: Software

Team Name: RailNexus_01

Team ID: 137850

👥 Team
RailNexus_01

🚀 Future Scope

Future versions of RailNexus can include:

Integration with real railway operational datasets
Real-time train tracking
Advanced optimization algorithms
Predictive maintenance
Real-time disruption handling
Integration with railway signaling systems
Larger-scale network simulation
Advanced ML-based demand and delay prediction
Enhanced security monitoring
📜 Disclaimer

RailNexus is an academic and hackathon prototype developed for demonstration and research purposes.

The system uses simulated/demo railway operational data and is not connected to live Indian Railways operational infrastructure.

⭐ Support

If you find this project useful or interesting, consider giving the repository a ⭐.
