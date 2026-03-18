"""
Metrics router for the Quality Metrics Platform.

Provides endpoints for:
- Ingesting deployment, defect, and coverage metrics (POST)
- Retrieving aggregated views (GET)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from sqlalchemy.orm import Session

# Import Pydantic schemas
from src.models.schemas import (
    DeploymentMetricCreate,
    DefectMetricCreate,
    CoverageMetricCreate,
    DeploymentMetricRead,
    DefectMetricRead,
    CoverageMetricRead,
)

# Import database dependencies and CRUD operations
from src.database import get_db
from src import crud

router = APIRouter()


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
    db: Session = Depends(get_db)
):
    """
    Insert deployment metric into the database.
    Auto-creates team and project if they don't exist.
    """
    db_metric = crud.create_deployment_metric(
        db=db,
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
    "/defects",
    response_model=DefectMetricRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a defect metric",
)
async def create_defect(
    metric: DefectMetricCreate,
    db: Session = Depends(get_db)
):
    """
    Insert defect metric into the database.
    Auto-creates team and project if they don't exist.
    """
    db_metric = crud.create_defect_metric(
        db=db,
        project_name=metric.project_name,
        team_name=metric.team_name,
        created_date=metric.created_date,
        resolved_date=metric.resolved_date,
        severity=metric.severity,
        status=metric.status,
    )
    
    return DefectMetricRead(
        id=db_metric.defect_id,
        project_name=metric.project_name,
        team_name=metric.team_name,
        created_date=metric.created_date,
        resolved_date=metric.resolved_date,
        severity=metric.severity,
        status=metric.status,
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
    db: Session = Depends(get_db)
):
    """
    Insert coverage metric into the database.
    Auto-creates team and project if they don't exist.
    """
    db_metric = crud.create_coverage_metric(
        db=db,
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
async def get_dora_metrics(db: Session = Depends(get_db)):
    """
    Query the dora_metrics_summary view for aggregated DORA metrics.
    """
    return crud.get_dora_metrics_summary(db)


@router.get(
    "/defect-trends",
    summary="Get defect trends summary",
)
async def get_defect_trends(db: Session = Depends(get_db)):
    """
    Query the defect_trends_summary view for weekly defect trends.
    """
    return crud.get_defect_trends_summary(db)


@router.get(
    "/coverage-trends",
    summary="Get coverage trends summary",
)
async def get_coverage_trends(db: Session = Depends(get_db)):
    """
    Query the coverage_trends_summary view for weekly coverage trends.
    """
    return crud.get_coverage_trends_summary(db)
