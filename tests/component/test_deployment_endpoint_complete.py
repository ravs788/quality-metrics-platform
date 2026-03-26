"""
Unit tests for deployment metrics endpoint.
"""

from datetime import date
from fastapi.testclient import TestClient


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
