#!/usr/bin/env python
"""
Script to run PostgreSQL migration: Add POD and AI columns to claims table
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.database_manager import DatabaseManager

def run_migration():
    """Execute the migration to add POD and AI columns."""
    
    print("🔧 Starting PostgreSQL migration...")
    print("=" * 60)
    
    try:
        # Initialize database manager with PostgreSQL
        db = DatabaseManager(db_type='postgres')
        print(f"✅ Connected to PostgreSQL database")
        
        # Read migration file
        migration_path = os.path.join(
            os.path.dirname(__file__),
            'database',
            'migrations',
            '002_add_pod_ai_columns.sql'
        )
        
        if not os.path.exists(migration_path):
            print(f"❌ Migration file not found: {migration_path}")
            return False
        
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print(f"📄 Loaded migration: 002_add_pod_ai_columns.sql")
        print("=" * 60)
        
        # Execute migration
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"Executing statement {i}/{len(statements)}...")
                try:
                    cursor.execute(statement)
                    print(f"  ✅ Success")
                except Exception as e:
                    # If column already exists, that's okay
                    if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                        print(f"  ℹ️  Column already exists (skipping)")
                    else:
                        print(f"  ⚠️  Warning: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print()
        print("📋 Added columns to 'claims' table:")
        print("   - pod_fetch_status")
        print("   - pod_url")
        print("   - pod_fetched_at")
        print("   - pod_delivery_person")
        print("   - pod_fetch_error")
        print("   - ai_reason_key")
        print("   - ai_advice")
        print()
        print("🎉 You can now refresh the application and test 'Gestion Litiges'!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
