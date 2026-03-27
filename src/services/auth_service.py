"""
Authentication service for API key management.

Handles API key generation, hashing, verification, and authentication.
"""

import hashlib
import secrets
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from src.models.db_models import ApiKey


def generate_api_key() -> str:
    """
    Generate a new API key with the format: qmp_<32 hex characters>
    
    Returns:
        str: Generated API key (plaintext, only shown once)
    """
    random_hex = secrets.token_hex(16)  # 32 characters
    return f"qmp_{random_hex}"


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA-256.
    
    Args:
        key: Plaintext API key
        
    Returns:
        str: SHA-256 hash of the key (hex encoded)
    """
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    """
    Verify a plaintext API key against its hash.
    
    Args:
        key: Plaintext API key to verify
        key_hash: Expected SHA-256 hash
        
    Returns:
        bool: True if key matches hash
    """
    return hash_api_key(key) == key_hash


def create_api_key(
    db: Session,
    team_id: int,
    key_name: str,
    is_admin: bool = False,
    created_by: Optional[str] = None
) -> Tuple[ApiKey, str]:
    """
    Create a new API key for a team.
    
    Args:
        db: Database session
        team_id: ID of the team this key belongs to
        key_name: Human-readable name for the key
        is_admin: Whether this is an admin key (default: False)
        created_by: Username/email of the creator (for audit)
        
    Returns:
        Tuple of (ApiKey object, plaintext key string)
        
    Note:
        The plaintext key is only returned once and should be
        provided to the user immediately. It cannot be retrieved later.
    """
    # Generate plaintext key
    plaintext_key = generate_api_key()
    
    # Hash the key for storage
    key_hash = hash_api_key(plaintext_key)
    
    # Create database record
    api_key = ApiKey(
        team_id=team_id,
        key_name=key_name,
        key_hash=key_hash,
        is_admin=is_admin,
        is_active=True,
        created_by=created_by
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return api_key, plaintext_key


def authenticate(db: Session, api_key: str) -> Optional[ApiKey]:
    """
    Authenticate an API key and return the associated key object.
    
    Args:
        db: Database session
        api_key: Plaintext API key from request
        
    Returns:
        ApiKey object if valid and active, None otherwise
        
    Side Effects:
        Updates last_used_at timestamp for valid keys
    """
    # Hash the provided key
    key_hash = hash_api_key(api_key)
    
    # Look up the key in database
    api_key_obj = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True
    ).first()
    
    if api_key_obj:
        # Update last_used_at timestamp
        api_key_obj.last_used_at = datetime.utcnow()
        db.commit()
    
    return api_key_obj


def revoke_api_key(db: Session, key_id: int) -> bool:
    """
    Revoke an API key (soft delete).
    
    Args:
        db: Database session
        key_id: ID of the key to revoke
        
    Returns:
        bool: True if key was revoked, False if not found
    """
    api_key = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    
    if not api_key:
        return False
    
    api_key.is_active = False
    api_key.revoked_at = datetime.utcnow()
    db.commit()
    
    return True


def list_api_keys(
    db: Session,
    team_id: Optional[int] = None,
    include_inactive: bool = False
) -> list[ApiKey]:
    """
    List API keys, optionally filtered by team.
    
    Args:
        db: Database session
        team_id: Filter by team ID (None = all teams)
        include_inactive: Include revoked keys (default: False)
        
    Returns:
        List of ApiKey objects
    """
    query = db.query(ApiKey)
    
    if team_id is not None:
        query = query.filter(ApiKey.team_id == team_id)
    
    if not include_inactive:
        query = query.filter(ApiKey.is_active == True)
    
    return query.all()