"""
Unit tests for deployment metrics endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.db_models import Team
from src.services import auth_service


class TestDeploymentsEndpoint:
    """Test POST /api/v1/deployments endpoint."""
    
    def test_create_deployment_success(self, component_client: TestClient):
        """Test creating a deployment metric."""
        payload = {
            "project_name": "API Gateway",
            "team_name": "Platform Team",
            "metric_date": "2026-03-18",
            "successful": True,
            "lead_time_hours": 2.5
        }
        
        response = component_client.post("/api/v1/deployments", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "API Gateway"
        assert data["team_name"] == "Platform Team"
        assert data["successful"] is True
        assert data["lead_time_hours"] == 2.5
        assert "id" in data
        assert "created_at" in data
    
    def test_create_deployment_failed(self, component_client: TestClient):
        """Test creating a failed deployment metric."""
        payload = {
            "project_name": "User Service",
            "team_name": "Backend Team",
            "metric_date": "2026-03-18",
            "successful": False,
            "lead_time_hours": 1.0
        }
        
        response = component_client.post("/api/v1/deployments", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["successful"] is False
    
    def test_create_deployment_minimal_data(self, component_client: TestClient):
        """Test creating deployment with minimal required data."""
        payload = {
            "project_name": "Mobile App",
            "successful": True
        }
        
        response = component_client.post("/api/v1/deployments", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "Mobile App"
    
    def test_create_deployment_invalid_data(self, component_client: TestClient):
        """Test validation error on invalid data."""
        payload = {
            "team_name": "Test Team"
            # Missing required project_name
        }
        
        response = component_client.post("/api/v1/deployments", json=payload)
        
        assert response.status_code == 422  # Validation error


class TestGitHubActionsDeploymentsEndpoint:
    """Test POST /api/v1/deployments/github-actions endpoint."""

    @pytest.fixture
    def github_ingestion_key(self, component_db: Session):
        """Create a non-admin API key for GitHub Actions ingestion."""
        team = Team(team_name="GitHub Actions Team", team_lead="Pipeline Lead")
        component_db.add(team)
        component_db.commit()
        component_db.refresh(team)

        _, plaintext_key = auth_service.create_api_key(
            db=component_db,
            team_id=team.team_id,
            key_name="GitHub Actions Ingestion",
            is_admin=False,
            created_by="ci-bot@github-actions"
        )
        return plaintext_key

    def test_github_actions_ingestion_requires_auth(self, component_client: TestClient):
        """Test GitHub Actions ingestion endpoint requires API key auth."""
        payload = {
            "repository": "acme/api-gateway",
            "run_id": 101,
            "status": "completed",
            "conclusion": "success",
            "run_started_at": "2026-03-27T10:30:00Z"
        }

        response = component_client.post("/api/v1/deployments/github-actions", json=payload)

        assert response.status_code == 401

    def test_github_actions_ingestion_success(self, component_client: TestClient, github_ingestion_key: str):
        """Test successful GitHub Actions deployment ingestion and repository-to-project mapping."""
        payload = {
            "repository": "acme/api-gateway",
            "run_id": 102,
            "status": "completed",
            "conclusion": "success",
            "run_started_at": "2026-03-27T10:30:00Z",
            "team_name": "Platform Team",
            "lead_time_hours": 1.75
        }

        response = component_client.post(
            "/api/v1/deployments/github-actions",
            json=payload,
            headers={"Authorization": f"Bearer {github_ingestion_key}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "api-gateway"
        assert data["team_name"] == "Platform Team"
        assert data["metric_date"] == "2026-03-27"
        assert data["successful"] is True
        assert data["lead_time_hours"] == 1.75

    def test_github_actions_ingestion_uses_project_override(self, component_client: TestClient, github_ingestion_key: str):
        """Test explicit project_name overrides repository-derived project mapping."""
        payload = {
            "repository": "acme/api-gateway",
            "run_id": 103,
            "status": "completed",
            "conclusion": "failure",
            "run_started_at": "2026-03-27T10:30:00Z",
            "project_name": "API Gateway Service"
        }

        response = component_client.post(
            "/api/v1/deployments/github-actions",
            json=payload,
            headers={"Authorization": f"Bearer {github_ingestion_key}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "API Gateway Service"
        assert data["successful"] is False

    def test_github_actions_ingestion_requires_conclusion_for_completed(self, component_client: TestClient, github_ingestion_key: str):
        """Test payload validation enforces conclusion for completed runs."""
        payload = {
            "repository": "acme/api-gateway",
            "run_id": 104,
            "status": "completed",
            "run_started_at": "2026-03-27T10:30:00Z"
        }

        response = component_client.post(
            "/api/v1/deployments/github-actions",
            json=payload,
            headers={"Authorization": f"Bearer {github_ingestion_key}"}
        )

        assert response.status_code == 422
