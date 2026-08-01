from routes.auth import router as auth_router
from routes.health import router as health_router

ROUTERS = [
    auth_router,
    health_router,
]
