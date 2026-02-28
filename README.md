[README.md](https://github.com/user-attachments/files/25621004/README.md)
# CRMPro — Flask CRM System

A full-featured CRM system built with Flask, including a sales pipeline, analytics, REST API, role-based access control, logging, Docker support, and tests.

---

## Tech Stack

- **Backend**: Python 3.11, Flask 3, SQLAlchemy 2, Flask-Migrate (Alembic)
- **Auth**: Flask-Login, Flask-WTF (CSRF)
- **DB**: PostgreSQL (production) / SQLite (development)
- **Frontend**: Bootstrap 5 dark theme, Bootstrap Icons
- **Tests**: pytest
- **Deploy**: Docker + docker-compose

---

## Quick Start (local)

```bash
git clone <repo>
cd crm_project

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

flask db upgrade
python run.py
```

Open http://localhost:5000 and register an account.  
To grant admin access, use `flask shell`:

```python
from app.models.user import User
from app import db
u = User.query.filter_by(username='yourname').first()
u.role = 'admin'
db.session.commit()
```

---

## Docker (with PostgreSQL)

```bash
cp .env.example .env
# Edit SECRET_KEY and DB_PASSWORD in .env

docker-compose up --build
```

App available at: http://localhost:5000  
Logs are written to `./logs/crm.log`

---

## Features

### Stage 1 — Sales Pipeline (Deals)

Deal model with stages: `New → Contacted → Proposal → Won / Lost`

```
User (manager) → Client → Deal
```

- Create / edit / delete deals
- `closed_at` is automatically set when a deal moves to Won or Lost
- Managers can only see their own deals

### Stage 2 — Analytics Dashboard

- Total deal amount and won deal amount
- Conversion rate (Win Rate %)
- Top manager by revenue
- Pipeline funnel by stage (progress bars)
- Recent deals list

### Stage 3 — Filtering, Search & Pagination

- Search by client name or deal title
- Filter by status or stage
- Sort by amount (asc/desc) or date
- Pagination (10 records per page)

### Stage 4 — REST API v1

Base URL: `/api/v1`  
Auth: **HTTP Basic Auth**

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/clients` | List all clients |
| POST | `/api/v1/clients` | Create a client |
| GET/PUT/DELETE | `/api/v1/clients/<id>` | Get/update/delete client by ID |
| GET | `/api/v1/deals` | List all deals |
| POST | `/api/v1/deals` | Create a deal |
| GET/PUT/DELETE | `/api/v1/deals/<id>` | Get/update/delete deal by ID |
| GET | `/api/v1/stats` | Statistics (admin only) |

Query parameters: `?search=&stage=&sort=newest|amount_desc|amount_asc&page=&per_page=`

```bash
# List deals
curl -u admin:pass http://localhost:5000/api/v1/deals

# Create a deal
curl -u admin:pass -X POST http://localhost:5000/api/v1/deals \
  -H "Content-Type: application/json" \
  -d '{"title":"New contract","client_id":1,"amount":5000,"stage":"proposal"}'

# Get statistics
curl -u admin:pass http://localhost:5000/api/v1/stats
```

### Stage 5 — Roles & Permissions

| Action | Manager | Admin |
|--------|---------|-------|
| View own clients | ✅ | ✅ (all) |
| Create a client | ✅ | ✅ |
| Delete a client | ❌ | ✅ |
| View own deals | ✅ | ✅ (all) |
| Create/edit a deal | ✅ | ✅ |
| Delete a deal | ✅ (own) | ✅ |
| Admin panel | ❌ | ✅ |
| API /stats | ❌ | ✅ |

### Stage 6 — Logging

Logs are written to console and `logs/crm.log` (rotation: 5 MB × 3 files).

Logged events:
- User registration, login and logout
- Client and deal creation/deletion
- Role changes
- Failed API authentication attempts

### Stage 7 — Docker

- `Dockerfile` — Python 3.11 slim base image
- `docker-compose.yml` — `web` + `db` (PostgreSQL 16) services
- Health check for the database
- Volumes for data and logs
- Auto-migration on startup

### Stage 8 — Tests

```bash
pip install pytest
pytest
# or with verbose output
pytest -v
```

Coverage:
- `test_auth.py` — registration, login, wrong password, logout
- `test_clients.py` — CRUD, permissions, search
- `test_deals.py` — CRUD, pipeline, filtering, permissions
- `test_api.py` — REST API, authentication, permissions

---

## Project Structure

```
crm_project/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py
│   ├── extensions.py        # db, login_manager, migrate, csrf
│   ├── logger.py            # Centralized logger
│   ├── utils.py             # Role-based decorators
│   ├── routes.py            # Clients + admin + dashboard
│   ├── models/user.py       # User, Client, Deal, ClientActivity
│   ├── auth/                # Registration / login
│   ├── deals/               # Sales pipeline
│   ├── api/                 # REST API v1
│   └── templates/
│       ├── base.html
│       ├── dashboard.html   # Analytics + funnel
│       ├── clients.html
│       └── deals/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_clients.py
│   ├── test_deals.py
│   └── test_api.py
├── migrations/
├── logs/                    # Created automatically
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── pytest.ini
└── requirements.txt
```
