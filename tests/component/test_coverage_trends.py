"""
Unit tests for coverage trends summary endpoint.
"""

from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.services import CoverageService


class TestCoverageTrendsEndpoint:
    """Test GET /api/v1/coverage-trends endpoint."""
    
    def test_get_coverage_trends_empty(self, component_client: TestClient):
        """Test retrieving coverage trends when no data exists."""
        response = component_client.get("/api/v1/coverage-trends")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_coverage_trends_with_data(self, component_client: TestClient, component_db: Session):
        """Test retrieving coverage trends with data."""
        # Create some coverage metrics
        coverage_service = CoverageService(component_db)
        coverage_service.create_coverage_metric(
            project_name="Web Dashboard",
            team_name="Frontend Team",
            week_start=date(2026, 3, 17),
            line_coverage_percent=85.5,
            branch_coverage_percent=78.3,
        )
        
        coverage_service.create_coverage_metric(
            project_name="Web Dashboard",
            team_name="Frontend Team",
            week_start=date(2026, 3, 17),
            line_coverage_percent=87.0,
            branch_coverage_percent=80.0,
        )
        
        # Commit the test data so the API can see it
        component_db.commit()
        
        response = component_client.get("/api/v1/coverage-trends")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify structure + key calculations (mutation guards)
        first_item = data[0]
        assert "project_id" in first_item
        assert "project_name" in first_item
        assert "week_start" in first_item
        assert "avg_line_coverage" in first_item
        assert "avg_branch_coverage" in first_item
        assert "max_line_coverage" in first_item
        assert "min_line_coverage" in first_item

        # Two snapshots: lines=[85.5, 87.0] => avg=86.25, max=87.0, min=85.5
        assert first_item["avg_line_coverage"] == 86.25
        assert first_item["max_line_coverage"] == 87.0
        assert first_item["min_line_coverage"] == 85.5

        # branches=[78.3, 80.0] => avg=79.15
        assert first_item["avg_branch_coverage"] == 79.15
