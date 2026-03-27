"""
Component tests for API key management endpoints.

Tests the admin router endpoints for creating, listing, and revoking API keys.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.db_models import Team, ApiKey
from src.services import auth_service


class TestApiKeyEndpoints:
    """Tests for API key management endpoints."""

    @pytest.fixture
    def test_team(self, component_db: Session):
        """Create a test team for API key tests."""
        team = Team(team_name="Test Team", team_lead="Test Lead")
        component_db.add(team)
        component_db.commit()
        component_db.refresh(team)
        return team

    @pytest.fixture
    def admin_key(self, component_db: Session, test_team: Team):
        """Create an admin API key for testing."""
        api_key_obj, plaintext_key = auth_service.create_api_key(
            db=component_db,
            team_id=test_team.team_id,
            key_name="Admin Key",
            is_admin=True,
            created_by="test@example.com"
        )
        return plaintext_key

    @pytest.fixture
    def regular_key(self, component_db: Session, test_team: Team):
        """Create a regular (non-admin) API key for testing."""
        api_key_obj, plaintext_key = auth_service.create_api_key(
            db=component_db,
            team_id=test_team.team_id,
            key_name="Regular Key",
            is_admin=False,
            created_by="user@example.com"
        )
        return plaintext_key

    def test_create_api_key_success(self, component_client, test_team, admin_key):
        """Test successful API key creation."""
        response = component_client.post(
            "/api/v1/api-keys",
            json={
                "team_id": test_team.team_id,
                "key_name": "New CI/CD Key",
                "is_admin": False,
                "created_by": "admin@example.com"
            },
            headers={"Authorization": f"Bearer {admin_key}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["key_name"] == "New CI/CD Key"
        assert data["team_id"] == test_team.team_id
        assert data["is_admin"] is False
        assert data["is_active"] is True
        assert "api_key" in data  # Plaintext key returned
        assert data["api_key"].startswith("qmp_")

    def test_create_api_key_requires_admin(self, component_client, test_team, regular_key):
        """Test that creating API key requires admin authentication."""
        response = component_client.post(
            "/api/v1/api-keys",
            json={
                "team_id": test_team.team_id,
                "key_name": "Attempted Key",
                "is_admin": False
            },
            headers={"Authorization": f"Bearer {regular_key}"}
        )
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_create_api_key_no_auth(self, component_client, test_team):
        """Test that creating API key requires authentication."""
        response = component_client.post(
            "/api/v1/api-keys",
            json={
                "team_id": test_team.team_id,
                "key_name": "No Auth Key",
                "is_admin": False
            }
        )
        
        assert response.status_code == 401

    def test_create_api_key_invalid_team(self, component_client, admin_key):
        """Test creating API key for non-existent team."""
        response = component_client.post(
            "/api/v1/api-keys",
            json={
                "team_id": 99999,
                "key_name": "Invalid Team Key",
                "is_admin": False
            },
            headers={"Authorization": f"Bearer {admin_key}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_api_keys(self, component_client, admin_key):
        """Test listing API keys."""
        response = component_client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {admin_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the admin key
        assert len(data) >= 1

    def test_list_api_keys_requires_admin(self, component_client, regular_key):
        """Test that listing API keys requires admin authentication."""
        response = component_client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {regular_key}"}
        )
        
        assert response.status_code == 403

    def test_list_api_keys_filter_by_team(self, component_client, test_team, admin_key):
        """Test filtering API keys by team."""
        response = component_client.get(
            f"/api/v1/api-keys?team_id={test_team.team_id}",
            headers={"Authorization": f"Bearer {admin_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        for key in data:
            assert key["team_id"] == test_team.team_id

    def test_revoke_api_key(self, component_client, component_db, test_team, admin_key):
        """Test revoking an API key."""
        # Create a key to revoke
        api_key_obj, _ = auth_service.create_api_key(
            db=component_db,
            team_id=test_team.team_id,
            key_name="Key to Revoke",
            is_admin=False
        )
        
        response = component_client.delete(
            f"/api/v1/api-keys/{api_key_obj.key_id}",
            headers={"Authorization": f"Bearer {admin_key}"}
        )
        
        assert response.status_code == 204
        
        # Verify key is revoked (need to expire all to reload)
        component_db.expire_all()
        assert api_key_obj.is_active is False
        assert api_key_obj.revoked_at is not None

    def test_revoke_api_key_not_found(self, component_client, admin_key):
        """Test revoking non-existent API key."""
        response = component_client.delete(
            "/api/v1/api-keys/99999",
            headers={"Authorization": f"Bearer {admin_key}"}
        )
        
        assert response.status_code == 404

    def test_revoke_api_key_requires_admin(self, component_client, component_db, test_team, regular_key):
        """Test that revoking API key requires admin authentication."""
        # Create a key to attempt to revoke
        api_key_obj, _ = auth_service.create_api_key(
            db=component_db,
            team_id=test_team.team_id,
            key_name="Protected Key",
            is_admin=False
        )
        
        response = component_client.delete(
            f"/api/v1/api-keys/{api_key_obj.key_id}",
            headers={"Authorization": f"Bearer {regular_key}"}
        )
        
        assert response.status_code == 403


class TestAuthenticationFlow:
    """Tests for authentication flow using API keys."""

    @pytest.fixture
    def test_team(self, component_db: Session):
        """Create a test team."""
        team = Team(team_name="Auth Flow Team", team_lead="Test Lead")
        component_db.add(team)
        component_db.commit()
        component_db.refresh(team)
        return team

    def test_invalid_bearer_format(self, component_client, component_db, test_team):
        """Test that invalid bearer format is rejected."""
        # Create an admin key first
        api_key_obj, plaintext_key = auth_service.create_api_key(
            db=component_db,
            team_id=test_team.team_id,
            key_name="Test Key",
            is_admin=True
        )
        
        # Try with wrong format (no "Bearer " prefix)
        response = component_client.get(
            "/api/v1/api-keys",
            headers={"Authorization": plaintext_key}
        )
        
        assert response.status_code == 401
        assert "Invalid authorization header format" in response.json()["detail"]

    def test_revoked_key_rejected(self, component_client, component_db, test_team):
        """Test that revoked API key is rejected."""
        # Create and revoke an admin key
        api_key_obj, plaintext_key = auth_service.create_api_key(
            db=component_db,
            team_id=test_team.team_id,
            key_name="Revoked Key",
            is_admin=True
        )
        auth_service.revoke_api_key(component_db, api_key_obj.key_id)
        
        # Try to use revoked key
        response = component_client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {plaintext_key}"}
        )
        
        assert response.status_code == 401
        assert "Invalid or inactive" in response.json()["detail"]

    def test_invalid_key_rejected(self, component_client):
        """Test that invalid API key is rejected."""
        response = component_client.get(
            "/api/v1/api-keys",
            headers={"Authorization": "Bearer qmp_invalid_key_12345678901234"}
        )
        
        assert response.status_code == 401