"""
Component Test: Health Check Endpoint

Tests the /health endpoint in isolation with test doubles.
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
    
    def test_health_check_no_database_required(self, component_client: TestClient):
        """Test health check works even if database operations would fail."""
        # Health check should not require database access
        # It should always return 200 if the API is running
        response = component_client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"