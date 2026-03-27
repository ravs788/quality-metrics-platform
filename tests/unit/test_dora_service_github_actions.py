"""Unit tests for GitHub Actions deployment ingestion mapping in DoraService."""

from datetime import datetime, timezone
from unittest.mock import Mock

from src.services import DoraService


class TestDoraServiceGitHubActionsMapping:
    """Validate payload mapping behavior for GitHub Actions ingestion."""

    def test_ingest_github_actions_uses_repository_fallback_project(self, mock_db_session):
        """Repository owner/repo should map to repo name when project_name is missing."""
        service = DoraService(mock_db_session)
        service.create_deployment_metric = Mock(return_value=object())

        run_started_at = datetime(2026, 3, 27, 10, 30, tzinfo=timezone.utc)

        service.ingest_github_actions_deployment(
            repository="acme/api-gateway",
            status="completed",
            conclusion="success",
            run_started_at=run_started_at,
            team_name="Platform Team",
            lead_time_hours=2.25,
            environment="production",
        )

        service.create_deployment_metric.assert_called_once_with(
            project_name="api-gateway",
            team_name="Platform Team",
            metric_date=run_started_at.date(),
            successful=True,
            lead_time_hours=2.25,
            environment="production",
        )

    def test_ingest_github_actions_maps_non_success_to_failed(self, mock_db_session):
        """Completed runs with non-success conclusions should map to failed deployments."""
        service = DoraService(mock_db_session)
        service.create_deployment_metric = Mock(return_value=object())

        run_started_at = datetime(2026, 3, 27, 10, 30, tzinfo=timezone.utc)

        service.ingest_github_actions_deployment(
            repository="acme/api-gateway",
            status="completed",
            conclusion="failure",
            run_started_at=run_started_at,
            project_name="API Gateway Service",
            environment="staging",
        )

        service.create_deployment_metric.assert_called_once_with(
            project_name="API Gateway Service",
            team_name=None,
            metric_date=run_started_at.date(),
            successful=False,
            lead_time_hours=None,
            environment="staging",
        )
