
# Discord Bot Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![uv](https://img.shields.io/badge/uv-Package_Manager-DE5D43?style=for-the-badge)](https://github.com/astral-sh/uv)

An asynchronous REST API built with **FastAPI**, **SQLAlchemy 2.0 (asyncio)**, and **PostgreSQL** (`asyncpg`). This service serves as the core management backend for a Discord bot, powering both real-time bot operations and the web admin dashboard.

> 🧪 **Looking to test or run locally?** Check out the [Testing & Local Setup Guide](TESTING.md).

## 🛠 Features & Capabilities

* **Authentication & Guild Context:** OAuth2/JWT auth endpoints and guild-level management.
* **Moderation & Escalation System:** Issue warnings, clear infractions, track active tempbans, and set up dynamic warning thresholds (e.g., 3 warns = mute, 5 warns = tempban).
* **AFK Tracking:** Set, update, and clear user AFK statuses for both bot commands and web dashboard management.
* **Database Shared Core:** Clean separation using `db_helpers` to allow shared database logic between FastAPI and Discord bot instances.

---

## 📁 Directory Structure

```text
.
├── database/
│   ├── base.py                 # Declarative Base definition
│   ├── database.py             # Async engine & session lifecycle
│   ├── models.py               # SQLAlchemy ORM models & mixins
│   └── db_helpers/             # Shared database operation modules
│       ├── admin_roles.py
│       ├── afk.py
│       ├── autoresponder.py
│       ├── guild.py
│       ├── leveling.py
│       ├── moderation.py
│       └── welcome.py
├── routes/                     # FastAPI Router endpoints
│   ├── afk.py
│   ├── auth.py
│   ├── guilds.py
│   ├── health.py
│   └── moderation.py
├── settings/
│   ├── apps.py                 # App configuration & route loaders
│   └── urls.py                 # Central ROUTERS list export
├── .env                        # Environment variables (DB credentials, secrets)
├── main.py                     # Entry point & lifespan handler
└── pyproject.toml              # UV / Dependency management configuration

```

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.14+**
* **PostgreSQL** running locally or in Docker
* **uv** package manager (`pip install uv`)

### 1. Database Setup

Ensure PostgreSQL is running on your machine or container:

```bash
# Start PostgreSQL via systemd
sudo systemctl start postgresql

# OR via Docker
docker run --name bot-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=bot_db -p 5432:5432 -d postgres

```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bot_db
SECRET_KEY=your_super_secret_jwt_key

```

### 3. Installation & Running

Install dependencies and start the Uvicorn development server:

```bash
# Sync virtualenv & dependencies
uv sync

# Run development server with live reload
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

```

Interactive API documentation will be available at:

* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

---

## 📡 API Endpoint Reference

### 🏥 System & Health

* `GET /health` – System status check.

---

### 🔑 Authentication (`/auth`)

* `POST /auth/login` – User authentication & JWT generation.
* `POST /auth/refresh` – Token refresh endpoint.

---

### 🛡️ Moderation System (`/guilds/{guild_id}/moderation`)

#### **Warnings & Infractions**

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/warnings/{user_id}` | Fetch all warning records for a user. |
| `POST` | `/warnings` | Issue a warning to a user (evaluates escalation rules automatically). |
| `DELETE` | `/warnings/{user_id}` | Reset/clear all warnings for a user. |

**`POST /warnings` Request Body:**

```json
{
  "user_id": 123456789012345678,
  "reason": "Repeated spam in general chat"
}

```

**Response Example (with Auto-Triggered Punishment):**

```json
{
  "status": "success",
  "warn_id": 12,
  "total_warnings": 3,
  "triggered_punishment": {
    "punishment_type": "mute",
    "duration_seconds": 3600,
    "warn_count": 3
  }
}

```

---

#### **Warning Punishment Escalation Rules**

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/punishment-rules` | List configured warning escalation thresholds for the server. |
| `POST` | `/punishment-rules` | Create or update a warning count threshold action. |
| `DELETE` | `/punishment-rules/{warn_count}` | Remove a punishment rule for a specific warning count. |

**`POST /punishment-rules` Request Body:**

```json
{
  "warn_count": 3,
  "punishment_type": "mute",
  "duration_seconds": 3600
}

```

---

#### **Tempbans**

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/tempbans` | Get active temporary bans for the moderation dashboard. |
| `POST` | `/tempbans` | Issue a tempban from the web dashboard. |
| `DELETE` | `/tempbans/{record_id}` | Unban / revoke an active tempban early. |

---

### 💤 AFK Management (`/guilds/{guild_id}/afk`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/{user_id}` | Check AFK status for a member. |
| `POST` | `/{user_id}` | Set/update AFK status for a member. |
| `DELETE` | `/{user_id}` | Clear AFK status. |

---


1. **API as Core Engine:** The API handles the database CRUD logic and exposes endpoints for Web Dashboard administrative tasks.
2. **Shared Helpers:** DB helpers in `database/db_helpers/` abstract raw SQL/SQLAlchemy logic into clean async functions imported by both API route handlers and Discord bot cogs.