# Quality Metrics Platform - Database Setup

This directory contains the database schema and seed data scripts for the Quality Metrics Platform.

## Prerequisites

- PostgreSQL 14+ installed and running
- Python 3.9+ (for dummy data generation)
- Required Python packages: `psycopg2-binary`, `faker`

## Quick Start

### 1. Install PostgreSQL (if not already installed)

**macOS (using Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Connect to PostgreSQL as postgres user
psql postgres

# Create database
CREATE DATABASE quality_metrics;

# Create user (optional, for production use)
CREATE USER qm_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE quality_metrics TO qm_user;

# Exit psql
\q
```

### 3. Create Schema

```bash
# Run schema creation script
psql -d quality_metrics -f database/schema.sql
```

### 4. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install psycopg2-binary faker
```

### 5. Generate Dummy Data

```bash
# Edit database/seed_data.py to configure database connection
# Update DB_CONFIG dictionary with your credentials

# Run data generation script
python database/seed_data.py
```

## Database Configuration

Edit the `DB_CONFIG` dictionary in `seed_data.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'quality_metrics',
    'user': 'postgres',        # Update with your username
    'password': 'postgres'     # Update with your password
}
```

## Schema Overview

### Tables

1. **teams** - Engineering teams using the platform
   - `team_id` (PK)
   - `team_name`
   - `team_lead`

2. **projects** - Projects tracked in the metrics platform
   - `project_id` (PK)
   - `project_name`
   - `team_id` (FK)
   - `repository_url`

3. **deployment_metrics** - CICD deployment metrics for DORA tracking
   - `metric_id` (PK)
   - `project_id` (FK)
   - `deployment_timestamp`
   - `deployment_status` (success/failed/rollback)
   - `lead_time_hours`
   - `build_duration_minutes`
   - `environment` (dev/staging/production)

4. **defect_metrics** - Bug/defect tracking metrics
   - `defect_id` (PK)
   - `project_id` (FK)
   - `defect_key` (e.g., BUG-123)
   - `priority` (critical/high/medium/low)
   - `severity` (blocker/critical/major/minor/trivial)
   - `status` (open/in_progress/resolved/closed/reopened)
   - `resolution_time_hours`

5. **coverage_metrics** - Test coverage metrics over time
   - `coverage_id` (PK)
   - `project_id` (FK)
   - `coverage_timestamp`
   - `line_coverage_percent`
   - `branch_coverage_percent`
   - `total_lines`, `covered_lines`

### Views

1. **dora_metrics_summary** - Pre-aggregated DORA metrics
   - Daily aggregations by project
   - Deployment frequency, lead time, change failure rate

2. **defect_trends_summary** - Weekly defect trend aggregations
   - Defects created/resolved by week
   - High priority defect tracking

3. **coverage_trends_summary** - Weekly test coverage trends
   - Average, min, max coverage by week

## Dummy Data Generated

Running `seed_data.py` will create:

- **3 teams** (Platform Engineering, Backend Services, Frontend Experience)
- **6 projects** (2 per team)
- **~900 deployment records** (150 per project, covering 5 months)
- **600 defect records** (100 per project)
- **~120 coverage records** (weekly records for 5 months)

Total: **~1,620 records** across all tables

## Sample Queries

### Get DORA Metrics for Last 30 Days

```sql
SELECT 
    project_name,
    metric_date,
    successful_deployments,
    avg_lead_time_hours,
    change_failure_rate_percent
FROM dora_metrics_summary
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date DESC, project_name;
```

### Get Defect Trends by Priority

```sql
SELECT 
    week_start,
    SUM(defects_created) as total_created,
    SUM(high_priority_defects) as high_priority,
    AVG(avg_resolution_time_hours) as avg_resolution_hours
FROM defect_trends_summary
WHERE week_start >= CURRENT_DATE - INTERVAL '8 weeks'
GROUP BY week_start
ORDER BY week_start DESC;
```

### Get Coverage Trends

```sql
SELECT 
    project_name,
    week_start,
    avg_line_coverage,
    avg_branch_coverage
FROM coverage_trends_summary
WHERE week_start >= CURRENT_DATE - INTERVAL '12 weeks'
ORDER BY week_start DESC, project_name;
```

### Get Active Defects by Project

```sql
SELECT 
    p.project_name,
    d.priority,
    COUNT(*) as open_defects,
    AVG(EXTRACT(EPOCH FROM (NOW() - d.created_date))/3600) as avg_age_hours
FROM defect_metrics d
JOIN projects p ON d.project_id = p.project_id
WHERE d.status IN ('open', 'in_progress')
GROUP BY p.project_name, d.priority
ORDER BY p.project_name, 
    CASE d.priority 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        WHEN 'low' THEN 4 
    END;
```

## Connecting to Database

### Using psql

```bash
psql -d quality_metrics -U postgres

# List tables
\dt

# Describe table
\d deployment_metrics

# List views
\dv

# Run query
SELECT * FROM dora_metrics_summary LIMIT 10;
```

### Using Python

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="quality_metrics",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM deployment_metrics")
print(f"Total deployments: {cursor.fetchone()[0]}")
cursor.close()
conn.close()
```

## Database Maintenance

### Backup Database

```bash
pg_dump -U postgres quality_metrics > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
psql -U postgres quality_metrics < backup_20260317.sql
```

### Reset Database

```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE IF EXISTS quality_metrics;"
psql -U postgres -c "CREATE DATABASE quality_metrics;"

# Recreate schema and data
psql -d quality_metrics -f database/schema.sql
python database/seed_data.py
```

## Troubleshooting

### Connection refused

```bash
# Check if PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Start PostgreSQL if not running
brew services start postgresql@14  # macOS
sudo systemctl start postgresql  # Linux
```

### Permission denied

```bash
# Make sure user has proper permissions
psql postgres
GRANT ALL PRIVILEGES ON DATABASE quality_metrics TO postgres;
```

### Python psycopg2 installation issues

```bash
# On macOS, if you get SSL errors:
pip install psycopg2-binary

# On Linux, install PostgreSQL development headers:
sudo apt-get install libpq-dev python3-dev
pip install psycopg2
```

## Next Steps

1. Set up FastAPI application to query this database
2. Configure Grafana to connect to PostgreSQL
3. Create Grafana dashboards using the views
4. Add API endpoints for data ingestion
5. Implement authentication and authorization

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [DORA Metrics Guide](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)
