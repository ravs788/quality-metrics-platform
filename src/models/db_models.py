"""
SQLAlchemy ORM models for Quality Metrics Platform.

Maps to the PostgreSQL schema defined in database/schema.sql.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, TIMESTAMP, ForeignKey,
    CheckConstraint, DECIMAL, VARCHAR, Boolean
)
from sqlalchemy.orm import relationship

from src.database import Base


class Team(Base):
    """Engineering teams using the platform."""
    
    __tablename__ = "teams"
    
    team_id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(VARCHAR(100), nullable=False, unique=True)
    team_lead = Column(VARCHAR(100))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="team")
    api_keys = relationship("ApiKey", back_populates="team")


class ApiKey(Base):
    """API keys for authentication and authorization."""
    
    __tablename__ = "api_keys"
    
    key_id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=False)
    key_name = Column(VARCHAR(100), nullable=False)
    key_hash = Column(VARCHAR(64), unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_used_at = Column(TIMESTAMP)
    revoked_at = Column(TIMESTAMP)
    created_by = Column(VARCHAR(100))
    
    # Relationships
    team = relationship("Team", back_populates="api_keys")


class Project(Base):
    """Projects tracked in the metrics platform."""
    
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(VARCHAR(100), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.team_id"))
    repository_url = Column(VARCHAR(255))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="projects")
    deployment_metrics = relationship("DeploymentMetric", back_populates="project")
    defect_metrics = relationship("DefectMetric", back_populates="project")
    coverage_metrics = relationship("CoverageMetric", back_populates="project")


class DeploymentMetric(Base):
    """CICD deployment metrics for DORA tracking."""
    
    __tablename__ = "deployment_metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"))
    deployment_timestamp = Column(TIMESTAMP, nullable=False)
    deployment_status = Column(
        VARCHAR(20), 
        nullable=False,
        # CheckConstraint handled at DB level
    )
    lead_time_hours = Column(DECIMAL(10, 2))
    build_duration_minutes = Column(DECIMAL(10, 2))
    commit_sha = Column(VARCHAR(40))
    environment = Column(VARCHAR(20))
    deployment_frequency_score = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="deployment_metrics")


class DefectMetric(Base):
    """Bug tracking data."""
    
    __tablename__ = "defect_metrics"
    
    defect_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"))
    defect_key = Column(VARCHAR(50), unique=True, nullable=False)
    title = Column(VARCHAR(255), nullable=False)
    priority = Column(VARCHAR(20))
    severity = Column(VARCHAR(20))
    status = Column(VARCHAR(20))
    component = Column(VARCHAR(100))
    created_date = Column(TIMESTAMP, nullable=False)
    resolved_date = Column(TIMESTAMP)
    resolution_time_hours = Column(DECIMAL(10, 2))
    assigned_to = Column(VARCHAR(100))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="defect_metrics")


class CoverageMetric(Base):
    """Test coverage metrics."""
    
    __tablename__ = "coverage_metrics"
    
    coverage_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"))
    coverage_timestamp = Column(TIMESTAMP, nullable=False)
    line_coverage_percent = Column(DECIMAL(5, 2))
    branch_coverage_percent = Column(DECIMAL(5, 2))
    total_lines = Column(Integer)
    covered_lines = Column(Integer)
    total_branches = Column(Integer)
    covered_branches = Column(Integer)
    component = Column(VARCHAR(100))
    commit_sha = Column(VARCHAR(40))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="coverage_metrics")
