"""
Metrics router for the Quality Metrics Platform.

Provides endpoints for:
- Ingesting deployment, defect, and coverage metrics (POST)
- Retrieving aggregated views (GET)
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

# Import Pydantic schemas
from src.models.schemas import (
    DeploymentMetricCreate,
    GitHubActionsDeploymentIngest,
    DefectMetricCreate,
    CoverageMetricCreate,
    DeploymentMetricRead,
    DefectMetricRead,
    CoverageMetricRead,
)

# Import database dependencies and services
from src.database import get_db
from src.dependencies import get_current_api_key
from src.models.db_models import ApiKey
from src.services import DoraService, DefectService, CoverageService

router = APIRouter()


def get_dora_service(db: Session = Depends(get_db)) -> DoraService:
    """Return a DORA service bound to the current database session."""
    return DoraService(db)


def get_defect_service(db: Session = Depends(get_db)) -> DefectService:
    """Return a defect service bound to the current database session."""
    return DefectService(db)


def get_coverage_service(db: Session = Depends(get_db)) -> CoverageService:
    """Return a coverage service bound to the current database session."""
    return CoverageService(db)


# -------------------------
# Ingestion Endpoints
# -------------------------

@router.post(
    "/deployments",
    response_model=DeploymentMetricRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a deployment metric",
)
async def create_deployment(
    metric: DeploymentMetricCreate,
    dora_service: DoraService = Depends(get_dora_service),
):
    """
    Insert deployment metric into the database.
    Auto-creates team and project if they don't exist.
    """
    db_metric = dora_service.create_deployment_metric(
        project_name=metric.project_name,
        team_name=metric.team_name,
        metric_date=metric.metric_date,
        successful=metric.successful,
        lead_time_hours=metric.lead_time_hours,
    )
    
    return DeploymentMetricRead(
        id=db_metric.metric_id,
        project_name=metric.project_name,
        team_name=metric.team_name,
        metric_date=metric.metric_date,
        successful=metric.successful,
        lead_time_hours=metric.lead_time_hours,
        created_at=db_metric.created_at,
    )


@router.post(
    "/deployments/github-actions",
    response_model=DeploymentMetricRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest GitHub Actions deployment event",
)
async def create_github_actions_deployment(
    event: GitHubActionsDeploymentIngest,
    dora_service: DoraService = Depends(get_dora_service),
    api_key: ApiKey = Depends(get_current_api_key),
):
    """
    Insert deployment metric from a GitHub Actions workflow run event.

    Requires API key authentication and maps workflow run fields into
    the deployment metric domain.
    """
    db_metric = dora_service.ingest_github_actions_deployment(
        repository=event.repository,
        status=event.status,
        conclusion=event.conclusion,
        run_started_at=event.run_started_at,
        project_name=event.project_name,
        team_name=event.team_name,
        lead_time_hours=event.lead_time_hours,
        environment=event.environment,
    )

    resolved_project_name = event.project_name or event.repository.split("/")[-1]

    return DeploymentMetricRead(
        id=db_metric.metric_id,
        project_name=resolved_project_name,
        team_name=event.team_name,
        metric_date=event.run_started_at.date(),
        successful=db_metric.deployment_status == "success",
        lead_time_hours=event.lead_time_hours,
        created_at=db_metric.created_at,
    )


@router.post(
    "/defects",
    response_model=DefectMetricRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a defect metric",
)
async def create_defect(
    metric: DefectMetricCreate,
    defect_service: DefectService = Depends(get_defect_service),
):
    """
    Insert defect metric into the database.
    Auto-creates team and project if they don't exist.
    """
    db_metric = defect_service.create_defect_metric(
        project_name=metric.project_name,
        team_name=metric.team_name,
        created_date=metric.created_date,
        resolved_date=metric.resolved_date,
        priority=metric.priority,
        severity=metric.severity,
        status=metric.status,
        resolution_time_hours=metric.resolution_time_hours,
    )
    
    return DefectMetricRead(
        id=db_metric.defect_id,
        defect_id=metric.defect_id,
        project_name=metric.project_name,
        team_name=metric.team_name,
        created_date=metric.created_date,
        resolved_date=metric.resolved_date,
        priority=metric.priority,
        severity=metric.severity,
        status=metric.status,
        resolution_time_hours=metric.resolution_time_hours,
        created_at=db_metric.created_at,
    )


@router.post(
    "/coverage",
    response_model=CoverageMetricRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a coverage metric",
)
async def create_coverage(
    metric: CoverageMetricCreate,
    coverage_service: CoverageService = Depends(get_coverage_service),
):
    """
    Insert coverage metric into the database.
    Auto-creates team and project if they don't exist.
    """
    db_metric = coverage_service.create_coverage_metric(
        project_name=metric.project_name,
        team_name=metric.team_name,
        week_start=metric.week_start,
        line_coverage_percent=metric.line_coverage_percent,
        branch_coverage_percent=metric.branch_coverage_percent,
    )
    
    return CoverageMetricRead(
        id=db_metric.coverage_id,
        project_name=metric.project_name,
        team_name=metric.team_name,
        week_start=metric.week_start,
        line_coverage_percent=metric.line_coverage_percent,
        branch_coverage_percent=metric.branch_coverage_percent,
        created_at=db_metric.created_at,
    )


# -------------------------
# Retrieval Endpoints
# -------------------------

@router.get(
    "/dora-metrics",
    summary="Get DORA metrics summary",
)
async def get_dora_metrics(
    project_name: Optional[str] = Query(default=None),
    dora_service: DoraService = Depends(get_dora_service),
):
    """
    Query the dora_metrics_summary view for aggregated DORA metrics.
    """
    return dora_service.get_dora_metrics_summary(project_name=project_name)


@router.get(
    "/defect-trends",
    summary="Get defect trends summary",
)
async def get_defect_trends(
    project_name: Optional[str] = Query(default=None),
    defect_service: DefectService = Depends(get_defect_service),
):
    """
    Query the defect_trends_summary view for weekly defect trends.
    """
    return defect_service.get_defect_trends_summary(project_name=project_name)


@router.get(
    "/coverage-trends",
    summary="Get coverage trends summary",
)
async def get_coverage_trends(
    project_name: Optional[str] = Query(default=None),
    coverage_service: CoverageService = Depends(get_coverage_service),
):
    """
    Query the coverage_trends_summary view for weekly coverage trends.
    """
    return coverage_service.get_coverage_trends_summary(project_name=project_name)
