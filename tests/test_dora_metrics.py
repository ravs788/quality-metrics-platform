"""
Unit tests for DORA metrics summary endpoint.
"""

from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.crud import create_deployment_metric


class TestDoraMetricsEndpoint:
    """Test GET /api/v1/dora-metrics endpoint."""
    
    def test_get_dora_metrics_empty(self, client: TestClient):
        """Test retrieving DORA metrics when no data exists."""
        response = client.get("/api/v1/dora-metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_dora_metrics_with_data(self, client: TestClient, test_db: Session):
        """Test retrieving DORA metrics with data."""
        # Create some deployment metrics
        create_deployment_metric(
            db=test_db,
            project_name="API Gateway",
            team_name="Platform Team",
            metric_date=date(2026, 3, 18),
            successful=True,
            lead_time_hours=2.5,
        )
        
        create_deployment_metric(
            db=test_db,
            project_name="API Gateway",
            team_name="Platform Team",
            metric_date=date(2026, 3, 18),
            successful=False,
            lead_time_hours=1.0,
        )
        
        response = client.get("/api/v1/dora-metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify structure + key calculations (mutation guards)
        first_item = data[0]
        assert "project_id" in first_item
        assert "project_name" in first_item
        assert "team_name" in first_item
        assert "metric_date" in first_item
        assert "successful_deployments" in first_item
        assert "failed_deployments" in first_item
        assert "avg_lead_time_hours" in first_item
        assert "change_failure_rate_percent" in first_item

        # successful=1, failed=1 => total=2 => change failure rate = 50%
        assert first_item["successful_deployments"] == 1
        assert first_item["failed_deployments"] == 1
        assert first_item["change_failure_rate_percent"] == 50.0
