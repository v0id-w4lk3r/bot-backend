from routes.afk import router as afk_router
from routes.auth import router as auth_router
from routes.guilds import router as guilds_router
from routes.health import router as health_router
from routes.moderation import router as moderation_router

ROUTERS = [
    auth_router,
    guilds_router,
    health_router,
    afk_router,
    moderation_router,
]