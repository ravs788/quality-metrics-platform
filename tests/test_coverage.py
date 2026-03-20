"""
Unit tests for coverage metrics endpoint.
"""

from datetime import date
from fastapi.testclient import TestClient


class TestCoverageEndpoint:
    """Test POST /api/v1/coverage endpoint."""
    
    def test_create_coverage_metric(self, client: TestClient):
        """Test creating a coverage metric."""
        payload = {
            "project_name": "Web Dashboard",
            "team_name": "Frontend Team",
            "week_start": "2026-03-17",
            "line_coverage_percent": 85.5,
            "branch_coverage_percent": 78.3
        }
        
        response = client.post("/api/v1/coverage", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "Web Dashboard"
        assert data["line_coverage_percent"] == 85.5
        assert data["branch_coverage_percent"] == 78.3
        assert "id" in data
        assert "created_at" in data
    
    def test_create_coverage_partial_data(self, client: TestClient):
        """Test creating coverage with partial data."""
        payload = {
            "project_name": "Mobile App",
            "team_name": "Mobile Team",
            "line_coverage_percent": 90.0
        }
        
        response = client.post("/api/v1/coverage", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["line_coverage_percent"] == 90.0
        assert data["branch_coverage_percent"] is None
    
    def test_create_coverage_minimal_data(self, client: TestClient):
        """Test creating coverage with minimal required data."""
        payload = {
            "project_name": "Analytics Engine"
        }
        
        response = client.post("/api/v1/coverage", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "Analytics Engine"
    
    def test_create_coverage_invalid_data(self, client: TestClient):
        """Test validation error on invalid data."""
        payload = {
            "line_coverage_percent": 85.0
            # Missing required project_name
        }
        
        response = client.post("/api/v1/coverage", json=payload)
        
        assert response.status_code == 422
