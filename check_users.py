#!/usr/bin/env python3
"""
Script to check users in the database
"""
import psycopg2
from urllib.parse import urlparse
import os
import sys

def check_users(database_url):
    """Check users in the PostgreSQL database"""
    try:
        print("Connecting to PostgreSQL database...")
        
        # Try direct connection first
        try:
            conn = psycopg2.connect(database_url, sslmode='require')
        except Exception as e:
            print(f"Direct connection failed: {e}")
            print("Trying with parsed URL...")
            
            # Parse and connect manually
            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password,
                sslmode='require'
            )
        
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ Users table does not exist in the database")
            return
        
        # First, check what columns exist in the users table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        print(f"\n📋 Users table structure:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")
        
        # Get all users with available columns
        if any(col[0] == 'created_at' for col in columns):
            cursor.execute('SELECT username, email, created_at FROM users ORDER BY created_at DESC;')
        else:
            cursor.execute('SELECT username, email FROM users;')
        
        users = cursor.fetchall()
        
        print(f"\n✅ Found {len(users)} users in PostgreSQL database:")
        print("-" * 60)
        
        if users:
            for i, user in enumerate(users, 1):
                print(f"{i}. Username: {user[0]}")
                print(f"   Email: {user[1]}")
                if len(user) > 2:  # If created_at exists
                    print(f"   Created: {user[2]}")
                print()
        else:
            print("No users found in the database.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("\nMake sure your DATABASE_URL is correct and the database is accessible.")

if __name__ == "__main__":
    # Check if DATABASE_URL is set as environment variable
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("DATABASE_URL environment variable not found.")
        print("Please provide your Supabase connection string:")
        database_url = input("DATABASE_URL: ").strip()
        
        if not database_url:
            print("No database URL provided. Exiting.")
            sys.exit(1)
    
    check_users(database_url)