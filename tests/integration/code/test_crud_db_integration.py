"""Code-level integration tests for repositories/services with the database."""

from sqlalchemy.orm import Session
from datetime import date

from src.repositories import TeamRepository, ProjectRepository
from src.services import DoraService
from src.models.db_models import Team, DeploymentMetric


class TestTeamProjectWorkflow:
    """Test team and project creation with database integration."""
    
    def test_team_creation_and_retrieval(self, postgres_db: Session):
        """
        Integration: Create team → Verify in database
        
        Validates:
        - Team is persisted to database
        - Team can be retrieved
        - Same team is not duplicated
        """
        team_name = "Integration Test Team"
        
        # Create team
        team_repo = TeamRepository(postgres_db)
        team1 = team_repo.get_or_create(team_name)
        assert team1.team_id is not None
        assert team1.team_name == team_name
        
        # Retrieve same team (should not create duplicate)
        team2 = team_repo.get_or_create(team_name)
        assert team2.team_id == team1.team_id
        
        # Verify only one team exists
        all_teams = postgres_db.query(Team).filter_by(team_name=team_name).all()
        assert len(all_teams) == 1
    
    def test_project_creation_with_team(self, postgres_db: Session):
        """
        Integration: Create team → Create project → Verify relationship
        
        Validates:
        - Project is linked to correct team
        - Foreign key relationship works
        - Project can access team data
        """
        # Create team first
        team_repo = TeamRepository(postgres_db)
        team = team_repo.get_or_create("Backend Team")
        
        # Create project under team
        project_repo = ProjectRepository(postgres_db)
        project = project_repo.get_or_create(
            "User Service",
            team
        )
        
        assert project.project_id is not None
        assert project.team_id == team.team_id
        
        # Test relationship access
        postgres_db.refresh(project)
        assert project.team.team_name == "Backend Team"
    
    def test_project_auto_creates_team(self, postgres_db: Session):
        """
        Integration: Create project with team name → Team auto-created
        
        Validates:
        - get_or_create pattern works across functions
        - Team is created if doesn't exist
        """
        team_name = "Auto Created Team"
        project_name = "Auto Test Project"
        
        # Verify team doesn't exist yet
        team_check = postgres_db.query(Team).filter_by(team_name=team_name).first()
        assert team_check is None
        
        # Create team and project
        team_repo = TeamRepository(postgres_db)
        team = team_repo.get_or_create(team_name)
        project_repo = ProjectRepository(postgres_db)
        project = project_repo.get_or_create(project_name, team)
        
        # Verify both exist in database
        assert team.team_id is not None
        assert project.project_id is not None
        assert project.team_id == team.team_id


class TestMetricPersistence:
    """Test metric creation with database persistence."""
    
    def test_deployment_metric_persistence(self, postgres_db: Session, integration_project):
        """
        Integration: Create deployment → Verify in database → Query back
        
        Validates:
        - Deployment is persisted correctly
        - All fields are saved
        - Can be queried back
        """
        # Create deployment metric
        dora_service = DoraService(postgres_db)
        metric = dora_service.create_deployment_metric(
            project_name=integration_project.project_name,
            team_name=integration_project.team.team_name,
            successful=True,
            lead_time_hours=2.5,
            metric_date=date.today()
        )
        
        postgres_db.commit()
        
        # Query back from database
        saved_metric = postgres_db.query(DeploymentMetric).filter_by(
            metric_id=metric.metric_id
        ).first()
        
        assert saved_metric is not None
        assert saved_metric.project_id == integration_project.project_id
        assert saved_metric.deployment_status == "success"
        assert saved_metric.lead_time_hours == 2.5
    
    def test_multiple_metrics_same_project(self, postgres_db: Session, integration_project):
        """
        Integration: Create multiple metrics → Verify all persisted → Count correct
        
        Validates:
        - Multiple metrics can be created for same project
        - All are stored correctly
        - Database constraints work
        """
        # Create multiple deployment metrics
        dora_service = DoraService(postgres_db)
        for i in range(5):
            dora_service.create_deployment_metric(
                project_name=integration_project.project_name,
                team_name=integration_project.team.team_name,
                successful=(i % 2 == 0),
                lead_time_hours=2.0 + i * 0.5,
                metric_date=date.today()
            )
        
        postgres_db.commit()
        
        # Verify all saved
        metrics = postgres_db.query(DeploymentMetric).filter_by(
            project_id=integration_project.project_id
        ).all()
        
        assert len(metrics) == 5
        
        # Verify mix of success/failure
        successful_count = sum(1 for m in metrics if m.deployment_status == "success")
        assert successful_count == 3  # 0, 2, 4 indices


class TestDatabaseConstraints:
    """Test database constraints and relationships."""
    
    def test_cascade_delete_project_deletes_metrics(self, postgres_db: Session):
        """
        Integration: Create project with metrics → Delete project → Verify metrics deleted
        
        Validates:
        - Cascade delete works correctly
        - Foreign key constraints are enforced
        """
        # Create team and project
        team_repo = TeamRepository(postgres_db)
        team = team_repo.get_or_create("Cascade Test Team")
        project_repo = ProjectRepository(postgres_db)
        project = project_repo.get_or_create("Cascade Test Project", team)
        
        # Create metrics
        dora_service = DoraService(postgres_db)
        for i in range(3):
            dora_service.create_deployment_metric(
                project_name=project.project_name,
                team_name=team.team_name,
                successful=True,
                lead_time_hours=2.0,
                metric_date=date.today()
            )
        
        postgres_db.commit()
        
        project_id = project.project_id
        
        # Verify metrics exist
        metrics_before = postgres_db.query(DeploymentMetric).filter_by(
            project_id=project_id
        ).count()
        assert metrics_before == 3
        
        # Delete project
        postgres_db.delete(project)
        postgres_db.commit()
        
        # Verify metrics are also deleted (cascade)
        metrics_after = postgres_db.query(DeploymentMetric).filter_by(
            project_id=project_id
        ).count()
        assert metrics_after == 0