# Discord Bot Panel Backend

FastAPI backend for sharing Discord bot configuration/state with a web panel.

## Run locally

Create a `.env` file when you are ready to connect a real shared database:

```env
ENV=development
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bot_backend
ALLOWED_ORIGINS=http://localhost:3000
DB_CREATE_TABLES=true
DB_CONNECT_TIMEOUT=5
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=http://127.0.0.1:8000/api/auth/discord/callback
AUTH_SUCCESS_REDIRECT_URL=http://localhost:3000
AUTH_FAILURE_REDIRECT_URL=http://localhost:3000/login
```

Start the API:

```bash
uv run uvicorn main:app --reload
```

Health endpoints:

- `GET /api/health`
- `GET /api/health/db`

Discord auth endpoints:

- `GET /api/auth/discord/login`
- `GET /api/auth/discord/callback`
- `GET /api/auth/me`
- `POST /api/auth/logout`

`DB_CREATE_TABLES=true` creates the SQLAlchemy model tables on startup. Keep it
off when you move to migrations.
