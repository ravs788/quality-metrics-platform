"""
Quality Metrics Platform - Dummy Data Generator
Generates realistic seed data for development and testing
"""

import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'quality_metrics',
    'user': 'postgres',
    'password': 'mysecretpassword'
}

# Configuration
NUM_TEAMS = 3
NUM_PROJECTS_PER_TEAM = 2
NUM_DEPLOYMENTS_PER_PROJECT = 150  # ~5 months of daily deployments
NUM_DEFECTS_PER_PROJECT = 100
NUM_COVERAGE_RECORDS_PER_PROJECT = 100

TEAMS_DATA = [
    ('Platform Engineering', 'Sarah Chen'),
    ('Backend Services', 'Michael Rodriguez'),
    ('Frontend Experience', 'Emily Johnson')
]

PROJECT_NAMES = [
    'API Gateway', 'User Service', 'Payment Service',
    'Web Dashboard', 'Mobile App', 'Analytics Engine'
]

COMPONENTS = [
    'Authentication', 'Database', 'API', 'UI', 'Cache',
    'Queue', 'Storage', 'Notification', 'Search', 'Analytics'
]


def create_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise


def insert_teams(conn):
    """Insert team data"""
    cursor = conn.cursor()
    teams = []
    
    for team_name, team_lead in TEAMS_DATA:
        teams.append((team_name, team_lead))
    
    cursor.executemany(
        "INSERT INTO teams (team_name, team_lead) VALUES (%s, %s)",
        teams
    )
    conn.commit()
    
    # Get team IDs
    cursor.execute("SELECT team_id, team_name FROM teams ORDER BY team_id")
    team_ids = {name: tid for tid, name in cursor.fetchall()}
    
    cursor.close()
    print(f"✓ Inserted {len(teams)} teams")
    return team_ids


def insert_projects(conn, team_ids):
    """Insert project data"""
    cursor = conn.cursor()
    projects = []
    
    project_idx = 0
    for team_name, team_id in team_ids.items():
        for i in range(NUM_PROJECTS_PER_TEAM):
            if project_idx < len(PROJECT_NAMES):
                project_name = PROJECT_NAMES[project_idx]
                repo_url = f"https://github.com/company/{project_name.lower().replace(' ', '-')}"
                projects.append((project_name, team_id, repo_url))
                project_idx += 1
    
    cursor.executemany(
        "INSERT INTO projects (project_name, team_id, repository_url) VALUES (%s, %s, %s)",
        projects
    )
    conn.commit()
    
    # Get project IDs
    cursor.execute("SELECT project_id FROM projects ORDER BY project_id")
    project_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    print(f"✓ Inserted {len(projects)} projects")
    return project_ids


def insert_deployment_metrics(conn, project_ids):
    """Insert deployment metrics data"""
    cursor = conn.cursor()
    deployments = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=150)
    
    for project_id in project_ids:
        current_date = start_date
        
        while current_date <= end_date:
            # Generate 0-3 deployments per day
            num_deployments = random.choices([0, 1, 2, 3], weights=[10, 40, 30, 20])[0]
            
            for _ in range(num_deployments):
                deployment_time = current_date + timedelta(
                    hours=random.randint(8, 18),
                    minutes=random.randint(0, 59)
                )
                
                # 85% success rate
                status = random.choices(
                    ['success', 'failed', 'rollback'],
                    weights=[85, 12, 3]
                )[0]
                
                # Lead time: 1-72 hours, most between 4-24 hours
                lead_time = round(random.triangular(1, 72, 8), 2)
                
                # Build duration: 5-60 minutes
                build_duration = round(random.triangular(5, 60, 15), 2)
                
                commit_sha = fake.sha1()[:40]
                environment = random.choices(
                    ['dev', 'staging', 'production'],
                    weights=[50, 30, 20]
                )[0]
                
                # Deployment frequency score (1-5, higher is better)
                freq_score = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 25, 35, 25])[0]
                
                deployments.append((
                    project_id,
                    deployment_time,
                    status,
                    lead_time,
                    build_duration,
                    commit_sha,
                    environment,
                    freq_score
                ))
            
            current_date += timedelta(days=1)
    
    execute_values(
        cursor,
        """
        INSERT INTO deployment_metrics 
        (project_id, deployment_timestamp, deployment_status, lead_time_hours, 
         build_duration_minutes, commit_sha, environment, deployment_frequency_score)
        VALUES %s
        """,
        deployments
    )
    conn.commit()
    cursor.close()
    print(f"✓ Inserted {len(deployments)} deployment records")


