"""
End-to-End Test: CI/CD Pipeline Simulation

Simulates a complete CI/CD pipeline tracking scenario across multiple days.
Tests the entire system from data ingestion through dashboard queries.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
import random


class TestCompleteCICDTracking:
    """E2E test simulating real CI/CD pipeline tracking workflow."""
    
    def test_one_week_cicd_pipeline_workflow(self, e2e_client: TestClient):
        """
        E2E: Simulate 1 week of CI/CD pipeline activity
        
        Scenario:
        1. Team deploys to production multiple times daily (some succeed, some fail)
        2. QA reports defects found in production
        3. Team updates test coverage metrics
        4. Engineering manager queries dashboard for all metrics
        
        Validates complete system integration and data consistency.
        """
        project = "Payment Service"
        team = "Backend Team"
        today = date.today()
        
        # Simulate 1 week of deployments (3 per day, varying success rate)
        deployment_count = 0
        successful_deployments = 0
        failed_deployments = 0
        
        for day in range(7):
            metric_date = today - timedelta(days=day)
            
            for deployment_num in range(3):
                # 80% success rate
                successful = random.random() > 0.2
                if successful:
                    successful_deployments += 1
                else:
                    failed_deployments += 1
                
                response = e2e_client.post("/api/v1/deployments", json={
                    "project_name": project,
                    "team_name": team,
                    "successful": successful,
                    "lead_time_hours": random.uniform(1.0, 4.0),
                    "metric_date": str(metric_date)
                })
                assert response.status_code == 201
                deployment_count += 1
        
        # Simulate defects discovered during the week
        defect_count = 0
        high_priority_count = 0
        
        for defect_num in range(8):
            priority = "high" if defect_num < 3 else "medium"
            if priority == "high":
                high_priority_count += 1
            
            status = "resolved" if defect_num < 4 else "open"
            resolution_time = random.uniform(24.0, 72.0) if status == "resolved" else None
            
            payload = {
                "project_name": project,
                "defect_id": f"PROD-{defect_num}",
                "priority": priority,
                "status": status,
                "created_date": str(today - timedelta(days=defect_num % 7))
            }
            
            if resolution_time:
                payload["resolution_time_hours"] = resolution_time
            
            response = e2e_client.post("/api/v1/defects", json=payload)
            assert response.status_code == 201
            defect_count += 1
        
        # Simulate weekly coverage report
        coverage_response = e2e_client.post("/api/v1/coverage", json={
            "project_name": project,
            "line_coverage": 85.5,
            "branch_coverage": 78.0,
            "metric_date": str(today)
        })
        assert coverage_response.status_code == 201
        
        # Manager queries dashboard - get all metrics
        dora_response = e2e_client.get(f"/api/v1/dora-metrics?project_name={project}")
        defect_response = e2e_client.get(f"/api/v1/defect-trends?project_name={project}")
        coverage_response = e2e_client.get(f"/api/v1/coverage-trends?project_name={project}")
        
        # Validate all endpoints return data
        assert dora_response.status_code == 200
        assert defect_response.status_code == 200
        assert coverage_response.status_code == 200
        
        # Validate DORA metrics reflect deployments
        dora_data = dora_response.json()
        assert len(dora_data) > 0
        
        # Total deployments should match across all days
        total_deployments_in_metrics = sum(
            m["successful_deployments"] + 
            (m["total_deployments"] - m["successful_deployments"])
            for m in dora_data
        )
        assert total_deployments_in_metrics == deployment_count
        
        # Validate defect trends
        defect_data = defect_response.json()
        assert len(defect_data) > 0
        assert defect_data[0]["defects_created"] == defect_count
        
        # Validate coverage trends
        coverage_data = coverage_response.json()
        assert len(coverage_data) > 0
        assert coverage_data[0]["avg_line_coverage"] == 85.5


class TestMultiTeamProductionScenario:
    """E2E test with multiple teams and projects."""
    
    def test_multi_team_dashboard(self, e2e_client: TestClient, e2e_test_data):
        """
        E2E: Multiple teams using the platform simultaneously
        
        Scenario:
        1. Three teams (Platform, Backend, Frontend) each have projects
        2. Each team deploys, reports defects, and tracks coverage
        3. Platform-wide dashboard shows all team metrics
        
        Validates multi-tenancy and data isolation.
        """
        teams_data = e2e_test_data["teams"]
        projects_data = e2e_test_data["projects"]
        
        # Each team's project generates metrics
        for project in projects_data:
            project_name = project.project_name
            
            # Create deployments
            e2e_client.post("/api/v1/deployments", json={
                "project_name": project_name,
                "successful": True,
                "lead_time_hours": 2.0
            })
            
            # Create defects
            e2e_client.post("/api/v1/defects", json={
                "project_name": project_name,
                "defect_id": f"{project_name}-BUG-1",
                "priority": "high",
                "status": "open"
            })
            
            # Create coverage
            e2e_client.post("/api/v1/coverage", json={
                "project_name": project_name,
                "line_coverage": 80.0 + random.uniform(0, 10),
                "branch_coverage": 75.0
            })
        
        # Query platform-wide metrics (no project filter)
        all_dora = e2e_client.get("/api/v1/dora-metrics")
        all_defects = e2e_client.get("/api/v1/defect-trends")
        all_coverage = e2e_client.get("/api/v1/coverage-trends")
        
        # Validate all teams' data is present
        assert all_dora.status_code == 200
        assert len(all_dora.json()) >= len(projects_data)
        
        assert all_defects.status_code == 200
        assert len(all_defects.json()) >= len(projects_data)
        
        assert all_coverage.status_code == 200
        assert len(all_coverage.json()) >= len(projects_data)
        
        # Validate project isolation - query specific project
        specific_project = projects_data[0].project_name
        project_dora = e2e_client.get(f"/api/v1/dora-metrics?project_name={specific_project}")
        
        assert project_dora.status_code == 200
        project_metrics = project_dora.json()
        # All returned metrics should be for the requested project
        assert all(m["project_name"] == specific_project for m in project_metrics)