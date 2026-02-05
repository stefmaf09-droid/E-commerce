"""
Database Migration Script - Add POD Auto-Fetch Columns

Adds necessary columns to support automatic POD retrieval.
"""

import os
import sys
import sqlite3
import logging

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from src.database.database_manager import get_db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_pod_columns():
    """Add POD-related columns to claims table."""
    
    logger.info("Starting POD columns migration...")
    
    db = get_db_manager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(claims)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        columns_to_add = [
            ('pod_url', 'TEXT'),
            ('pod_fetch_status', "TEXT DEFAULT 'pending'"),
            ('pod_fetch_error', 'TEXT'),
            ('pod_fetched_at', 'TIMESTAMP'),
            ('pod_signature_url', 'TEXT'),
            ('pod_delivery_person', 'TEXT')
        ]
        
        added_count = 0
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                logger.info(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE claims ADD COLUMN {column_name} {column_type}")
                added_count += 1
            else:
                logger.info(f"Column {column_name} already exists, skipping")
        
        # Create index
        logger.info("Creating index on pod_fetch_status...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_claims_pod_status 
            ON claims(pod_fetch_status)
        """)
        
        conn.commit()
        
        logger.info(f"✅ Migration complete! Added {added_count} new columns.")
        
        # Show final schema
        cursor.execute("PRAGMA table_info(claims)")
        columns = cursor.fetchall()
        
        logger.info(f"\nCurrent claims table has {len(columns)} columns:")
        for col in columns:
            if col[1].startswith('pod_'):
                logger.info(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DATABASE MIGRATION: Add POD Auto-Fetch Columns")
    print("="*70 + "\n")
    
    add_pod_columns()
    
    print("\n" + "="*70)
    print("Migration completed successfully!")
    print("="*70 + "\n")