def insert_defect_metrics(conn, project_ids):
    """Insert defect metrics data"""
    cursor = conn.cursor()
    defects = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=150)
    
    defect_counter = 1
    
    for project_id in project_ids:
        for _ in range(NUM_DEFECTS_PER_PROJECT):
            created_date = start_date + timedelta(
                days=random.randint(0, 150),
                hours=random.randint(0, 23)
            )
            
            # 70% of defects are resolved
            is_resolved = random.random() < 0.70
            
            if is_resolved:
                # Resolution time: 1 hour to 14 days
                resolution_hours = round(random.triangular(1, 336, 48), 2)
                resolved_date = created_date + timedelta(hours=resolution_hours)
                status = random.choice(['resolved', 'closed'])
            else:
                resolution_hours = None
                resolved_date = None
                status = random.choice(['open', 'in_progress'])
            
            priority = random.choices(
                ['critical', 'high', 'medium', 'low'],
                weights=[10, 25, 45, 20]
            )[0]
            
            severity = random.choices(
                ['blocker', 'critical', 'major', 'minor', 'trivial'],
                weights=[5, 15, 35, 35, 10]
            )[0]
            
            component = random.choice(COMPONENTS)
            assigned_to = fake.name()
            
            defect_key = f"BUG-{project_id}-{defect_counter}"
            title = f"{fake.catch_phrase()} - {component} issue"
            
            defects.append((
                project_id,
                defect_key,
                title,
                priority,
                severity,
                status,
                component,
                created_date,
                resolved_date,
                resolution_hours,
                assigned_to
            ))
            
            defect_counter += 1
    
    execute_values(
        cursor,
        """
        INSERT INTO defect_metrics 
        (project_id, defect_key, title, priority, severity, status, component,
         created_date, resolved_date, resolution_time_hours, assigned_to)
        VALUES %s
        """,
        defects
    )
    conn.commit()
    cursor.close()
    print(f"✓ Inserted {len(defects)} defect records")


def insert_coverage_metrics(conn, project_ids):
    """Insert test coverage metrics data"""
    cursor = conn.cursor()
    coverage_records = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=150)
    
    for project_id in project_ids:
        # Initial coverage baseline (40-60%)
        base_line_coverage = random.uniform(40, 60)
        base_branch_coverage = base_line_coverage - random.uniform(5, 15)
        
        current_date = start_date
        
        while current_date <= end_date:
            # Coverage gradually improves over time with some variance
            days_elapsed = (current_date - start_date).days
            improvement = days_elapsed * 0.05  # 0.05% per day
            
            line_coverage = min(
                95,
                base_line_coverage + improvement + random.uniform(-3, 5)
            )
            branch_coverage = min(
                90,
                base_branch_coverage + improvement + random.uniform(-3, 5)
            )
            
            # Total lines: 10k-100k
            total_lines = random.randint(10000, 100000)
            covered_lines = int(total_lines * line_coverage / 100)
            
            # Total branches: ~30% of lines
            total_branches = int(total_lines * 0.3)
            covered_branches = int(total_branches * branch_coverage / 100)
            
            component = random.choice(COMPONENTS)
            commit_sha = fake.sha1()[:40]
            
            coverage_records.append((
                project_id,
                current_date,
                round(line_coverage, 2),
                round(branch_coverage, 2),
                total_lines,
                covered_lines,
                total_branches,
                covered_branches,
                component,
                commit_sha
            ))
            
            # Coverage recorded weekly
            current_date += timedelta(days=7)
    
    execute_values(
        cursor,
        """
        INSERT INTO coverage_metrics 
        (project_id, coverage_timestamp, line_coverage_percent, branch_coverage_percent,
         total_lines, covered_lines, total_branches, covered_branches, component, commit_sha)
        VALUES %s
        """,
        coverage_records
    )
    conn.commit()
    cursor.close()
    print(f"✓ Inserted {len(coverage_records)} coverage records")


def print_summary(conn):
    """Print data summary"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    
    cursor.execute("SELECT COUNT(*) FROM teams")
    print(f"Teams: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM projects")
    print(f"Projects: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM deployment_metrics")
    print(f"Deployment records: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM defect_metrics")
    print(f"Defect records: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM coverage_metrics")
    print(f"Coverage records: {cursor.fetchone()[0]}")
    
    print("\nSample DORA Metrics (Last 7 days):")
    cursor.execute("""
        SELECT 
            project_name,
            successful_deployments,
            failed_deployments,
            avg_lead_time_hours,
            change_failure_rate_percent
        FROM dora_metrics_summary
        WHERE metric_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY metric_date DESC, project_name
        LIMIT 10
    """)
    
    print(f"\n{'Project':<20} {'Success':<10} {'Failed':<10} {'Avg Lead (hrs)':<15} {'Fail Rate %':<12}")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<10} {row[2]:<10} {row[3]:<15} {row[4]:<12}")
    
    cursor.close()
    print("\n" + "="*60)


def main():
    """Main execution function"""
    print("Quality Metrics Platform - Dummy Data Generator")
    print("=" * 60)
    
    try:
        conn = create_connection()
        print("✓ Connected to database\n")
        
        # Insert data
        team_ids = insert_teams(conn)
        project_ids = insert_projects(conn, team_ids)
        insert_deployment_metrics(conn, project_ids)
        insert_defect_metrics(conn, project_ids)
        insert_coverage_metrics(conn, project_ids)
        
        # Print summary
        print_summary(conn)
        
        conn.close()
        print("\n✓ Data generation complete!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
