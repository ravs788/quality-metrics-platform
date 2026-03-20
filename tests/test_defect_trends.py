"""
Unit tests for defect trends summary endpoint.
"""

from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.crud import create_defect_metric


class TestDefectTrendsEndpoint:
    """Test GET /api/v1/defect-trends endpoint."""
    
    def test_get_defect_trends_empty(self, client: TestClient):
        """Test retrieving defect trends when no data exists."""
        response = client.get("/api/v1/defect-trends")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_defect_trends_with_data(self, client: TestClient, test_db: Session):
        """Test retrieving defect trends with data."""
        # Create some defect metrics
        create_defect_metric(
            db=test_db,
            project_name="User Service",
            team_name="Backend Team",
            created_date=date(2026, 3, 15),
            resolved_date=date(2026, 3, 17),
            severity="high",
            status="resolved",
        )
        
        create_defect_metric(
            db=test_db,
            project_name="User Service",
            team_name="Backend Team",
            created_date=date(2026, 3, 16),
            resolved_date=None,
            severity="medium",
            status="open",
        )
        
        response = client.get("/api/v1/defect-trends")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify structure
        first_item = data[0]
        assert "project_id" in first_item
        assert "project_name" in first_item
        assert "week_start" in first_item
        assert "defects_created" in first_item
        assert "high_priority_defects" in first_item
        assert "defects_resolved" in first_item
        assert "avg_resolution_time_hours" in first_item
