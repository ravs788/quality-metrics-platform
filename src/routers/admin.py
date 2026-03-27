"""
Admin router for API key management.

Provides endpoints for creating, listing, and revoking API keys.
All endpoints require admin authentication.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies.auth import require_admin
from src.models.db_models import ApiKey, Team
from src.models.schemas import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyResponse
from src.services import auth_service

router = APIRouter(
    prefix="/api/v1/api-keys",
    tags=["admin"]
)


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    admin_key: ApiKey = Depends(require_admin)
):
    """
    Create a new API key for a team.
    
    **Requires admin authentication.**
    
    The plaintext API key is only returned once. Store it securely.
    """
    # Verify team exists
    team = db.query(Team).filter(Team.team_id == payload.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {payload.team_id} not found"
        )
    
    # Create API key
    api_key_obj, plaintext_key = auth_service.create_api_key(
        db=db,
        team_id=payload.team_id,
        key_name=payload.key_name,
        is_admin=payload.is_admin,
        created_by=payload.created_by
    )
    
    # Build response with plaintext key
    return ApiKeyCreateResponse(
        key_id=api_key_obj.key_id,
        team_id=api_key_obj.team_id,
        key_name=api_key_obj.key_name,
        is_admin=api_key_obj.is_admin,
        is_active=api_key_obj.is_active,
        created_at=api_key_obj.created_at,
        last_used_at=api_key_obj.last_used_at,
        revoked_at=api_key_obj.revoked_at,
        created_by=api_key_obj.created_by,
        api_key=plaintext_key
    )


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    team_id: int = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    admin_key: ApiKey = Depends(require_admin)
):
    """
    List all API keys.
    
    **Requires admin authentication.**
    
    Query parameters:
    - team_id: Filter by team ID (optional)
    - include_inactive: Include revoked keys (default: false)
    """
    api_keys = auth_service.list_api_keys(
        db=db,
        team_id=team_id,
        include_inactive=include_inactive
    )
    
    return [
        ApiKeyResponse(
            key_id=key.key_id,
            team_id=key.team_id,
            key_name=key.key_name,
            is_admin=key.is_admin,
            is_active=key.is_active,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            revoked_at=key.revoked_at,
            created_by=key.created_by
        )
        for key in api_keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    admin_key: ApiKey = Depends(require_admin)
):
    """
    Revoke an API key.
    
    **Requires admin authentication.**
    
    This is a soft delete - the key record remains in the database
    but is marked as inactive and cannot be used for authentication.
    """
    success = auth_service.revoke_api_key(db=db, key_id=key_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID {key_id} not found"
        )
    
    return None