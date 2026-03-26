"""
API Integration Tests: Coverage Workflow

Tests the complete coverage tracking workflow from ingestion to trend analysis.
Validates weekly bucketing and coverage evolution tracking.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta


class TestCoverageToTrendsFlow:
    """Test coverage ingestion to trend analysis workflow."""
    
    def test_coverage_ingestion_to_trends(self, postgres_client: TestClient):
        """
        API Flow: POST coverage → GET coverage trends
        
        Validates:
        - Coverage data is created successfully
        - Trends are calculated with weekly bucketing
        - Line and branch coverage are tracked separately
        """
        project = "API Gateway"
        
        # Step 1: Create coverage metric
        coverage_response = postgres_client.post("/api/v1/coverage", json={
            "project_name": project,
            "line_coverage": 85.5,
            "branch_coverage": 78.0,
            "metric_date": str(date.today())
        })
        
        assert coverage_response.status_code == 201
        
        # Step 2: Get coverage trends
        trends_response = postgres_client.get(f"/api/v1/coverage-trends?project_name={project}")
        
        # Step 3: Validate trends
        assert trends_response.status_code == 200
        trends = trends_response.json()
        assert len(trends) > 0
        
        trend = trends[0]
        assert trend["project_name"] == project
        assert trend["avg_line_coverage"] == 85.5
        assert trend["avg_branch_coverage"] == 78.0
    
    def test_coverage_evolution_over_weeks(self, postgres_client: TestClient):
        """
        API Flow: POST coverage over multiple weeks → GET trends → Validate evolution
        
        Validates:
        - Weekly bucketing of coverage data
        - Average calculation per week
        - Coverage improvement tracking
        """
        project = "User Service"
        today = date.today()
        
        # Simulate 3 weeks of coverage improvement
        weeks_data = [
            {"week_offset": 0, "line": 75.0, "branch": 68.0},
            {"week_offset": 7, "line": 80.0, "branch": 73.0},
            {"week_offset": 14, "line": 85.0, "branch": 78.0},
        ]
        
        # Step 1: Create coverage data for each week
        for week in weeks_data:
            metric_date = today - timedelta(days=week["week_offset"])
            postgres_client.post("/api/v1/coverage", json={
                "project_name": project,
                "line_coverage": week["line"],
                "branch_coverage": week["branch"],
                "metric_date": str(metric_date)
            })
        
        # Step 2: Get coverage trends
        trends_response = postgres_client.get(f"/api/v1/coverage-trends?project_name={project}")
        
        # Step 3: Validate weekly bucketing
        assert trends_response.status_code == 200
        trends = trends_response.json()
        assert len(trends) >= 3  # At least 3 weeks
        
        # Validate coverage improvement trend (most recent first)
        assert trends[0]["avg_line_coverage"] >= trends[1]["avg_line_coverage"]
    
    def test_multiple_coverage_entries_same_week(self, postgres_client: TestClient):
        """
        API Flow: POST multiple coverage entries in same week → GET trends → Validate averaging
        
        Validates:
        - Multiple entries in same week are averaged
        - Weekly bucketing groups correctly
        """
        project = "Payment Service"
        today = date.today()
        
        # Step 1: Create multiple coverage entries within same week
        coverage_values = [80.0, 82.0, 84.0]
        
        for i, coverage in enumerate(coverage_values):
            # All within same week
            metric_date = today - timedelta(days=i)
            postgres_client.post("/api/v1/coverage", json={
                "project_name": project,
                "line_coverage": coverage,
                "branch_coverage": 75.0,
                "metric_date": str(metric_date)
            })
        
        # Step 2: Get trends
        trends_response = postgres_client.get(f"/api/v1/coverage-trends?project_name={project}")
        
        # Step 3: Validate averaging
        assert trends_response.status_code == 200
        trends = trends_response.json()
        
        # Should have one entry with averaged values
        trend = trends[0]
        expected_avg = sum(coverage_values) / len(coverage_values)
        assert abs(trend["avg_line_coverage"] - expected_avg) < 0.1  # Allow small floating point difference


class TestCoverageProjectIsolation:
    """Test coverage isolation between projects."""
    
    def test_multi_project_coverage_tracking(self, postgres_client: TestClient):
        """
        API Flow: POST coverage for multiple projects → GET trends per project
        
        Validates:
        - Coverage data is isolated per project
        - Trends calculated correctly per project
        """
        projects = {
            "API Gateway": 85.0,
            "User Service": 90.0,
            "Web Dashboard": 78.0
        }
        
        # Step 1: Create coverage for each project
        for project, coverage in projects.items():
            postgres_client.post("/api/v1/coverage", json={
                "project_name": project,
                "line_coverage": coverage,
                "branch_coverage": 75.0
            })
        
        # Step 2: Verify trends for each project
        for project, expected_coverage in projects.items():
            trends_response = postgres_client.get(f"/api/v1/coverage-trends?project_name={project}")
            
            assert trends_response.status_code == 200
            trends = trends_response.json()
            assert len(trends) > 0
            assert trends[0]["avg_line_coverage"] == expected_coverage