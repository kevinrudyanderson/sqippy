from fastapi import Response

from app.config import settings

_VALID_SAMESITE = {"lax", "strict", "none"}


def _get_samesite() -> str:
    """Return a sanitized SameSite value FastAPI/Starlette understands."""
    configured = (settings.COOKIE_SAMESITE or "lax").lower()
    if configured not in _VALID_SAMESITE:
        return "lax"
    return configured


def set_refresh_token_cookie(response: Response, token: str, max_age_seconds: int) -> None:
    """Attach the refresh token to the response with hardened defaults."""
    cookie_kwargs = {
        "key": settings.REFRESH_TOKEN_COOKIE_NAME,
        "value": token,
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": _get_samesite(),
        "path": settings.COOKIE_PATH,
        "max_age": max_age_seconds,
    }

    if cookie_kwargs["samesite"] == "none":
        # Browsers require Secure flag when SameSite=None; enforce it here.
        cookie_kwargs["secure"] = True

    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN

    response.set_cookie(**cookie_kwargs)


def clear_refresh_token_cookie(response: Response) -> None:
    """Remove the refresh token cookie with the same scope that set it."""
    delete_kwargs = {
        "key": settings.REFRESH_TOKEN_COOKIE_NAME,
        "path": settings.COOKIE_PATH,
    }

    if settings.COOKIE_DOMAIN:
        delete_kwargs["domain"] = settings.COOKIE_DOMAIN

    response.delete_cookie(**delete_kwargs)
