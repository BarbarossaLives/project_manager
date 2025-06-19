#!/usr/bin/env python3
"""
Database migration script for Project Manager
Adds new columns for AI features to existing database
"""

import sqlite3
import logging
from pathlib import Path
import sys

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    """Get the database file path from config"""
    db_url = config.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return "project_tracker.db"

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_tasks_table(cursor):
    """Add new columns to tasks table"""
    logger.info("🔄 Migrating tasks table...")
    
    migrations = [
        ("description", "TEXT"),
        ("estimated_hours", "REAL"),
        ("priority", "TEXT DEFAULT 'medium'"),
        ("ai_generated", "BOOLEAN DEFAULT 0"),
        ("parent_task_id", "INTEGER"),
        ("order_index", "INTEGER DEFAULT 0"),
        ("skills_required", "TEXT"),  # JSON field
        ("dependencies", "TEXT"),     # JSON field
    ]
    
    for column_name, column_type in migrations:
        if not check_column_exists(cursor, "tasks", column_name):
            try:
                cursor.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_type}")
                logger.info(f"✅ Added column: tasks.{column_name}")
            except sqlite3.Error as e:
                logger.error(f"❌ Failed to add column tasks.{column_name}: {e}")
        else:
            logger.info(f"⏭️  Column tasks.{column_name} already exists")

def create_new_tables(cursor):
    """Create new tables for AI features"""
    logger.info("🔄 Creating new AI feature tables...")
    
    # ProjectPlan table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_plans (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            ai_generated BOOLEAN DEFAULT 1,
            plan_data TEXT,  -- JSON field
            estimated_duration_weeks INTEGER,
            difficulty_level TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    """)
    logger.info("✅ Created/verified project_plans table")
    
    # ProjectMilestone table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_milestones (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            name TEXT,
            description TEXT,
            target_week INTEGER,
            completed BOOLEAN DEFAULT 0,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    """)
    logger.info("✅ Created/verified project_milestones table")
    
    # ProjectRisk table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_risks (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            risk_description TEXT,
            impact_level TEXT,
            mitigation_strategy TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    """)
    logger.info("✅ Created/verified project_risks table")
    
    # ScheduleAdjustment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_adjustments (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            task_id INTEGER,
            adjustment_reason TEXT,
            old_deadline DATETIME,
            new_deadline DATETIME,
            ai_suggested BOOLEAN DEFAULT 1,
            applied BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    """)
    logger.info("✅ Created/verified schedule_adjustments table")

    # Event table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            all_day BOOLEAN DEFAULT 0,
            location TEXT,
            event_type TEXT DEFAULT 'personal',
            priority TEXT DEFAULT 'medium',
            completed BOOLEAN DEFAULT 0,
            project_id INTEGER,
            task_id INTEGER,
            recurring BOOLEAN DEFAULT 0,
            recurrence_pattern TEXT,
            recurrence_end DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    """)
    logger.info("✅ Created/verified events table")

    # Add missing columns to tasks table
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN created_at DATETIME")
        cursor.execute("UPDATE tasks SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        logger.info("✅ Added created_at column to tasks table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("✅ created_at column already exists in tasks table")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN updated_at DATETIME")
        cursor.execute("UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
        logger.info("✅ Added updated_at column to tasks table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("✅ updated_at column already exists in tasks table")
        else:
            raise

def backup_database(db_path):
    """Create a backup of the database before migration"""
    backup_path = f"{db_path}.backup"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        return None

def main():
    """Main migration function"""
    print("🔄 Database Migration for AI Features")
    print("=" * 50)
    
    db_path = get_db_path()
    logger.info(f"📍 Database path: {db_path}")
    
    # Check if database exists
    if not Path(db_path).exists():
        logger.error(f"❌ Database file not found: {db_path}")
        logger.info("💡 Run the application first to create the database")
        return False
    
    # Create backup
    backup_path = backup_database(db_path)
    if not backup_path:
        response = input("⚠️  Could not create backup. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            logger.info("❌ Migration cancelled")
            return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Perform migrations
        migrate_tasks_table(cursor)
        create_new_tables(cursor)
        
        # Commit changes
        conn.commit()
        logger.info("✅ All migrations completed successfully")
        
        # Verify migrations
        cursor.execute("PRAGMA table_info(tasks)")
        task_columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"📋 Tasks table columns: {', '.join(task_columns)}")
        
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        print("✅ Database is now ready for AI features")
        
        if backup_path:
            print(f"💾 Backup saved at: {backup_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        
        if backup_path:
            logger.info(f"💡 You can restore from backup: {backup_path}")
        
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
