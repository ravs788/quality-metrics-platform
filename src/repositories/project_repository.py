"""
Project repository for data access operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from src.models.db_models import Project, Team


class ProjectRepository:
    """Repository for Project entity data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name_and_team(
        self, 
        project_name: str, 
        team: Optional[Team]
    ) -> Optional[Project]:
        """Get project by name and team."""
        query = self.db.query(Project).filter(Project.project_name == project_name)
        
        if team:
            query = query.filter(Project.team_id == team.team_id)
        else:
            query = query.filter(Project.team_id.is_(None))
        
        return query.first()
    
    def create(self, project_name: str, team: Optional[Team]) -> Project:
        """Create a new project."""
        project = Project(
            project_name=project_name,
            team_id=team.team_id if team else None
        )
        self.db.add(project)
        self.db.flush()
        return project
    
    def get_or_create(
        self, 
        project_name: str, 
        team: Optional[Team]
    ) -> Project:
        """
        Get existing project by name and team, or create if not exists.
        """
        project = self.get_by_name_and_team(project_name, team)
        
        if not project:
            project = self.create(project_name, team)
        
        return project