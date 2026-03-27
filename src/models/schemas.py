"""
Pydantic schemas for request/response payloads.

These models form the API contract for metric ingestion and retrieval endpoints.
They are intentionally minimal for Phase 1 (Foundation) and can be expanded
later as persistence and analytics queries are implemented.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, AliasChoices, model_validator


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


class GitHubActionsDeploymentIngest(BaseModel):
    """Payload for ingesting GitHub Actions workflow run deployment outcomes."""

    repository: str = Field(
        ...,
        description="Repository in owner/repo format.",
        examples=["acme/api-gateway"],
    )
    run_id: int = Field(..., description="GitHub Actions workflow run ID.")
    status: str = Field(..., description="Workflow run status.")
    conclusion: Optional[str] = Field(
        None,
        description="Workflow run conclusion for completed runs.",
    )
    run_started_at: datetime = Field(
        ...,
        description="UTC timestamp when the run started.",
    )
    project_name: Optional[str] = Field(
        None,
        description="Optional explicit project name override.",
    )
    team_name: Optional[str] = Field(
        None,
        description="Optional team name for project association.",
    )
    lead_time_hours: Optional[float] = Field(
        None,
        ge=0,
        description="Optional commit-to-deploy lead time in hours.",
    )
    environment: str = Field(
        "production",
        description="Deployment environment label.",
    )

    @model_validator(mode="after")
    def validate_conclusion_for_completed_status(self):
        """Ensure completed runs include a conclusion signal."""
        if self.status.lower() == "completed" and not self.conclusion:
            raise ValueError("conclusion is required when status is completed")
        return self


# -------------------------
# Defects
# -------------------------


class DefectMetricBase(BaseModel):
    """Common fields for defect metrics."""

    defect_id: Optional[str] = Field(None, description="External defect identifier.")
    project_name: str = Field(..., examples=["user-service"])
    team_name: Optional[str] = Field(None, examples=["backend-services"])
    created_date: Optional[date] = Field(None, description="Defect created date (UTC).")
    resolved_date: Optional[date] = Field(None, description="Defect resolved date (UTC).")
    priority: Optional[str] = Field(
        None, description="Defect priority (e.g., low/medium/high/critical)."
    )
    severity: Optional[str] = Field(
        None, description="Defect severity (e.g., low/medium/high/critical)."
    )
    status: Optional[str] = Field(None, description="Defect status (e.g., open/resolved).")
    resolution_time_hours: Optional[float] = Field(
        None, ge=0, description="Resolution time in hours when provided by caller."
    )


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
    week_start: Optional[date] = Field(
        None,
        description="Week start date for this snapshot.",
        validation_alias=AliasChoices("week_start", "metric_date"),
    )
    line_coverage_percent: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Line coverage percentage.",
        validation_alias=AliasChoices("line_coverage_percent", "line_coverage"),
    )
    branch_coverage_percent: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Branch coverage percentage.",
        validation_alias=AliasChoices("branch_coverage_percent", "branch_coverage"),
    )


class CoverageMetricCreate(CoverageMetricBase):
    """Payload for creating a coverage metric."""


class CoverageMetricRead(CoverageMetricBase):
    """Response model for a coverage metric."""

    id: Optional[int] = Field(None, description="Database ID (when persistence exists).")
    created_at: Optional[datetime] = Field(
        None, description="Server-side creation timestamp (when persistence exists)."
    )


# -------------------------
# API Keys
# -------------------------


class ApiKeyCreate(BaseModel):
    """Payload for creating an API key."""

    team_id: int = Field(..., description="ID of the team this key belongs to")
    key_name: str = Field(..., min_length=1, max_length=100, examples=["CI/CD Integration"])
    is_admin: bool = Field(False, description="Whether this is an admin key")
    created_by: Optional[str] = Field(None, max_length=100, examples=["admin@example.com"])


class ApiKeyResponse(BaseModel):
    """Response model for an API key (without sensitive data)."""

    key_id: int = Field(..., description="Unique key identifier")
    team_id: int = Field(..., description="Team this key belongs to")
    key_name: str = Field(..., description="Human-readable key name")
    is_admin: bool = Field(..., description="Whether this is an admin key")
    is_active: bool = Field(..., description="Whether this key is active")
    created_at: datetime = Field(..., description="When the key was created")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    revoked_at: Optional[datetime] = Field(None, description="When the key was revoked")
    created_by: Optional[str] = Field(None, description="Who created this key")

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreateResponse(ApiKeyResponse):
    """Response when creating a new API key (includes plaintext key)."""

    api_key: str = Field(
        ..., 
        description="Plaintext API key (only shown once, store securely)",
        examples=["qmp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"]
    )
