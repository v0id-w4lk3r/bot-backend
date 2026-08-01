import httpx
import secrets
from typing import Any
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from core.session import create_session_token, read_session_token
from settings.config import settings

router = APIRouter(tags=["auth"])

client = httpx.AsyncClient(headers={"User-Agent": "BotPanel/1.0"})


def _cookie_kwargs(max_age: int | None = None) -> dict[str, Any]:
    return {
        "httponly": True,
        "secure": settings.secure_cookies,  
        "samesite": "lax",
        "path": "/",
        "max_age": max_age
    }


@router.get("/discord/login")
async def discord_login() -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    query = f"client_id={settings.DISCORD_CLIENT_ID}&redirect_uri={settings.DISCORD_REDIRECT_URI}&response_type=code&scope={settings.DISCORD_OAUTH_SCOPES}&state={state}"

    response = RedirectResponse(
        f"https://discord.com/oauth2/authorize?{query}")
    response.set_cookie(settings.OAUTH_STATE_COOKIE_NAME, state,
                        **_cookie_kwargs(600))
    return response


@router.get("/discord/callback")
async def discord_callback(request: Request, code: str,
                           state: str) -> RedirectResponse:
    saved_state = request.cookies.get(settings.OAUTH_STATE_COOKIE_NAME)

    if not saved_state or not secrets.compare_digest(state, saved_state):
        raise HTTPException(status_code=400, detail="Invalid state")

    # 1. Exchange code for token
    token_resp = await client.post("https://discord.com/api/oauth2/token",
                                   data={
                                       "client_id":
                                       settings.DISCORD_CLIENT_ID,
                                       "client_secret":
                                       settings.DISCORD_CLIENT_SECRET,
                                       "grant_type":
                                       "authorization_code",
                                       "code":
                                       code,
                                       "redirect_uri":
                                       settings.DISCORD_REDIRECT_URI,
                                   })

    if token_resp.status_code != 200:
        print(f"Token Error: {token_resp.text}")
        return RedirectResponse(settings.auth_failure_redirect_url)

    token_data = token_resp.json()

    # 2. Fetch User
    user_resp = await client.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"})
    user = user_resp.json()

    # 3. Create Session
    session_token = create_session_token({"discord_user": user})

    response = RedirectResponse(settings.auth_success_redirect_url)
    response.set_cookie(settings.SESSION_COOKIE_NAME, session_token,
                        **_cookie_kwargs(settings.SESSION_MAX_AGE_SECONDS))
    response.delete_cookie(settings.OAUTH_STATE_COOKIE_NAME)
    return response


@router.get("/me")
async def me(request: Request) -> dict[str, Any]:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401)

    session = read_session_token(token)
    if not session:
        raise HTTPException(status_code=401)
    return session
