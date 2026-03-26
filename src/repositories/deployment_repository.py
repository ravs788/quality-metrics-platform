"""
Deployment repository for data access operations.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from src.models.db_models import DeploymentMetric, Project, Team


class DeploymentRepository:
    """Repository for DeploymentMetric entity data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        project_id: int,
        deployment_timestamp: datetime,
        deployment_status: str,
        lead_time_hours: Optional[float],
        environment: str = "production"
    ) -> DeploymentMetric:
        """Create a new deployment metric."""
        metric = DeploymentMetric(
            project_id=project_id,
            deployment_timestamp=deployment_timestamp,
            deployment_status=deployment_status,
            lead_time_hours=lead_time_hours,
            environment=environment,
        )
        
        self.db.add(metric)
        self.db.flush()
        self.db.refresh(metric)
        
        return metric
    
    def get_aggregated_metrics(self, limit: int = 100) -> List[dict]:
        """
        Get aggregated deployment metrics grouped by project, team, and date.
        Returns DORA metrics data.
        """
        query = (
            self.db.query(
                Project.project_id,
                Project.project_name,
                Team.team_name,
                func.date(DeploymentMetric.deployment_timestamp).label('metric_date'),
                func.sum(
                    case((DeploymentMetric.deployment_status == 'success', 1), else_=0)
                ).label('successful_deployments'),
                func.sum(
                    case((DeploymentMetric.deployment_status == 'failed', 1), else_=0)
                ).label('failed_deployments'),
                func.avg(DeploymentMetric.lead_time_hours).label('avg_lead_time_hours'),
            )
            .join(Project, DeploymentMetric.project_id == Project.project_id)
            .outerjoin(Team, Project.team_id == Team.team_id)
            .filter(DeploymentMetric.environment == 'production')
            .group_by(
                Project.project_id,
                Project.project_name,
                Team.team_name,
                func.date(DeploymentMetric.deployment_timestamp)
            )
            .order_by(func.date(DeploymentMetric.deployment_timestamp).desc())
            .limit(limit)
        )
        
        return query.all()