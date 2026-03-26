"""
Coverage repository for data access operations.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from src.models.db_models import CoverageMetric, Project


class CoverageRepository:
    """Repository for CoverageMetric entity data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        project_id: int,
        coverage_timestamp: datetime,
        line_coverage_percent: Optional[float],
        branch_coverage_percent: Optional[float]
    ) -> CoverageMetric:
        """Create a new coverage metric."""
        metric = CoverageMetric(
            project_id=project_id,
            coverage_timestamp=coverage_timestamp,
            line_coverage_percent=line_coverage_percent,
            branch_coverage_percent=branch_coverage_percent,
        )
        
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        
        return metric
    
    def get_all_with_project(self) -> List[tuple]:
        """
        Get all coverage metrics with project information.
        Returns tuples of (project_id, project_name, coverage_timestamp, line_cov, branch_cov).
        """
        return (
            self.db.query(
                Project.project_id,
                Project.project_name,
                CoverageMetric.coverage_timestamp,
                CoverageMetric.line_coverage_percent,
                CoverageMetric.branch_coverage_percent,
            )
            .join(Project, CoverageMetric.project_id == Project.project_id)
            .all()
        )