#!/usr/bin/env python3

import psycopg2
import os

# Database connection
DATABASE_URL = "postgresql://postgres:Sanjana123!@db.ynbsbpmyzubwkmfgdzes.supabase.co:5432/postgres"

def check_and_fix_user():
    """Check ayushi's assignment and fix if needed"""
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        # Check current user data
        print("🔍 Checking current user data for ayushi@turmerik.ai...")
        cursor.execute("""
            SELECT id, username, email, name, assigned_folder, assignment_order, registered_at 
            FROM users 
            WHERE username = %s OR email = %s
        """, ('ayushi@turmerik.ai', 'ayushi@turmerik.ai'))
        
        user = cursor.fetchone()
        if user:
            print(f"📋 Current user data:")
            print(f"   ID: {user[0]}")
            print(f"   Username: {user[1]}")
            print(f"   Email: {user[2]}")
            print(f"   Name: {user[3]}")
            print(f"   Assigned Folder: {user[4]}")
            print(f"   Assignment Order: {user[5]}")
            print(f"   Registered At: {user[6]}")
            
            # If no folder assigned, assign one
            if user[4] is None:
                print("\n🔧 No folder assigned. Assigning folder now...")
                
                # Get the next assignment order
                cursor.execute("SELECT COALESCE(MAX(assignment_order), 0) FROM users WHERE assignment_order IS NOT NULL")
                max_order = cursor.fetchone()[0]
                next_order = max_order + 1
                assigned_folder = str(((next_order - 1) % 90) + 1)
                
                # Update the user
                cursor.execute("""
                    UPDATE users 
                    SET assigned_folder = %s, assignment_order = %s 
                    WHERE username = %s
                """, (assigned_folder, next_order, 'ayushi@turmerik.ai'))
                
                conn.commit()
                print(f"✅ Assigned folder {assigned_folder} to ayushi@turmerik.ai (order: {next_order})")
                
                # Verify the update
                cursor.execute("""
                    SELECT assigned_folder, assignment_order 
                    FROM users 
                    WHERE username = %s
                """, ('ayushi@turmerik.ai',))
                
                updated_user = cursor.fetchone()
                print(f"📋 Updated user data:")
                print(f"   Assigned Folder: {updated_user[0]}")
                print(f"   Assignment Order: {updated_user[1]}")
            else:
                print(f"✅ User already has folder {user[4]} assigned")
        else:
            print("❌ User ayushi@turmerik.ai not found in database")
        
        # Show all users with assignments
        print("\n📊 All users with folder assignments:")
        cursor.execute("""
            SELECT username, assigned_folder, assignment_order 
            FROM users 
            WHERE assigned_folder IS NOT NULL 
            ORDER BY assignment_order
        """)
        
        users = cursor.fetchall()
        for user in users:
            print(f"   {user[0]} → Folder {user[1]} (Order: {user[2]})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_and_fix_user()