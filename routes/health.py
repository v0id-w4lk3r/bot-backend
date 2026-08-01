from fastapi import APIRouter, HTTPException
from database.database import check_database
from settings.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "environment": settings.ENV,
        "database_configured": bool(settings.DATABASE_URL),
    }


@router.get("/health/db")
async def database_health() -> dict[str, str]:
    try:
        await check_database()
    except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        raise HTTPException(
            status_code=503,
            detail=f"Database is not ready: {message}",
        ) from exc

    return {"status": "ok"}
