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
    """
    Query DORA metrics summary using ORM.
    Aggregates deployment metrics by project, team, and date.
    """
    from sqlalchemy import func, case
    from datetime import datetime
    
    # Aggregate deployment metrics
    query = (
        db.query(
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
    
    results = []
    for row in query.all():
        total = row.successful_deployments + row.failed_deployments
        change_failure_rate = (row.failed_deployments / total * 100) if total > 0 else 0.0
        
        results.append({
            'project_id': row.project_id,
            'project_name': row.project_name,
            'team_name': row.team_name,
            'metric_date': row.metric_date,
            'successful_deployments': row.successful_deployments,
            'failed_deployments': row.failed_deployments,
            'avg_lead_time_hours': round(row.avg_lead_time_hours, 3) if row.avg_lead_time_hours else None,
            'change_failure_rate_percent': round(change_failure_rate, 2),
        })
    
    return results


def get_defect_trends_summary(db: Session, limit: int = 100) -> List[dict]:
    """
    Defect trends summary aggregated by project and week.

    Note: implemented in Python (not SQL views) to stay cross-database
    compatible for unit tests (SQLite) and runtime (PostgreSQL).
    """
    from collections import defaultdict
    from datetime import timedelta
    from sqlalchemy import select

    # Load the minimal columns needed for aggregation
    rows = (
        db.query(
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

    buckets: dict[tuple[int, str, date], dict] = {}

    for project_id, project_name, created_dt, priority, status, resolution_time_hours in rows:
        created_date_only = created_dt.date() if created_dt else date.today()
        week_start = created_date_only - timedelta(days=created_date_only.weekday())  # Monday

        key = (project_id, project_name, week_start)
        if key not in buckets:
            buckets[key] = {
                "project_id": project_id,
                "project_name": project_name,
                "week_start": week_start.isoformat(),
                "defects_created": 0,
                "high_priority_defects": 0,
                "defects_resolved": 0,
                "_resolution_times": [],
            }

        bucket = buckets[key]
        bucket["defects_created"] += 1

        if priority in ("critical", "high"):
            bucket["high_priority_defects"] += 1

        if status in ("resolved", "closed"):
            bucket["defects_resolved"] += 1

        if resolution_time_hours is not None:
            bucket["_resolution_times"].append(float(resolution_time_hours))

    # Finalize avg
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


def get_coverage_trends_summary(db: Session, limit: int = 100) -> List[dict]:
    """
    Coverage trends summary aggregated by project and week.

    Note: implemented in Python (not SQL views) to stay cross-database
    compatible for unit tests (SQLite) and runtime (PostgreSQL).
    """
    from collections import defaultdict
    from datetime import timedelta

    rows = (
        db.query(
            Project.project_id,
            Project.project_name,
            CoverageMetric.coverage_timestamp,
            CoverageMetric.line_coverage_percent,
            CoverageMetric.branch_coverage_percent,
        )
        .join(Project, CoverageMetric.project_id == Project.project_id)
        .all()
    )

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
