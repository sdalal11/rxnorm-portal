import psycopg2
import os

# Test connection to Supabase
connection_string = "postgresql://postgres:Sanjana123!@db.ynbsbpmyzubwkmfgdzes.supabase.co:5432/postgres"

print("Testing PostgreSQL connection...")
print(f"Connection string: {connection_string}")

try:
    conn = psycopg2.connect(connection_string)
    print("✅ Connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    result = cursor.fetchone()
    print(f"PostgreSQL version: {result[0]}")
    
    # Test if users table exists
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'users';
    """)
    users_table = cursor.fetchone()
    if users_table:
        print("✅ 'users' table found")
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print("Users table columns:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
    else:
        print("❌ 'users' table not found")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print(f"Error type: {type(e).__name__}")