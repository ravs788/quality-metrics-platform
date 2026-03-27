"""
FastAPI dependencies for authentication and authorization.

Provides dependency functions for extracting and validating API keys
from request headers.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.db_models import ApiKey
from src.services import auth_service


async def get_current_api_key(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> ApiKey:
    """
    Extract and validate API key from Authorization header.
    
    Args:
        authorization: Authorization header value (Bearer token)
        db: Database session
        
    Returns:
        ApiKey object if valid and active
        
    Raises:
        HTTPException: 401 if missing/invalid/inactive API key
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <api_key>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract the API key
    api_key = authorization.replace("Bearer ", "", 1)
    
    # Authenticate
    key_obj = auth_service.authenticate(db, api_key)
    
    if not key_obj or not key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return key_obj


async def require_admin(
    api_key: ApiKey = Depends(get_current_api_key)
) -> ApiKey:
    """
    Require admin API key.
    
    Args:
        api_key: Current API key from get_current_api_key
        
    Returns:
        ApiKey object if it's an admin key
        
    Raises:
        HTTPException: 403 if not an admin key
    """
    if not api_key.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return api_key


async def get_optional_api_key(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[ApiKey]:
    """
    Extract and validate API key from Authorization header (optional).
    
    This dependency allows endpoints to accept both authenticated and
    unauthenticated requests during migration period.
    
    Args:
        authorization: Authorization header value (Bearer token)
        db: Database session
        
    Returns:
        ApiKey object if valid, None if no auth provided
        
    Raises:
        HTTPException: 401 if authorization provided but invalid
    """
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <api_key>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    api_key = authorization.replace("Bearer ", "", 1)
    key_obj = auth_service.authenticate(db, api_key)
    
    if not key_obj or not key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return key_obj