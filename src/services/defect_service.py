"""
Defect metrics service for business logic operations.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from src.repositories.team_repository import TeamRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.defect_repository import DefectRepository
from src.models.db_models import DefectMetric


class DefectService:
    """Service for defect metrics business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.team_repo = TeamRepository(db)
        self.project_repo = ProjectRepository(db)
        self.defect_repo = DefectRepository(db)
    
    def create_defect_metric(
        self,
        project_name: str,
        team_name: Optional[str],
        created_date: Optional[date],
        resolved_date: Optional[date],
        priority: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        resolution_time_hours: Optional[float] = None,
    ) -> DefectMetric:
        """
        Create a defect metric.
        Auto-creates team and project if they don't exist.
        """
        # Get or create team and project
        team = self.team_repo.get_or_create(team_name)
        project = self.project_repo.get_or_create(project_name, team)
        
        # Generate unique defect key
        defect_key = f"{project_name}-{datetime.utcnow().timestamp()}"
        
        # Calculate resolution time if not explicitly provided and both dates exist
        computed_resolution_time = resolution_time_hours
        if computed_resolution_time is None and created_date and resolved_date:
            delta = datetime.combine(resolved_date, datetime.min.time()) - \
                    datetime.combine(created_date, datetime.min.time())
            computed_resolution_time = delta.total_seconds() / 3600
        
        # Convert dates to datetimes
        created_datetime = datetime.combine(
            created_date or date.today(),
            datetime.min.time()
        )
        resolved_datetime = datetime.combine(
            resolved_date, datetime.min.time()
        ) if resolved_date else None
        
        # Create defect metric
        return self.defect_repo.create(
            project_id=project.project_id,
            defect_key=defect_key,
            title=f"Defect for {project_name}",
            priority=priority,
            severity=severity,
            status=status or "open",
            created_date=created_datetime,
            resolved_date=resolved_datetime,
            resolution_time_hours=computed_resolution_time
        )
    
    def get_defect_trends_summary(self, limit: int = 100, project_name: Optional[str] = None) -> List[dict]:
        """
        Get defect trends summary aggregated by project and week.
        Implemented in Python for cross-database compatibility.
        """
        rows = self.defect_repo.get_all_with_project()
        
        buckets: dict[tuple, dict] = {}
        
        for project_id, current_project_name, created_dt, priority, status, resolution_time_hours in rows:
            if project_name and current_project_name != project_name:
                continue

            created_date_only = created_dt.date() if created_dt else date.today()
            week_start = created_date_only - timedelta(days=created_date_only.weekday())  # Monday
            
            key = (project_id, current_project_name) if project_name else (project_id, current_project_name, week_start)
            if key not in buckets:
                buckets[key] = {
                    "project_id": project_id,
                    "project_name": current_project_name,
                    "week_start": week_start.isoformat(),
                    "defects_created": 0,
                    "high_priority_defects": 0,
                    "defects_resolved": 0,
                    "_resolution_times": [],
                }
            
            bucket = buckets[key]
            if project_name:
                existing_week = date.fromisoformat(bucket["week_start"])
                if week_start < existing_week:
                    bucket["week_start"] = week_start.isoformat()
            bucket["defects_created"] += 1
            
            if priority in ("critical", "high"):
                bucket["high_priority_defects"] += 1
            
            if status in ("resolved", "closed"):
                bucket["defects_resolved"] += 1
            
            if resolution_time_hours is not None:
                bucket["_resolution_times"].append(float(resolution_time_hours))
        
        # Finalize average resolution time
        results = []
        for bucket in buckets.values():
            times = bucket.pop("_resolution_times")
            bucket["avg_resolution_time_hours"] = (
                round(sum(times) / len(times), 2) if times else None
            )
            results.append(bucket)
        
        # Sort newest week first and apply limit
        results.sort(key=lambda x: x["week_start"], reverse=True)
        return results[:limit]