"""
Unit tests for health check endpoint.
"""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test the /health endpoint."""
    
    def test_health_check_returns_200(self, component_client: TestClient):
        """Test health check endpoint returns 200 OK."""
        response = component_client.get("/health")
        
        assert response.status_code == 200
    
    def test_health_check_response_format(self, component_client: TestClient):
        """Test health check response has correct format."""
        response = component_client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "message" in data
        assert data["status"] == "ok"
        assert "Quality Metrics Platform" in data["message"]
