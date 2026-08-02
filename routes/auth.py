import secrets
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from core.session import create_session_token, read_session_token
from settings.config import settings

router = APIRouter(tags=["auth"])


def _cookie_kwargs(max_age: int | None = None) -> dict[str, Any]:
    return {
        "httponly": True,
        "secure": settings.secure_cookies,
        "samesite": "lax",
        "path": "/",
        "max_age": max_age,
    }


@router.get("/discord/login")
async def discord_login() -> RedirectResponse:
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.DISCORD_OAUTH_SCOPES,
        "state": state,
    }

    auth_url = f"https://discord.com/oauth2/authorize?{urlencode(params)}"
    response = RedirectResponse(auth_url)
    response.set_cookie(
        settings.OAUTH_STATE_COOKIE_NAME,
        state,
        **_cookie_kwargs(600),
    )
    return response


@router.get("/discord/callback")
async def discord_callback(request: Request, code: str, state: str) -> RedirectResponse:
    saved_state = request.cookies.get(settings.OAUTH_STATE_COOKIE_NAME)

    if not saved_state or not secrets.compare_digest(state, saved_state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state parameter")

    async with httpx.AsyncClient(headers={"User-Agent": "BotPanel/1.0"}) as client:
        # 1. Token Exchange
        token_resp = await client.post(
            "https://discord.com/api/v10/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_resp.status_code != 200:
            return RedirectResponse(settings.auth_failure_redirect_url)

        token_data = token_resp.json()

        # 2. Fetch User Profile
        user_resp = await client.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

        if user_resp.status_code != 200:
            return RedirectResponse(settings.auth_failure_redirect_url)

        user = user_resp.json()

    # Minimal payload to prevent cookie truncation (>4KB limit)
    session_payload = {
        "id": user["id"],
        "username": user["username"],
        "avatar": user.get("avatar"),
        "access_token": token_data["access_token"],
    }

    session_token = create_session_token({"user": session_payload})

    response = RedirectResponse(settings.auth_success_redirect_url)
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        session_token,
        **_cookie_kwargs(settings.SESSION_MAX_AGE_SECONDS),
    )
    response.delete_cookie(settings.OAUTH_STATE_COOKIE_NAME)
    return response


@router.get("/me")
async def me(request: Request) -> dict[str, Any]:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = read_session_token(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return session


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(settings.allowed_origins_list[0])
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return response