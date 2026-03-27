"""Unit tests for authentication dependency helpers."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

from src.dependencies.auth import get_current_api_key, get_optional_api_key, require_admin


@pytest.mark.asyncio
async def test_get_current_api_key_missing_authorization_header():
    """Returns 401 when Authorization header is missing."""
    with pytest.raises(HTTPException) as exc:
        await get_current_api_key(authorization=None, db=MagicMock())

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Missing authorization header"


@pytest.mark.asyncio
async def test_get_current_api_key_invalid_authorization_format():
    """Returns 401 when Authorization header is not Bearer format."""
    with pytest.raises(HTTPException) as exc:
        await get_current_api_key(authorization="Token abc", db=MagicMock())

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid authorization header format" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_api_key_invalid_api_key():
    """Returns 401 when auth service returns no key object."""
    db = MagicMock()
    with patch("src.dependencies.auth.auth_service.authenticate", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await get_current_api_key(authorization="Bearer qmp_invalid", db=db)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid or inactive API key"


@pytest.mark.asyncio
async def test_get_current_api_key_inactive_api_key():
    """Returns 401 when auth service returns an inactive key."""
    db = MagicMock()
    inactive_key = MagicMock()
    inactive_key.is_active = False

    with patch("src.dependencies.auth.auth_service.authenticate", return_value=inactive_key):
        with pytest.raises(HTTPException) as exc:
            await get_current_api_key(authorization="Bearer qmp_inactive", db=db)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid or inactive API key"


@pytest.mark.asyncio
async def test_get_current_api_key_valid_api_key():
    """Returns ApiKey object when key is valid and active."""
    db = MagicMock()
    active_key = MagicMock()
    active_key.is_active = True

    with patch("src.dependencies.auth.auth_service.authenticate", return_value=active_key):
        result = await get_current_api_key(authorization="Bearer qmp_valid", db=db)

    assert result is active_key


@pytest.mark.asyncio
async def test_require_admin_rejects_non_admin_key():
    """Returns 403 for non-admin API keys."""
    api_key = MagicMock()
    api_key.is_admin = False

    with pytest.raises(HTTPException) as exc:
        await require_admin(api_key=api_key)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "Admin access required"


@pytest.mark.asyncio
async def test_require_admin_accepts_admin_key():
    """Returns the key object for admin API keys."""
    api_key = MagicMock()
    api_key.is_admin = True

    result = await require_admin(api_key=api_key)
    assert result is api_key


@pytest.mark.asyncio
async def test_get_optional_api_key_without_authorization_returns_none():
    """Returns None when no auth header is provided."""
    result = await get_optional_api_key(authorization=None, db=MagicMock())
    assert result is None


@pytest.mark.asyncio
async def test_get_optional_api_key_invalid_format():
    """Returns 401 when optional auth header is malformed."""
    with pytest.raises(HTTPException) as exc:
        await get_optional_api_key(authorization="Token bad", db=MagicMock())

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid authorization header format" in exc.value.detail


@pytest.mark.asyncio
async def test_get_optional_api_key_invalid_api_key():
    """Returns 401 when optional auth key lookup fails."""
    db = MagicMock()
    with patch("src.dependencies.auth.auth_service.authenticate", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await get_optional_api_key(authorization="Bearer qmp_invalid", db=db)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid or inactive API key"


@pytest.mark.asyncio
async def test_get_optional_api_key_inactive_api_key():
    """Returns 401 when optional auth key is inactive."""
    db = MagicMock()
    inactive_key = MagicMock()
    inactive_key.is_active = False

    with patch("src.dependencies.auth.auth_service.authenticate", return_value=inactive_key):
        with pytest.raises(HTTPException) as exc:
            await get_optional_api_key(authorization="Bearer qmp_inactive", db=db)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid or inactive API key"


@pytest.mark.asyncio
async def test_get_optional_api_key_valid_api_key():
    """Returns ApiKey object when optional auth is valid and active."""
    db = MagicMock()
    active_key = MagicMock()
    active_key.is_active = True

    with patch("src.dependencies.auth.auth_service.authenticate", return_value=active_key):
        result = await get_optional_api_key(authorization="Bearer qmp_valid", db=db)

    assert result is active_key