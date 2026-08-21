# CRMPro - Flask CRM System

[![CI](https://github.com/3axap345/CRM-project/actions/workflows/ci.yml/badge.svg)](https://github.com/3axap345/CRM-project/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)

CRMPro is a Flask-based CRM pet project for managing clients, sales deals, tasks, and client interaction history. It includes role-based access control, a sales dashboard, REST API, Docker setup, tests, linting, and GitHub Actions CI/CD.

## Features

- User registration, login, and logout.
- Roles: `manager` and `admin`.
- Client management with create, view, search, edit, delete, and statuses.
- Deals pipeline with money-safe `Numeric` amounts and won/lost close tracking.
- Task management with due dates, priorities, completion, and overdue filters.
- Client interaction timeline for notes, calls, meetings, and emails.
- Role-aware dashboard with sales analytics and Chart.js graphs.
- REST API with HTTP Basic Auth.
- Docker and docker-compose with PostgreSQL.
- GitHub Actions CI and GHCR image publishing.

## Stack

- Python 3.11
- Flask 3
- SQLAlchemy 2
- Flask-Migrate / Alembic
- Flask-Login
- Flask-WTF / CSRFProtect
- SQLite for local development
- PostgreSQL for Docker/production-style setup
- Bootstrap 5
- Bootstrap Icons
- Chart.js
- pytest
- ruff
- Docker
- GitHub Actions

## Project Structure

```text
CRM-project-main/
├── app/
│   ├── __init__.py
│   ├── api/
│   ├── auth/
│   ├── deals/
│   ├── tasks/
│   ├── templates/
│   ├── config.py
│   ├── dashboard.py
│   ├── extensions.py
│   ├── forms.py
│   ├── routes.py
│   └── models/
│       └── user.py
├── migrations/
├── tests/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── requirements.txt
├── pyproject.toml
└── run.py
```

## Local Setup

```bash
git clone https://github.com/3axap345/CRM-project.git
cd CRM-project

python -m venv venv
venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m flask db upgrade
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## Environment Variables

Local development works without an `.env` file and defaults to SQLite.

Supported variables:

```text
SECRET_KEY
DATABASE_URL
FLASK_ENV
FLASK_RUN_HOST
FLASK_RUN_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

Example:

```bash
copy .env.example .env
```

Never commit a real `.env` file.

## Admin User

New users are created as `manager` by default.

To promote a user to admin:

```bash
python -m flask shell
```

```python
from app.extensions import db
from app.models.user import User

user = User.query.filter_by(email="you@example.com").first()
user.role = "admin"
db.session.commit()
```

## Database Migrations

Apply migrations:

```bash
python -m flask db upgrade
```

Create a new migration after model changes:

```bash
python -m flask db migrate -m "describe change"
```

## Tests

Run all tests:

```bash
python -m pytest -q
```

Current coverage includes:

- authentication;
- clients;
- deals;
- tasks;
- interactions;
- dashboard calculations;
- REST API authentication, validation, CRUD, and authorization.

## Lint

Run ruff:

```bash
python -m ruff check .
```

## Docker

Create `.env`:

```bash
copy .env.example .env
```

Edit `SECRET_KEY` and `POSTGRES_PASSWORD`, then run:

```bash
docker compose --env-file .env up --build
```

The app runs at:

```text
http://localhost:5000
```

The container entrypoint waits for PostgreSQL and runs:

```bash
flask db upgrade
```

## REST API

Base URL:

```text
/api
```

Auth:

```text
HTTP Basic Auth
```

You can authenticate with email or username.

### Clients

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/clients` | List visible clients |
| POST | `/api/clients` | Create client |
| GET | `/api/clients/<id>` | Get client |
| PUT/PATCH | `/api/clients/<id>` | Update client |
| DELETE | `/api/clients/<id>` | Delete client, admin only |

### Deals

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/deals` | List visible deals |
| POST | `/api/deals` | Create deal |
| GET | `/api/deals/<id>` | Get deal |
| PUT/PATCH | `/api/deals/<id>` | Update deal |
| DELETE | `/api/deals/<id>` | Delete deal |

### Tasks

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/tasks` | List visible tasks |
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks/<id>` | Get task |
| PUT/PATCH | `/api/tasks/<id>` | Update task |
| DELETE | `/api/tasks/<id>` | Delete task |

### API Examples

```bash
curl -u manager@example.com:password http://localhost:5000/api/clients
```

```bash
curl -u manager@example.com:password ^
  -H "Content-Type: application/json" ^
  -X POST http://localhost:5000/api/deals ^
  -d "{\"title\":\"Website redesign\",\"client_id\":1,\"amount\":\"2500.00\",\"status\":\"proposal\"}"
```

```bash
curl -u manager@example.com:password ^
  -H "Content-Type: application/json" ^
  -X PATCH http://localhost:5000/api/tasks/1 ^
  -d "{\"status\":\"done\"}"
```

## Roles and Permissions

| Action | Manager | Admin |
| --- | --- | --- |
| View clients | Own only | All |
| Create client | Yes | Yes |
| Edit client | Own only | All |
| Delete client | No | Yes |
| View deals | Own only | All |
| Create deal | Own clients only | All clients |
| Edit/delete deal | Own only | All |
| View tasks | Assigned only | All |
| Create task | Assign to self | Assign to anyone |
| Edit/complete/delete task | Assigned only | All |
| View interactions | Own clients only | All clients |
| Admin panel | No | Yes |
| API access | Scoped to own data | All data |

## CI/CD

### CI

Workflow:

```text
.github/workflows/ci.yml
```

Runs on:

- push to `main`;
- pull request to `main`.

Pipeline:

1. checkout;
2. set up Python 3.11;
3. install dependencies;
4. run `ruff check .`;
5. run `python -m pytest -q`.

### CD

Workflow:

```text
.github/workflows/release.yml
```

Runs on:

- tags matching `v*`;
- manual workflow dispatch.

Publishes Docker image to:

```text
ghcr.io/3axap345/crm-project
```

Release flow:

```bash
git tag v1.0.0
git push origin v1.0.0
```

No personal access token is stored in the repository. The workflow uses `GITHUB_TOKEN`.

## Production Deployment Flow

A simple production flow can use the GHCR image:

1. Create a release tag such as `v1.0.0`.
2. GitHub Actions publishes the Docker image to GHCR.
3. On a server, set real environment variables:
   - `SECRET_KEY`
   - `DATABASE_URL`
4. Pull and run the image.
5. The entrypoint runs migrations before starting the app.

Server-specific deployment credentials are intentionally not included.

## Current Limitations

- No pagination yet.
- No OpenAPI/Swagger docs yet.
- No password reset flow.
- No file attachments.
- No production server deployment workflow yet.
