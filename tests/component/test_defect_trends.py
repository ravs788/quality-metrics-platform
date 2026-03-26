"""
Unit tests for defect trends summary endpoint.
"""

from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.services import DefectService


class TestDefectTrendsEndpoint:
    """Test GET /api/v1/defect-trends endpoint."""
    
    def test_get_defect_trends_empty(self, component_client: TestClient):
        """Test retrieving defect trends when no data exists."""
        response = component_client.get("/api/v1/defect-trends")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_defect_trends_with_data(self, component_client: TestClient, component_db: Session):
        """Test retrieving defect trends with data."""
        # Create some defect metrics
        defect_service = DefectService(component_db)
        defect_service.create_defect_metric(
            project_name="User Service",
            team_name="Backend Team",
            created_date=date(2026, 3, 15),
            resolved_date=date(2026, 3, 17),
            severity="high",
            status="resolved",
        )
        
        defect_service.create_defect_metric(
            project_name="User Service",
            team_name="Backend Team",
            created_date=date(2026, 3, 16),
            resolved_date=None,
            severity="medium",
            status="open",
        )
        
        # Commit the test data so the API can see it
        component_db.commit()
        
        response = component_client.get("/api/v1/defect-trends")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify structure + key calculations (mutation guards)
        first_item = data[0]
        assert "project_id" in first_item
        assert "project_name" in first_item
        assert "week_start" in first_item
        assert "defects_created" in first_item
        assert "high_priority_defects" in first_item
        assert "defects_resolved" in first_item
        assert "avg_resolution_time_hours" in first_item

        # Metrics are grouped by week_start (Monday).
        # 2026-03-15 is Sunday (week_start=2026-03-09) and 2026-03-16 is Monday (week_start=2026-03-16),
        # so we get two buckets. The endpoint sorts newest week first.
        assert first_item["week_start"] == "2026-03-16"
        assert first_item["defects_created"] == 1
        assert first_item["defects_resolved"] == 0
        assert first_item["avg_resolution_time_hours"] is None

        # Validate the older bucket as well (contains the resolved defect)
        older_item = data[1]
        assert older_item["week_start"] == "2026-03-09"
        assert older_item["defects_created"] == 1
        assert older_item["defects_resolved"] == 1
        assert older_item["avg_resolution_time_hours"] == 48.0
