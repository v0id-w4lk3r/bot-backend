Here is the complete, raw content for your **`TESTING.md`** file, tailored for testing your FastAPI + Discord Bot backend stack.

```markdown
# 🧪 Testing & Local Setup Guide

This document covers everything you need to set up, configure, and run tests for the **Discord Bot Backend API**. Follow these instructions to spin up the required local dependencies (PostgreSQL, Redis), configure environment variables, and run tests cleanly.

---

## 📋 Prerequisites

Ensure the following tools are installed on your machine before starting:

* **Python 3.14+**
* **Docker & Docker Compose** (Recommended for quick service setup)
* **uv** (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

---

## 🛠️ Step 1: Services Setup (PostgreSQL & Redis)

The backend relies on **PostgreSQL** (relational database) and **Redis** (caching / task queues / rate-limiting).

### Option A: Using Docker Compose (Recommended)

Create a temporary `docker-compose.yml` or use the following command to run both services locally in isolated containers:

```bash
# Run PostgreSQL and Redis in the background
docker run -d \
  --name bot-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=bot_db_test \
  -p 5432:5432 \
  postgres:16-alpine

docker run -d \
  --name bot-redis \
  -p 6379:6379 \
  redis:alpine

```

### Option B: Local System Services

If you prefer using systemd/local services:

```bash
# PostgreSQL
sudo systemctl start postgresql

# Redis
sudo systemctl start redis

```

---

## ⚙️ Step 2: Environment Configuration (`.env`)

Copy `example.env` (or create a `.env` file in the root directory) and fill out the values needed for local testing:

```bash
cp example.env .env

```

### Key Environment Variables (`.env` Reference)

| Variable | Recommended Test Value | Description |
| --- | --- | --- |
| `ENVIRONMENT` | `testing` | Switches app state to testing mode |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/bot_db_test` | Connection string for async SQLAlchemy |
| `REDIS_URL` | `redis://localhost:6379/0` | Connection string for Redis instance |
| `SECRET_KEY` | `test_secret_key_change_in_production_12345` | JWT signing secret |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifespan |
| `DISCORD_BOT_TOKEN` | `your_test_bot_token_here` | Discord bot application token (Optional for API-only tests) |
| `DISCORD_CLIENT_ID` | `123456789012345678` | Discord application Client ID |
| `DISCORD_CLIENT_SECRET` | `your_discord_client_secret` | Discord OAuth2 Client Secret |

---

## 🔍 Step 3: Verifying Service Connections

Before running the API server or tests, verify that both PostgreSQL and Redis are accepting connections.

### 1. Check PostgreSQL

```bash
# Check if port 5432 is listening
ss -tulpn | grep 5432

# Or ping using psql / docker
docker exec -it bot-postgres pg_isready -U postgres

```

### 2. Check Redis

```bash
# Ping Redis using redis-cli
redis-cli ping
# Expected output: PONG

```

---

## 🧪 Step 4: Running the Test Suite

### 1. Install Dependencies

Sync your virtual environment using `uv`:

```bash
uv sync

```

### 2. Execute Pytest

Run the async test suite:

```bash
# Run all tests
uv run pytest

# Run tests with verbose output & print statements
uv run pytest -s -v

# Run a specific test file
uv run pytest tests/test_moderation.py

```

---

## 🚀 Step 5: Running the Server in Development / Test Mode

To launch the FastAPI development server with live reload:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

```

Once running, verify endpoints using:

* **Interactive Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check Endpoint:** `GET http://localhost:8000/health`

---

## 🧹 Step 6: Cleaning Up Test Artifacts

To stop and remove test containers after testing:

```bash
docker stop bot-postgres bot-redis
docker rm bot-postgres bot-redis

```