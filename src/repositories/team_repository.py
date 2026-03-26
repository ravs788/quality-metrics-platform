"""
Team repository for data access operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from src.models.db_models import Team


class TeamRepository:
    """Repository for Team entity data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, team_name: str) -> Optional[Team]:
        """Get team by name."""
        return self.db.query(Team).filter(Team.team_name == team_name).first()
    
    def create(self, team_name: str) -> Team:
        """Create a new team."""
        team = Team(team_name=team_name)
        self.db.add(team)
        self.db.flush()  # Get team_id without committing
        return team
    
    def get_or_create(self, team_name: Optional[str]) -> Optional[Team]:
        """
        Get existing team by name or create if not exists.
        Returns None if team_name is None.
        """
        if not team_name:
            return None
        
        team = self.get_by_name(team_name)
        if not team:
            team = self.create(team_name)
        
        return team