"""
API Integration Tests: Defect Lifecycle

Tests the complete defect tracking workflow from creation to trend analysis.
Validates API chaining and defect state transitions.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date


class TestDefectToTrendsFlow:
    """Test defect creation to trend analysis workflow."""
    
    def test_defect_creation_to_trends(self, postgres_client: TestClient):
        """
        API Flow: POST defects → GET defect trends
        
        Validates:
        - Defects are created successfully
        - Trends are calculated correctly
        - Priority distribution is accurate
        """
        project = "User Service"
        today = date.today()
        
        # Step 1: Create high-priority defect
        postgres_client.post("/api/v1/defects", json={
            "project_name": project,
            "defect_id": "BUG-001",
            "priority": "high",
            "status": "open",
            "created_date": str(today)
        })
        
        # Step 2: Create medium-priority resolved defect
        postgres_client.post("/api/v1/defects", json={
            "project_name": project,
            "defect_id": "BUG-002",
            "priority": "medium",
            "status": "resolved",
            "created_date": str(today),
            "resolution_time_hours": 48.0
        })
        
        # Step 3: Create low-priority defect
        postgres_client.post("/api/v1/defects", json={
            "project_name": project,
            "defect_id": "BUG-003",
            "priority": "low",
            "status": "open",
            "created_date": str(today)
        })
        
        # Step 4: Get defect trends
        trends_response = postgres_client.get(f"/api/v1/defect-trends?project_name={project}")
        
        # Step 5: Validate calculations
        assert trends_response.status_code == 200
        trends = trends_response.json()
        assert len(trends) > 0
        
        trend = trends[0]
        assert trend["defects_created"] == 3
        assert trend["high_priority_defects"] == 1
        assert trend["avg_resolution_time_hours"] == 48.0
    
    def test_defect_resolution_workflow(self, postgres_client: TestClient):
        """
        API Flow: POST open defects → POST resolved defects → GET trends
        
        Validates:
        - Open vs resolved defect tracking
        - Resolution time calculation
        - Average resolution metrics
        """
        project = "Payment Service"
        
        # Step 1: Create multiple open defects
        for i in range(5):
            postgres_client.post("/api/v1/defects", json={
                "project_name": project,
                "defect_id": f"PAY-{i+1}",
                "priority": "high" if i < 2 else "medium",
                "status": "open"
            })
        
        # Step 2: Resolve some defects with different resolution times
        postgres_client.post("/api/v1/defects", json={
            "project_name": project,
            "defect_id": "PAY-RESOLVED-1",
            "priority": "high",
            "status": "resolved",
            "resolution_time_hours": 24.0
        })
        
        postgres_client.post("/api/v1/defects", json={
            "project_name": project,
            "defect_id": "PAY-RESOLVED-2",
            "priority": "medium",
            "status": "resolved",
            "resolution_time_hours": 72.0
        })
        
        # Step 3: Get trends
        trends_response = postgres_client.get(f"/api/v1/defect-trends?project_name={project}")
        
        # Step 4: Validate
        assert trends_response.status_code == 200
        trends = trends_response.json()
        
        trend = trends[0]
        assert trend["defects_created"] == 7  # 5 open + 2 resolved
        assert trend["avg_resolution_time_hours"] == 48.0  # (24 + 72) / 2
    
    def test_multi_project_defect_isolation(self, postgres_client: TestClient):
        """
        API Flow: POST defects for multiple projects → GET trends per project
        
        Validates:
        - Defect isolation between projects
        - Correct trend calculation per project
        """
        projects = {
            "API Gateway": 3,
            "User Service": 5,
            "Web Dashboard": 2
        }
        
        # Step 1: Create defects for each project
        for project, count in projects.items():
            for i in range(count):
                postgres_client.post("/api/v1/defects", json={
                    "project_name": project,
                    "defect_id": f"{project}-{i+1}",
                    "priority": "high",
                    "status": "open"
                })
        
        # Step 2: Verify trends for each project
        for project, expected_count in projects.items():
            trends_response = postgres_client.get(f"/api/v1/defect-trends?project_name={project}")
            
            assert trends_response.status_code == 200
            trends = trends_response.json()
            assert len(trends) > 0
            assert trends[0]["defects_created"] == expected_count


class TestDefectPriorityDistribution:
    """Test defect priority tracking across API flow."""
    
    def test_priority_distribution_in_trends(self, postgres_client: TestClient):
        """
        API Flow: POST defects with various priorities → GET trends → Validate distribution
        
        Validates:
        - High priority defect counting
        - Priority-based filtering
        """
        project = "Mobile App"
        
        # Create defects with different priorities
        priorities = {
            "high": 3,
            "medium": 5,
            "low": 2
        }
        
        for priority, count in priorities.items():
            for i in range(count):
                postgres_client.post("/api/v1/defects", json={
                    "project_name": project,
                    "defect_id": f"{priority.upper()}-{i+1}",
                    "priority": priority,
                    "status": "open"
                })
        
        # Get trends and validate
        trends_response = postgres_client.get(f"/api/v1/defect-trends?project_name={project}")
        
        assert trends_response.status_code == 200
        trends = trends_response.json()
        
        trend = trends[0]
        assert trend["defects_created"] == 10  # 3+5+2
        assert trend["high_priority_defects"] == 3