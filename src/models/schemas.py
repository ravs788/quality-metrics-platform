"""
Pydantic schemas for request/response payloads.

These models form the API contract for metric ingestion and retrieval endpoints.
They are intentionally minimal for Phase 1 (Foundation) and can be expanded
later as persistence and analytics queries are implemented.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# -------------------------
# Deployments
# -------------------------


class DeploymentMetricBase(BaseModel):
    """Common fields for deployment metrics."""

    project_name: str = Field(..., examples=["api-gateway"])
    team_name: Optional[str] = Field(None, examples=["platform-engineering"])
    metric_date: Optional[date] = Field(
        None, description="Date the deployment happened (UTC)."
    )
    successful: bool = Field(..., description="Whether the deployment succeeded.")
    lead_time_hours: Optional[float] = Field(
        None, ge=0, description="Lead time from commit to deploy in hours."
    )


class DeploymentMetricCreate(DeploymentMetricBase):
    """Payload for creating a deployment metric."""


class DeploymentMetricRead(DeploymentMetricBase):
    """Response model for a deployment metric."""

    id: Optional[int] = Field(None, description="Database ID (when persistence exists).")
    created_at: Optional[datetime] = Field(
        None, description="Server-side creation timestamp (when persistence exists)."
    )


# -------------------------
# Defects
# -------------------------


class DefectMetricBase(BaseModel):
    """Common fields for defect metrics."""

    project_name: str = Field(..., examples=["user-service"])
    team_name: Optional[str] = Field(None, examples=["backend-services"])
    created_date: Optional[date] = Field(None, description="Defect created date (UTC).")
    resolved_date: Optional[date] = Field(None, description="Defect resolved date (UTC).")
    severity: Optional[str] = Field(
        None, description="Defect severity (e.g., low/medium/high/critical)."
    )
    status: Optional[str] = Field(None, description="Defect status (e.g., open/resolved).")


class DefectMetricCreate(DefectMetricBase):
    """Payload for creating a defect metric."""


class DefectMetricRead(DefectMetricBase):
    """Response model for a defect metric."""

    id: Optional[int] = Field(None, description="Database ID (when persistence exists).")
    created_at: Optional[datetime] = Field(
        None, description="Server-side creation timestamp (when persistence exists)."
    )


# -------------------------
# Coverage
# -------------------------


class CoverageMetricBase(BaseModel):
    """Common fields for coverage metrics."""

    project_name: str = Field(..., examples=["web-dashboard"])
    team_name: Optional[str] = Field(None, examples=["frontend-experience"])
    week_start: Optional[date] = Field(None, description="Week start date for this snapshot.")
    line_coverage_percent: Optional[float] = Field(
        None, ge=0, le=100, description="Line coverage percentage."
    )
    branch_coverage_percent: Optional[float] = Field(
        None, ge=0, le=100, description="Branch coverage percentage."
    )


class CoverageMetricCreate(CoverageMetricBase):
    """Payload for creating a coverage metric."""


class CoverageMetricRead(CoverageMetricBase):
    """Response model for a coverage metric."""

    id: Optional[int] = Field(None, description="Database ID (when persistence exists).")
    created_at: Optional[datetime] = Field(
        None, description="Server-side creation timestamp (when persistence exists)."
    )
