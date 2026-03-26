"""
API Integration Tests: Cross-Metric Consistency

Tests that validate data consistency across different metric endpoints.
Ensures that creating metrics in one endpoint doesn't affect others incorrectly.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date


class TestCrossMetricDataIsolation:
    """Test that different metric types don't interfere with each other."""
    
    def test_all_metrics_for_single_project(self, postgres_client: TestClient):
        """
        API Flow: POST all metric types → GET all metric types → Validate isolation
        
        Validates:
        - Deployments, defects, and coverage are tracked independently
        - Each metric type returns correct data
        - No cross-contamination between metric types
        """
        project = "Full Stack Project"
        today = date.today()
        
        # Step 1: Create deployment metrics
        postgres_client.post("/api/v1/deployments", json={
            "project_name": project,
            "successful": True,
            "lead_time_hours": 2.0,
            "metric_date": str(today)
        })
        
        # Step 2: Create defect metrics
        postgres_client.post("/api/v1/defects", json={
            "project_name": project,
            "defect_id": "BUG-100",
            "priority": "high",
            "status": "open",
            "created_date": str(today)
        })
        
        # Step 3: Create coverage metrics
        postgres_client.post("/api/v1/coverage", json={
            "project_name": project,
            "line_coverage": 85.0,
            "branch_coverage": 78.0,
            "metric_date": str(today)
        })
        
        # Step 4: Retrieve all metric types
        dora_response = postgres_client.get(f"/api/v1/dora-metrics?project_name={project}")
        defect_response = postgres_client.get(f"/api/v1/defect-trends?project_name={project}")
        coverage_response = postgres_client.get(f"/api/v1/coverage-trends?project_name={project}")
        
        # Step 5: Validate each metric type
        assert dora_response.status_code == 200
        assert defect_response.status_code == 200
        assert coverage_response.status_code == 200
        
        dora_data = dora_response.json()
        defect_data = defect_response.json()
        coverage_data = coverage_response.json()
        
        # Validate DORA metrics
        assert len(dora_data) > 0
        assert dora_data[0]["successful_deployments"] == 1
        assert dora_data[0]["avg_lead_time_hours"] == 2.0
        
        # Validate defect trends
        assert len(defect_data) > 0
        assert defect_data[0]["defects_created"] == 1
        assert defect_data[0]["high_priority_defects"] == 1
        
        # Validate coverage trends
        assert len(coverage_data) > 0
        assert coverage_data[0]["avg_line_coverage"] == 85.0
        assert coverage_data[0]["avg_branch_coverage"] == 78.0
    
    def test_dashboard_query_workflow(self, postgres_client: TestClient):
        """
        API Flow: Simulate complete dashboard data fetch
        
        Workflow:
        1. Ingest all metric types for a project
        2. Query all endpoints as a dashboard would
        3. Validate complete dataset
        """
        project = "Dashboard Test"
        
        # Simulate 1 week of data ingestion
        for day in range(7):
            # Daily deployments
            postgres_client.post("/api/v1/deployments", json={
                "project_name": project,
                "successful": day % 3 != 0,  # Fail every 3rd day
                "lead_time_hours": 2.0 + (day * 0.1)
            })
            
            # Defects reported
            if day % 2 == 0:
                postgres_client.post("/api/v1/defects", json={
                    "project_name": project,
                    "defect_id": f"DB-{day}",
                    "priority": "high" if day < 3 else "medium",
                    "status": "open"
                })
        
        # Weekly coverage report
        postgres_client.post("/api/v1/coverage", json={
            "project_name": project,
            "line_coverage": 82.5,
            "branch_coverage": 75.0
        })
        
        # Dashboard query: Get all metrics
        dora = postgres_client.get(f"/api/v1/dora-metrics?project_name={project}")
        defects = postgres_client.get(f"/api/v1/defect-trends?project_name={project}")
        coverage = postgres_client.get(f"/api/v1/coverage-trends?project_name={project}")
        
        # Validate all endpoints return data
        assert dora.status_code == 200
        assert defects.status_code == 200
        assert coverage.status_code == 200
        
        assert len(dora.json()) > 0
        assert len(defects.json()) > 0
        assert len(coverage.json()) > 0


class TestTeamProjectConsistency:
    """Test team and project relationships across metrics."""
    
    def test_team_project_consistency_across_metrics(self, postgres_client: TestClient):
        """
        API Flow: Create metrics with team/project → Verify relationships
        
        Validates:
        - Teams and projects are auto-created consistently
        - Same team/project used across metric types
        """
        team = "Platform Engineering"
        project = "API Gateway"
        
        # Create deployment with team
        postgres_client.post("/api/v1/deployments", json={
            "project_name": project,
            "team_name": team,
            "successful": True
        })
        
        # Create defect (without team, should use existing project)
        postgres_client.post("/api/v1/defects", json={
            "project_name": project,
            "defect_id": "PLAT-1",
            "priority": "high",
            "status": "open"
        })
        
        # Create coverage (without team, should use existing project)
        postgres_client.post("/api/v1/coverage", json={
            "project_name": project,
            "line_coverage": 85.0,
            "branch_coverage": 78.0
        })
        
        # All should return data for same project
        dora = postgres_client.get(f"/api/v1/dora-metrics?project_name={project}")
        defects = postgres_client.get(f"/api/v1/defect-trends?project_name={project}")
        coverage = postgres_client.get(f"/api/v1/coverage-trends?project_name={project}")
        
        assert all([
            dora.status_code == 200,
            defects.status_code == 200,
            coverage.status_code == 200
        ])
        
        # Validate all metrics are for the same project
        assert dora.json()[0]["project_name"] == project
        assert defects.json()[0]["project_name"] == project  
        assert coverage.json()[0]["project_name"] == project