"""
Unit tests for authentication service.

Tests API key generation, hashing, verification, and authentication logic.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.services import auth_service


class TestApiKeyGeneration:
    """Tests for API key generation."""

    def test_generate_api_key_format(self):
        """Test that generated API key has correct format."""
        key = auth_service.generate_api_key()
        
        assert key.startswith("qmp_")
        assert len(key) == 36  # "qmp_" (4) + 32 hex chars
    
    def test_generate_api_key_uniqueness(self):
        """Test that generated keys are unique."""
        keys = [auth_service.generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100  # All unique
    
    def test_generate_api_key_hex_characters(self):
        """Test that key contains only valid hex characters after prefix."""
        key = auth_service.generate_api_key()
        hex_part = key[4:]  # Remove "qmp_" prefix
        
        # Should only contain hex characters
        assert all(c in "0123456789abcdef" for c in hex_part)


class TestApiKeyHashing:
    """Tests for API key hashing."""

    def test_hash_api_key_returns_sha256(self):
        """Test that hash returns a 64-character SHA-256 hex string."""
        key = "qmp_test1234567890abcdef12345678"
        key_hash = auth_service.hash_api_key(key)
        
        assert len(key_hash) == 64
        assert all(c in "0123456789abcdef" for c in key_hash)
    
    def test_hash_api_key_deterministic(self):
        """Test that hashing the same key produces same hash."""
        key = "qmp_test1234567890abcdef12345678"
        hash1 = auth_service.hash_api_key(key)
        hash2 = auth_service.hash_api_key(key)
        
        assert hash1 == hash2
    
    def test_hash_api_key_different_keys_different_hashes(self):
        """Test that different keys produce different hashes."""
        key1 = "qmp_test1234567890abcdef12345678"
        key2 = "qmp_test1234567890abcdef12345679"
        
        hash1 = auth_service.hash_api_key(key1)
        hash2 = auth_service.hash_api_key(key2)
        
        assert hash1 != hash2


class TestApiKeyVerification:
    """Tests for API key verification."""

    def test_verify_api_key_correct(self):
        """Test that verification succeeds with correct key."""
        key = "qmp_test1234567890abcdef12345678"
        key_hash = auth_service.hash_api_key(key)
        
        assert auth_service.verify_api_key(key, key_hash) is True
    
    def test_verify_api_key_incorrect(self):
        """Test that verification fails with incorrect key."""
        key = "qmp_test1234567890abcdef12345678"
        wrong_key = "qmp_wrong1234567890abcdef1234567"
        key_hash = auth_service.hash_api_key(key)
        
        assert auth_service.verify_api_key(wrong_key, key_hash) is False


class TestCreateApiKey:
    """Tests for API key creation."""

    def test_create_api_key_returns_tuple(self):
        """Test that create_api_key returns (ApiKey, plaintext_key) tuple."""
        mock_db = MagicMock()
        
        # Mock the ApiKey class
        with patch("src.services.auth_service.ApiKey") as mock_api_key_class:
            mock_api_key_instance = MagicMock()
            mock_api_key_class.return_value = mock_api_key_instance
            
            result = auth_service.create_api_key(
                db=mock_db,
                team_id=1,
                key_name="Test Key",
                is_admin=False,
                created_by="test@example.com"
            )
            
            # Verify it returns a tuple
            assert isinstance(result, tuple)
            assert len(result) == 2
            
            # First element is the ApiKey object
            api_key_obj, plaintext_key = result
            assert api_key_obj == mock_api_key_instance
            
            # Second element is a string (the plaintext key)
            assert isinstance(plaintext_key, str)
            assert plaintext_key.startswith("qmp_")
    
    def test_create_api_key_calls_db_correctly(self):
        """Test that create_api_key interacts with database correctly."""
        mock_db = MagicMock()
        
        with patch("src.services.auth_service.ApiKey") as mock_api_key_class:
            mock_api_key_instance = MagicMock()
            mock_api_key_class.return_value = mock_api_key_instance
            
            auth_service.create_api_key(
                db=mock_db,
                team_id=1,
                key_name="Test Key",
                is_admin=True,
                created_by="admin@example.com"
            )
            
            # Verify database operations
            mock_db.add.assert_called_once_with(mock_api_key_instance)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_api_key_instance)


class TestAuthenticate:
    """Tests for authentication."""

    def test_authenticate_valid_key(self):
        """Test authentication with valid key."""
        mock_db = MagicMock()
        mock_api_key = MagicMock()
        mock_api_key.is_active = True
        
        # Mock the query chain (single filter call with multiple conditions)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_api_key
        
        result = auth_service.authenticate(mock_db, "qmp_valid_key")
        
        assert result == mock_api_key
        # Verify last_used_at was updated
        assert mock_api_key.last_used_at is not None
        mock_db.commit.assert_called_once()
    
    def test_authenticate_invalid_key(self):
        """Test authentication with invalid key."""
        mock_db = MagicMock()
        
        # Mock no key found (single filter call with multiple conditions)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = auth_service.authenticate(mock_db, "qmp_invalid_key")
        
        assert result is None


class TestRevokeApiKey:
    """Tests for API key revocation."""

    def test_revoke_api_key_success(self):
        """Test successful API key revocation."""
        mock_db = MagicMock()
        mock_api_key = MagicMock()
        mock_api_key.is_active = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_api_key
        
        result = auth_service.revoke_api_key(mock_db, key_id=1)
        
        assert result is True
        assert mock_api_key.is_active is False
        assert mock_api_key.revoked_at is not None
        mock_db.commit.assert_called_once()
    
    def test_revoke_api_key_not_found(self):
        """Test revocation of non-existent key."""
        mock_db = MagicMock()
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = auth_service.revoke_api_key(mock_db, key_id=999)
        
        assert result is False
        mock_db.commit.assert_not_called()


class TestListApiKeys:
    """Tests for listing API keys."""

    def test_list_api_keys_all(self):
        """Test listing all API keys."""
        mock_db = MagicMock()
        mock_keys = [MagicMock(), MagicMock()]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_keys
        
        result = auth_service.list_api_keys(mock_db)
        
        assert len(result) == 2
    
    def test_list_api_keys_by_team(self):
        """Test listing API keys filtered by team."""
        mock_db = MagicMock()
        mock_keys = [MagicMock()]
        
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = mock_keys
        
        result = auth_service.list_api_keys(mock_db, team_id=1)
        
        assert len(result) == 1