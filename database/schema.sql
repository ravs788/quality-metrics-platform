-- Quality Metrics Platform Database Schema
-- PostgreSQL 14+

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS deployment_metrics CASCADE;
DROP TABLE IF EXISTS defect_metrics CASCADE;
DROP TABLE IF EXISTS coverage_metrics CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS teams CASCADE;

-- Teams table
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    team_lead VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys table (for authentication)
CREATE TABLE api_keys (
    key_id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_by VARCHAR(100)
);

-- Create indexes for API key lookups
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_team_id ON api_keys(team_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;

-- Projects table
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    team_id INTEGER REFERENCES teams(team_id),
    repository_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deployment metrics (CICD data)
CREATE TABLE deployment_metrics (
    metric_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(project_id),
    deployment_timestamp TIMESTAMP NOT NULL,
    deployment_status VARCHAR(20) NOT NULL CHECK (deployment_status IN ('success', 'failed', 'rollback')),
    lead_time_hours DECIMAL(10, 2),
    build_duration_minutes DECIMAL(10, 2),
    commit_sha VARCHAR(40),
    environment VARCHAR(20) CHECK (environment IN ('dev', 'staging', 'production')),
    deployment_frequency_score INTEGER CHECK (deployment_frequency_score BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on timestamp for time-series queries
CREATE INDEX idx_deployment_timestamp ON deployment_metrics(deployment_timestamp);
CREATE INDEX idx_deployment_project ON deployment_metrics(project_id);

-- Defect metrics (Bug tracking data)
CREATE TABLE defect_metrics (
    defect_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(project_id),
    defect_key VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    priority VARCHAR(20) CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    severity VARCHAR(20) CHECK (severity IN ('blocker', 'critical', 'major', 'minor', 'trivial')),
    status VARCHAR(20) CHECK (status IN ('open', 'in_progress', 'resolved', 'closed', 'reopened')),
    component VARCHAR(100),
    created_date TIMESTAMP NOT NULL,
    resolved_date TIMESTAMP,
    resolution_time_hours DECIMAL(10, 2),
    assigned_to VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for defect queries
CREATE INDEX idx_defect_created_date ON defect_metrics(created_date);
CREATE INDEX idx_defect_project ON defect_metrics(project_id);
CREATE INDEX idx_defect_status ON defect_metrics(status);

-- Test coverage metrics
CREATE TABLE coverage_metrics (
    coverage_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(project_id),
    coverage_timestamp TIMESTAMP NOT NULL,
    line_coverage_percent DECIMAL(5, 2) CHECK (line_coverage_percent BETWEEN 0 AND 100),
    branch_coverage_percent DECIMAL(5, 2) CHECK (branch_coverage_percent BETWEEN 0 AND 100),
    total_lines INTEGER,
    covered_lines INTEGER,
    total_branches INTEGER,
    covered_branches INTEGER,
    component VARCHAR(100),
    commit_sha VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for coverage queries
CREATE INDEX idx_coverage_timestamp ON coverage_metrics(coverage_timestamp);
CREATE INDEX idx_coverage_project ON coverage_metrics(project_id);

-- Create view for DORA metrics calculation
CREATE OR REPLACE VIEW dora_metrics_summary AS
SELECT 
    p.project_id,
    p.project_name,
    t.team_name,
    DATE_TRUNC('day', dm.deployment_timestamp) as metric_date,
    COUNT(*) FILTER (WHERE dm.deployment_status = 'success') as successful_deployments,
    COUNT(*) FILTER (WHERE dm.deployment_status = 'failed') as failed_deployments,
    ROUND(AVG(dm.lead_time_hours), 2) as avg_lead_time_hours,
    ROUND(
        (COUNT(*) FILTER (WHERE dm.deployment_status = 'failed')::DECIMAL / 
        NULLIF(COUNT(*), 0)) * 100, 2
    ) as change_failure_rate_percent
FROM deployment_metrics dm
JOIN projects p ON dm.project_id = p.project_id
JOIN teams t ON p.team_id = t.team_id
WHERE dm.environment = 'production'
GROUP BY p.project_id, p.project_name, t.team_name, DATE_TRUNC('day', dm.deployment_timestamp);

-- Create view for defect trends
CREATE OR REPLACE VIEW defect_trends_summary AS
SELECT 
    p.project_id,
    p.project_name,
    DATE_TRUNC('week', d.created_date) as week_start,
    COUNT(*) as defects_created,
    COUNT(*) FILTER (WHERE d.priority IN ('critical', 'high')) as high_priority_defects,
    COUNT(*) FILTER (WHERE d.status IN ('resolved', 'closed')) as defects_resolved,
    ROUND(AVG(d.resolution_time_hours), 2) as avg_resolution_time_hours
FROM defect_metrics d
JOIN projects p ON d.project_id = p.project_id
GROUP BY p.project_id, p.project_name, DATE_TRUNC('week', d.created_date);

-- Create view for coverage trends
CREATE OR REPLACE VIEW coverage_trends_summary AS
SELECT 
    p.project_id,
    p.project_name,
    DATE_TRUNC('week', c.coverage_timestamp) as week_start,
    ROUND(AVG(c.line_coverage_percent), 2) as avg_line_coverage,
    ROUND(AVG(c.branch_coverage_percent), 2) as avg_branch_coverage,
    MAX(c.line_coverage_percent) as max_line_coverage,
    MIN(c.line_coverage_percent) as min_line_coverage
FROM coverage_metrics c
JOIN projects p ON c.project_id = p.project_id
GROUP BY p.project_id, p.project_name, DATE_TRUNC('week', c.coverage_timestamp);

-- Add comments for documentation
COMMENT ON TABLE teams IS 'Engineering teams using the platform';
COMMENT ON TABLE api_keys IS 'API keys for authentication and authorization';
COMMENT ON TABLE projects IS 'Projects tracked in the metrics platform';
COMMENT ON TABLE deployment_metrics IS 'CICD deployment metrics for DORA tracking';
COMMENT ON TABLE defect_metrics IS 'Bug/defect tracking metrics';
COMMENT ON TABLE coverage_metrics IS 'Test coverage metrics over time';

COMMENT ON VIEW dora_metrics_summary IS 'Pre-aggregated DORA metrics for dashboards';
COMMENT ON VIEW defect_trends_summary IS 'Weekly defect trend aggregations';
COMMENT ON VIEW coverage_trends_summary IS 'Weekly test coverage trend aggregations';
