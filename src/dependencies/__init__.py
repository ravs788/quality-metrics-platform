"""
FastAPI dependencies for authentication and authorization.
"""

from src.dependencies.auth import (
    get_current_api_key,
    require_admin,
    get_optional_api_key
)

__all__ = [
    "get_current_api_key",
    "require_admin",
    "get_optional_api_key"
]