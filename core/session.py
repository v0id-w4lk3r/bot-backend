import base64
import hashlib
import hmac
import json
import time
from typing import Any

from settings.config import settings


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padded = data + ("=" * (-len(data) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _sign(value: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        value.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def create_session_token(data: dict[str, Any], max_age_seconds: int | None = None) -> str:
    expires_at = int(time.time()) + (max_age_seconds or settings.SESSION_MAX_AGE_SECONDS)
    payload = {"exp": expires_at, "data": data}
    encoded_payload = _b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    return f"{encoded_payload}.{_sign(encoded_payload)}"


def read_session_token(token: str) -> dict[str, Any] | None:
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError:
        return None

    if not hmac.compare_digest(signature, _sign(encoded_payload)):
        return None

    try:
        payload = json.loads(_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get("exp", 0)) < int(time.time()):
        return None

    data = payload.get("data")
    return data if isinstance(data, dict) else None