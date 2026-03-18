"""
CRUD operations for Quality Metrics Platform.

Provides database operations for teams, projects, and metrics.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.models.db_models import (
    Team, Project, DeploymentMetric, DefectMetric, CoverageMetric
)


# -------------------------
# Teams & Projects
# -------------------------

def get_or_create_team(db: Session, team_name: Optional[str]) -> Optional[Team]:
    """
    Get existing team by name or create if not exists.
    Returns None if team_name is None.
    """
    if not team_name:
        return None
    
    team = db.query(Team).filter(Team.team_name == team_name).first()
    if not team:
        team = Team(team_name=team_name)
        db.add(team)
        db.flush()  # Get team_id without committing
    
    return team


def get_or_create_project(
    db: Session, 
    project_name: str, 
    team: Optional[Team]
) -> Project:
    """
    Get existing project by name and team, or create if not exists.
    """
    query = db.query(Project).filter(Project.project_name == project_name)
    
    if team:
        query = query.filter(Project.team_id == team.team_id)
    else:
        query = query.filter(Project.team_id.is_(None))
    
    project = query.first()
    
    if not project:
        project = Project(
            project_name=project_name,
            team_id=team.team_id if team else None
        )
        db.add(project)
        db.flush()
    
    return project


# -------------------------
# Deployment Metrics
# -------------------------

def create_deployment_metric(
    db: Session,
    project_name: str,
    team_name: Optional[str],
    metric_date: Optional[date],
    successful: bool,
    lead_time_hours: Optional[float],
) -> DeploymentMetric:
    """
    Create a deployment metric record.
    Auto-creates team and project if they don't exist.
    """
    team = get_or_create_team(db, team_name)
    project = get_or_create_project(db, project_name, team)
    
    # Map Pydantic schema fields to DB schema
    deployment_timestamp = datetime.combine(
        metric_date or date.today(),
        datetime.min.time()
    )
    
    metric = DeploymentMetric(
        project_id=project.project_id,
        deployment_timestamp=deployment_timestamp,
        deployment_status="success" if successful else "failed",
        lead_time_hours=lead_time_hours,
        environment="production",  # Default for now
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    
    return metric


# -------------------------
# Defect Metrics
# -------------------------

def create_defect_metric(
    db: Session,
    project_name: str,
    team_name: Optional[str],
    created_date: Optional[date],
    resolved_date: Optional[date],
    severity: Optional[str],
    status: Optional[str],
) -> DefectMetric:
    """
    Create a defect metric record.
    Auto-creates team and project if they don't exist.
    """
    team = get_or_create_team(db, team_name)
    project = get_or_create_project(db, project_name, team)
    
    # Generate unique defect key
    defect_key = f"{project_name}-{datetime.utcnow().timestamp()}"
    
    # Calculate resolution time if both dates provided
    resolution_time_hours = None
    if created_date and resolved_date:
        delta = datetime.combine(resolved_date, datetime.min.time()) - \
                datetime.combine(created_date, datetime.min.time())
        resolution_time_hours = delta.total_seconds() / 3600
    
    metric = DefectMetric(
        project_id=project.project_id,
        defect_key=defect_key,
        title=f"Defect for {project_name}",  # Placeholder
        severity=severity,
        status=status or "open",
        created_date=datetime.combine(
            created_date or date.today(),
            datetime.min.time()
        ),
        resolved_date=datetime.combine(
            resolved_date, datetime.min.time()
        ) if resolved_date else None,
        resolution_time_hours=resolution_time_hours,
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    
    return metric


# -------------------------
# Coverage Metrics
# -------------------------

def create_coverage_metric(
    db: Session,
    project_name: str,
    team_name: Optional[str],
    week_start: Optional[date],
    line_coverage_percent: Optional[float],
    branch_coverage_percent: Optional[float],
) -> CoverageMetric:
    """
    Create a coverage metric record.
    Auto-creates team and project if they don't exist.
    """
    team = get_or_create_team(db, team_name)
    project = get_or_create_project(db, project_name, team)
    
    metric = CoverageMetric(
        project_id=project.project_id,
        coverage_timestamp=datetime.combine(
            week_start or date.today(),
            datetime.min.time()
        ),
        line_coverage_percent=line_coverage_percent,
        branch_coverage_percent=branch_coverage_percent,
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    
    return metric


# -------------------------
# Query Views
# -------------------------

def get_dora_metrics_summary(db: Session, limit: int = 100) -> List[dict]:
    """Query the dora_metrics_summary view."""
    query = text("""
        SELECT 
            project_id,
            project_name,
            team_name,
            metric_date,
            successful_deployments,
            failed_deployments,
            avg_lead_time_hours,
            change_failure_rate_percent
        FROM dora_metrics_summary
        ORDER BY metric_date DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    return [dict(row._mapping) for row in result]


def get_defect_trends_summary(db: Session, limit: int = 100) -> List[dict]:
    """Query the defect_trends_summary view."""
    query = text("""
        SELECT 
            project_id,
            project_name,
            week_start,
            defects_created,
            high_priority_defects,
            defects_resolved,
            avg_resolution_time_hours
        FROM defect_trends_summary
        ORDER BY week_start DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    return [dict(row._mapping) for row in result]


def get_coverage_trends_summary(db: Session, limit: int = 100) -> List[dict]:
    """Query the coverage_trends_summary view."""
    query = text("""
        SELECT 
            project_id,
            project_name,
            week_start,
            avg_line_coverage,
            avg_branch_coverage,
            max_line_coverage,
            min_line_coverage
        FROM coverage_trends_summary
        ORDER BY week_start DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    return [dict(row._mapping) for row in result]
