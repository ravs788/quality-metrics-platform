"""
Unit tests for CRUD operations.
"""

import pytest
from datetime import date
from sqlalchemy.orm import Session

from src.crud import get_or_create_team, get_or_create_project
from src.models.db_models import Team


class TestTeamAndProjectCreation:
    """Test team and project auto-creation logic."""
    
    def test_get_or_create_team_new(self, test_db: Session):
        """Test creating a new team."""
        team = get_or_create_team(test_db, "New Team")
        
        assert team is not None
        assert team.team_name == "New Team"
        assert team.team_id is not None
    
    def test_get_or_create_team_existing(self, test_db: Session):
        """Test retrieving an existing team."""
        team1 = get_or_create_team(test_db, "Existing Team")
        team1_id = team1.team_id
        
        team2 = get_or_create_team(test_db, "Existing Team")
        
        assert team2.team_id == team1_id
    
    def test_get_or_create_project_new(self, test_db: Session, sample_team: Team):
        """Test creating a new project."""
        project = get_or_create_project(test_db, "New Project", sample_team)
        
        assert project is not None
        assert project.project_name == "New Project"
        assert project.team_id == sample_team.team_id
