"""
Database migration script to upgrade from single-store to multi-store support.

This script migrates existing credentials to the new multi-store schema.
"""

import sqlite3
import os
from pathlib import Path


def migrate_to_multi_store():
    """Migrate database from single-store to multi-store schema."""
    
    db_path = "database/credentials.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Nothing to migrate.")
        return False
    
    # Backup first
    backup_path = f"{db_path}.backup"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if already migrated
        cursor.execute("PRAGMA table_info(credentials)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'id' in columns and 'store_name' in columns:
            print("✅ Database already migrated to multi-store schema.")
            return True
        
        print("🔄 Migrating database schema...")
        
        # Create new table with multi-store support
        cursor.execute("""
            CREATE TABLE credentials_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                store_name TEXT,
                credentials_encrypted BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, platform, store_name)
            )
        """)
        
        # Copy data from old table
        cursor.execute("""
            INSERT INTO credentials_new (client_id, platform, credentials_encrypted, created_at, updated_at)
            SELECT client_id, platform, credentials_encrypted, created_at, updated_at
            FROM credentials
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE credentials")
        
        # Rename new table
        cursor.execute("ALTER TABLE credentials_new RENAME TO credentials")
        
        # Update sync_status table
        cursor.execute("DROP TABLE IF EXISTS sync_status")
        cursor.execute("""
            CREATE TABLE sync_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credential_id INTEGER NOT NULL,
                last_sync TIMESTAMP,
                last_order_id TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (credential_id) REFERENCES credentials(id)
            )
        """)
        
        conn.commit()
        print("✅ Migration successful!")
        print(f"📊 Migrated {cursor.rowcount} credential(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        
        # Restore backup
        conn.close()
        shutil.copy2(backup_path, db_path)
        print(f"⚠️ Database restored from backup")
        
        return False
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("="*70)
    print("DATABASE MIGRATION - Single Store → Multi-Store")
    print("="*70)
    print()
    
    success = migrate_to_multi_store()
    
    print()
    print("="*70)
    
    if success:
        print("✅ Migration Complete!")
        print()
        print("You can now add multiple stores per client:")
        print("  manager.store_credentials(email, 'shopify', creds, 'Store 1')")
        print("  manager.store_credentials(email, 'woocommerce', creds, 'Store 2')")
    else:
        print("❌ Migration Failed")
    
    print("="*70)
