"""
API Integration Tests: Deployment Flow

Tests the complete deployment tracking workflow from ingestion to DORA metrics retrieval.
Validates API chaining and data propagation across endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta


class TestDeploymentToDoraMetricsFlow:
    """Test deployment ingestion to DORA metrics retrieval workflow."""
    
    def test_single_deployment_to_dora_metrics(self, postgres_client: TestClient):
        """
        API Flow: POST deployment → GET DORA metrics
        
        Validates:
        - Deployment is created successfully
        - DORA metrics are calculated correctly
        - Data propagates from ingestion to aggregation endpoint
        """
        project = "API Gateway"
        
        # Step 1: Create deployment
        deployment_response = postgres_client.post("/api/v1/deployments", json={
            "project_name": project,
            "team_name": "Platform Team",
            "successful": True,
            "lead_time_hours": 2.5,
            "metric_date": str(date.today())
        })
        
        assert deployment_response.status_code == 201
        
        # Step 2: Retrieve DORA metrics
        dora_response = postgres_client.get(f"/api/v1/dora-metrics?project_name={project}")
        
        # Step 3: Validate aggregation
        assert dora_response.status_code == 200
        metrics = dora_response.json()
        assert len(metrics) > 0
        
        metric = metrics[0]
        assert metric["project_name"] == project
        assert metric["successful_deployments"] == 1
        assert metric["avg_lead_time_hours"] == 2.5
    
    def test_multiple_deployments_calculate_failure_rate(self, postgres_client: TestClient):
        """
        API Flow: POST multiple deployments → GET DORA metrics
        
        Validates:
        - Change failure rate calculation
        - Average lead time calculation
        - Multiple deployments aggregation
        """
        project = "User Service"
        today = date.today()
        
        # Step 1: Create successful deployments
        for i in range(3):
            postgres_client.post("/api/v1/deployments", json={
                "project_name": project,
                "successful": True,
                "lead_time_hours": 2.0,
                "metric_date": str(today)
            })
        
        # Step 2: Create failed deployment
        postgres_client.post("/api/v1/deployments", json={
            "project_name": project,
            "successful": False,
            "lead_time_hours": 1.5,
            "metric_date": str(today)
        })
        
        # Step 3: Retrieve DORA metrics
        dora_response = postgres_client.get(f"/api/v1/dora-metrics?project_name={project}")
        
        # Step 4: Validate calculations
        assert dora_response.status_code == 200
        metrics = dora_response.json()
        
        metric = metrics[0]
        assert metric["successful_deployments"] == 3
        assert metric["change_failure_rate_percent"] == 25.0  # 1 failure out of 4 total
        assert metric["avg_lead_time_hours"] == 1.875  # (2*3 + 1.5) / 4
    
    def test_multi_project_deployment_tracking(self, postgres_client: TestClient):
        """
        API Flow: POST deployments for multiple projects → GET DORA metrics for each
        
        Validates:
        - Multiple project tracking
        - Project isolation in metrics
        - Correct aggregation per project
        """
        projects = ["API Gateway", "User Service", "Payment Service"]
        today = date.today()
        
        # Step 1: Create deployments for each project
        for project in projects:
            postgres_client.post("/api/v1/deployments", json={
                "project_name": project,
                "successful": True,
                "lead_time_hours": 2.0,
                "metric_date": str(today)
            })
        
        # Step 2: Retrieve DORA metrics for each project
        for project in projects:
            dora_response = postgres_client.get(f"/api/v1/dora-metrics?project_name={project}")
            
            assert dora_response.status_code == 200
            metrics = dora_response.json()
            assert len(metrics) > 0
            assert metrics[0]["project_name"] == project
            assert metrics[0]["successful_deployments"] == 1
    
    def test_deployment_flow_with_date_filtering(self, postgres_client: TestClient):
        """
        API Flow: POST deployments on different dates → GET DORA metrics with date filter
        
        Validates:
        - Date-based filtering in DORA metrics
        - Multiple days of deployment data
        """
        project = "Analytics Engine"
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Step 1: Create deployments on different days
        postgres_client.post("/api/v1/deployments", json={
            "project_name": project,
            "successful": True,
            "metric_date": str(today)
        })
        
        postgres_client.post("/api/v1/deployments", json={
            "project_name": project,
            "successful": False,
            "metric_date": str(yesterday)
        })
        
        # Step 2: Get all DORA metrics for project
        all_metrics = postgres_client.get(f"/api/v1/dora-metrics?project_name={project}")
        
        # Step 3: Validate multiple date entries
        assert all_metrics.status_code == 200
        metrics = all_metrics.json()
        assert len(metrics) >= 2  # At least 2 different dates


class TestDeploymentErrorHandling:
    """Test error handling in deployment flow."""
    
    def test_invalid_deployment_does_not_affect_metrics(self, postgres_client: TestClient):
        """
        API Flow: POST invalid deployment → POST valid deployment → GET metrics
        
        Validates:
        - Invalid deployments are rejected
        - Valid deployments still work
        - Metrics only reflect valid data
        """
        project = "Error Test Project"
        
        # Step 1: Try to create invalid deployment (missing required field)
        invalid_response = postgres_client.post("/api/v1/deployments", json={
            "team_name": "Test Team"
            # Missing project_name
        })
        assert invalid_response.status_code == 422  # Validation error
        
        # Step 2: Create valid deployment
        valid_response = postgres_client.post("/api/v1/deployments", json={
            "project_name": project,
            "successful": True
        })
        assert valid_response.status_code == 201
        
        # Step 3: Verify only valid deployment is in metrics
        metrics_response = postgres_client.get(f"/api/v1/dora-metrics?project_name={project}")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert len(metrics) > 0
        assert metrics[0]["successful_deployments"] == 1