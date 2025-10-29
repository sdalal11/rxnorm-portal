#!/usr/bin/env python3
import psycopg2

DATABASE_URL = "postgresql://postgres:Sanjana123!@db.ynbsbpmyzubwkmfgdzes.supabase.co:5432/postgres"

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    
    # Update ayushi to folder 1
    cursor.execute("UPDATE users SET assigned_folder = %s WHERE username = %s", ('1', 'ayushi@turmerik.ai'))
    conn.commit()
    print("✅ Updated ayushi@turmerik.ai to folder 1")
    
    # Show current assignments
    cursor.execute("SELECT username, name, assigned_folder, assignment_order FROM users ORDER BY registered_at")
    users = cursor.fetchall()
    print("\nCurrent user assignments:")
    for user in users:
        print(f"  {user[1]} ({user[0]}) -> Folder: {user[2]}, Order: {user[3]}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")