from .urls import ROUTERS


def register_routes(app):
    for router in ROUTERS:
        app.include_router(router, prefix="/api")
