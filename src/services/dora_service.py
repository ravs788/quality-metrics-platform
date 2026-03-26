"""
DORA metrics service for business logic operations.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session

from src.repositories.team_repository import TeamRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.deployment_repository import DeploymentRepository
from src.models.db_models import DeploymentMetric


class DoraService:
    """Service for DORA metrics business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.team_repo = TeamRepository(db)
        self.project_repo = ProjectRepository(db)
        self.deployment_repo = DeploymentRepository(db)
    
    def create_deployment_metric(
        self,
        project_name: str,
        team_name: Optional[str],
        metric_date: Optional[date],
        successful: bool,
        lead_time_hours: Optional[float],
    ) -> DeploymentMetric:
        """
        Create a deployment metric.
        Auto-creates team and project if they don't exist.
        """
        # Get or create team and project
        team = self.team_repo.get_or_create(team_name)
        project = self.project_repo.get_or_create(project_name, team)
        
        # Convert date to datetime
        deployment_timestamp = datetime.combine(
            metric_date or date.today(),
            datetime.min.time()
        )
        
        # Map successful flag to status
        deployment_status = "success" if successful else "failed"
        
        # Create deployment metric
        return self.deployment_repo.create(
            project_id=project.project_id,
            deployment_timestamp=deployment_timestamp,
            deployment_status=deployment_status,
            lead_time_hours=lead_time_hours,
            environment="production"
        )
    
    def get_dora_metrics_summary(self, limit: int = 100) -> List[dict]:
        """
        Get DORA metrics summary with change failure rate calculated.
        """
        rows = self.deployment_repo.get_aggregated_metrics(limit)
        
        results = []
        for row in rows:
            total = row.successful_deployments + row.failed_deployments
            change_failure_rate = (row.failed_deployments / total * 100) if total > 0 else 0.0
            
            results.append({
                'project_id': row.project_id,
                'project_name': row.project_name,
                'team_name': row.team_name,
                'metric_date': row.metric_date,
                'successful_deployments': row.successful_deployments,
                'failed_deployments': row.failed_deployments,
                'total_deployments': total,
                'avg_lead_time_hours': round(row.avg_lead_time_hours, 3) if row.avg_lead_time_hours else None,
                'change_failure_rate_percent': round(change_failure_rate, 2),
            })
        
        return results