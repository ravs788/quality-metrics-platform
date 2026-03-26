"""
Defect repository for data access operations.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session

from src.models.db_models import DefectMetric, Project


class DefectRepository:
    """Repository for DefectMetric entity data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        project_id: int,
        defect_key: str,
        title: str,
        severity: Optional[str],
        status: str,
        created_date: datetime,
        resolved_date: Optional[datetime],
        resolution_time_hours: Optional[float]
    ) -> DefectMetric:
        """Create a new defect metric."""
        metric = DefectMetric(
            project_id=project_id,
            defect_key=defect_key,
            title=title,
            severity=severity,
            status=status,
            created_date=created_date,
            resolved_date=resolved_date,
            resolution_time_hours=resolution_time_hours,
        )
        
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        
        return metric
    
    def get_all_with_project(self) -> List[tuple]:
        """
        Get all defects with project information.
        Returns tuples of (project_id, project_name, created_date, priority, status, resolution_time_hours).
        """
        return (
            self.db.query(
                Project.project_id,
                Project.project_name,
                DefectMetric.created_date,
                DefectMetric.priority,
                DefectMetric.status,
                DefectMetric.resolution_time_hours,
            )
            .join(Project, DefectMetric.project_id == Project.project_id)
            .all()
        )