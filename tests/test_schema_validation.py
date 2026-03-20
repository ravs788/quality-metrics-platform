"""
Unit tests for Pydantic schema validation.

These tests primarily exist to kill schema-related survived mutations
(e.g., relaxing validation bounds).
"""

import pytest
from pydantic import ValidationError

from src.models.schemas import DeploymentMetricCreate


def test_deployment_metric_lead_time_hours_non_negative():
    """lead_time_hours is defined as ge=0; negative values should be rejected."""
    with pytest.raises(ValidationError):
        DeploymentMetricCreate(
            project_name="api-gateway",
            team_name="platform-engineering",
            metric_date=None,
            successful=True,
            lead_time_hours=-0.01,
        )
