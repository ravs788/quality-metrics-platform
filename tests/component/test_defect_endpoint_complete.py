"""
Unit tests for defect metrics endpoint.
"""

from datetime import date
from fastapi.testclient import TestClient


class TestDefectsEndpoint:
    """Test POST /api/v1/defects endpoint."""
    
    def test_create_defect_open(self, component_client: TestClient):
        """Test creating an open defect metric."""
        payload = {
            "project_name": "User Service",
            "team_name": "Backend Team",
            "created_date": "2026-03-15",
            "severity": "high",
            "status": "open"
        }
        
        response = component_client.post("/api/v1/defects", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "User Service"
        assert data["severity"] == "high"
        assert data["status"] == "open"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_defect_resolved(self, component_client: TestClient):
        """Test creating a resolved defect metric."""
        payload = {
            "project_name": "API Gateway",
            "team_name": "Platform Team",
            "created_date": "2026-03-15",
            "resolved_date": "2026-03-17",
            "severity": "medium",
            "status": "resolved"
        }
        
        response = component_client.post("/api/v1/defects", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "resolved"
        assert data["resolved_date"] is not None
    
    def test_create_defect_minimal_data(self, component_client: TestClient):
        """Test creating defect with minimal required data."""
        payload = {
            "project_name": "Web Dashboard"
        }
        
        response = component_client.post("/api/v1/defects", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "Web Dashboard"
    
    def test_create_defect_invalid_data(self, component_client: TestClient):
        """Test validation error on invalid data."""
        payload = {
            "severity": "high"
            # Missing required project_name
        }
        
        response = component_client.post("/api/v1/defects", json=payload)
        
        assert response.status_code == 422
