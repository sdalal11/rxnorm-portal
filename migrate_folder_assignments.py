#!/usr/bin/env python3
"""
Database migration script to add folder assignment columns to existing users table.
This script can be run safely multiple times - it only adds columns if they don't exist.

Usage:
    python3 migrate_folder_assignments.py

Requirements:
    - Set DATABASE_URL environment variable for Supabase connection
    - Or the script will use local SQLite for testing
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path to import from api_server
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the database migration to add folder assignment columns"""
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        print("🔗 Connecting to Supabase PostgreSQL database...")
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()
            is_postgres = True
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            return False
    else:
        print("⚠️  DATABASE_URL not set, using local SQLite for testing...")
        import sqlite3
        conn = sqlite3.connect('/tmp/users.db')
        cursor = conn.cursor()
        is_postgres = False
    
    print("📋 Starting folder assignment migration...")
    
    try:
        # Check current table structure
        if is_postgres:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
        else:
            cursor.execute("PRAGMA table_info(users)")
        
        existing_columns = cursor.fetchall()
        print(f"📊 Current table columns: {[col[0] if is_postgres else col[1] for col in existing_columns]}")
        
        # Add columns if they don't exist
        columns_to_add = [
            ('assigned_folder', 'VARCHAR(50)' if is_postgres else 'TEXT'),
            ('assignment_order', 'INTEGER'),
            ('login_timestamp', 'TIMESTAMP' if is_postgres else 'DATETIME')
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                print(f"🔧 Adding column: {column_name} ({column_type})")
                cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                conn.commit()
                print(f"✅ Added {column_name} column successfully")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"ℹ️  Column {column_name} already exists, skipping...")
                else:
                    print(f"⚠️  Error adding {column_name}: {e}")
        
        # Show updated table structure
        print("\n📋 Updated table structure:")
        if is_postgres:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]} {'NULL' if col[3] == 0 else 'NOT NULL'}")
        
        # Show current users and their folder assignments
        print("\n👥 Current users:")
        cursor.execute("SELECT username, assigned_folder, assignment_order FROM users")
        users = cursor.fetchall()
        
        if users:
            for user in users:
                folder = user[1] if user[1] else "Not assigned"
                order = user[2] if user[2] else "N/A"
                print(f"  - {user[0]}: {folder} (Order: {order})")
        else:
            print("  No users found")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Deploy your updated api_server.py to Render")
        print("2. Users will get folder assignments on their next login")
        print("3. Folder assignments will persist across server restarts")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    print("🚀 RxNorm Folder Assignment Migration")
    print("=" * 50)
    
    if not os.environ.get('DATABASE_URL'):
        print("⚠️  Warning: DATABASE_URL not set.")
        print("   For Supabase migration, set your DATABASE_URL environment variable:")
        print("   export DATABASE_URL='postgresql://user:pass@host:5432/database'")
        print("   For now, running on local SQLite for testing...\n")
    
    success = run_migration()
    
    if success:
        print("\n🎉 Migration completed!")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)