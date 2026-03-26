"""
Coverage metrics service for business logic operations.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from src.repositories.team_repository import TeamRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.coverage_repository import CoverageRepository
from src.models.db_models import CoverageMetric


class CoverageService:
    """Service for coverage metrics business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.team_repo = TeamRepository(db)
        self.project_repo = ProjectRepository(db)
        self.coverage_repo = CoverageRepository(db)
    
    def create_coverage_metric(
        self,
        project_name: str,
        team_name: Optional[str],
        week_start: Optional[date],
        line_coverage_percent: Optional[float],
        branch_coverage_percent: Optional[float],
    ) -> CoverageMetric:
        """
        Create a coverage metric.
        Auto-creates team and project if they don't exist.
        """
        # Get or create team and project
        team = self.team_repo.get_or_create(team_name)
        project = self.project_repo.get_or_create(project_name, team)
        
        # Convert date to datetime
        coverage_timestamp = datetime.combine(
            week_start or date.today(),
            datetime.min.time()
        )
        
        # Create coverage metric
        return self.coverage_repo.create(
            project_id=project.project_id,
            coverage_timestamp=coverage_timestamp,
            line_coverage_percent=line_coverage_percent,
            branch_coverage_percent=branch_coverage_percent
        )
    
    def get_coverage_trends_summary(self, limit: int = 100) -> List[dict]:
        """
        Get coverage trends summary aggregated by project and week.
        Implemented in Python for cross-database compatibility.
        """
        rows = self.coverage_repo.get_all_with_project()
        
        buckets: dict[tuple[int, str, date], dict] = {}
        
        for project_id, project_name, ts, line_cov, branch_cov in rows:
            ts_date = (ts.date() if ts else date.today())
            week_start = ts_date - timedelta(days=ts_date.weekday())  # Monday
            
            key = (project_id, project_name, week_start)
            if key not in buckets:
                buckets[key] = {
                    "project_id": project_id,
                    "project_name": project_name,
                    "week_start": week_start.isoformat(),
                    "_line": [],
                    "_branch": [],
                }
            
            b = buckets[key]
            if line_cov is not None:
                b["_line"].append(float(line_cov))
            if branch_cov is not None:
                b["_branch"].append(float(branch_cov))
        
        results = []
        for b in buckets.values():
            lines = b.pop("_line")
            branches = b.pop("_branch")
            
            b["avg_line_coverage"] = round(sum(lines) / len(lines), 2) if lines else None
            b["avg_branch_coverage"] = (
                round(sum(branches) / len(branches), 2) if branches else None
            )
            b["max_line_coverage"] = round(max(lines), 2) if lines else None
            b["min_line_coverage"] = round(min(lines), 2) if lines else None
            
            results.append(b)
        
        results.sort(key=lambda x: x["week_start"], reverse=True)
        return results[:limit]