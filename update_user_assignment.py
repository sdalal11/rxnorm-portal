#!/usr/bin/env python3
"""
Update user folder assignments in Supabase PostgreSQL database
"""

import psycopg2
import sys

# Database connection string
DATABASE_URL = "postgresql://postgres:Sanjana123!@db.ynbsbpmyzubwkmfgdzes.supabase.co:5432/postgres"

def update_user_assignment(username, assigned_folder, assignment_order=1):
    """Update user's folder assignment"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        # Update the user's assigned folder and order
        cursor.execute("""
            UPDATE users 
            SET assigned_folder = %s, assignment_order = %s 
            WHERE username = %s
        """, (assigned_folder, assignment_order, username))
        
        # Check if user was found and updated
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Updated user '{username}' - assigned to folder '{assigned_folder}' (order: {assignment_order})")
            return True
        else:
            print(f"❌ User '{username}' not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error updating user assignment: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def list_all_users():
    """List all users and their current assignments"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, email, name, assigned_folder, assignment_order, registered_at 
            FROM users 
            ORDER BY registered_at
        """)
        
        users = cursor.fetchall()
        print("\n📋 Current Users and Folder Assignments:")
        print("-" * 80)
        for user in users:
            username, email, name, folder, order, registered = user
            folder_info = f"Folder: {folder} (Order: {order})" if folder else "No folder assigned"
            print(f"👤 {name} ({username}) - {folder_info}")
        print("-" * 80)
        
        return users
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def auto_assign_folders():
    """Automatically assign folders 1-90 to existing users based on registration order"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        # Get users who don't have folder assignments, ordered by registration time
        cursor.execute("""
            SELECT username, registered_at 
            FROM users 
            WHERE assigned_folder IS NULL OR assigned_folder = ''
            ORDER BY registered_at
        """)
        
        unassigned_users = cursor.fetchall()
        
        if not unassigned_users:
            print("✅ All users already have folder assignments!")
            return
        
        print(f"🎯 Found {len(unassigned_users)} users without folder assignments")
        
        # Get the current highest assignment order to continue from there
        cursor.execute("""
            SELECT COALESCE(MAX(assignment_order), 0) 
            FROM users 
            WHERE assignment_order IS NOT NULL
        """)
        max_order = cursor.fetchone()[0]
        
        # Assign folders starting from the next order number
        for i, (username, registered_at) in enumerate(unassigned_users):
            assignment_order = max_order + i + 1
            folder_number = ((assignment_order - 1) % 90) + 1  # Folders 1-90, then cycle
            assigned_folder = str(folder_number)
            
            cursor.execute("""
                UPDATE users 
                SET assigned_folder = %s, assignment_order = %s 
                WHERE username = %s
            """, (assigned_folder, assignment_order, username))
            
            print(f"✅ Assigned user '{username}' to folder {assigned_folder} (order: {assignment_order})")
        
        conn.commit()
        print(f"\n� Successfully assigned folders to {len(unassigned_users)} users!")
        
    except Exception as e:
        print(f"❌ Error in auto-assignment: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    print("🔧 User Folder Assignment Manager")
    print("=" * 50)
    
    # List current users
    users = list_all_users()
    
    if not users:
        print("No users found in database.")
        return
    
    print(f"\nFound {len(users)} users in database.")
    
    # Auto-assign folders to users who don't have them
    print(f"\n🎯 Auto-assigning folders (1-90) based on registration order...")
    auto_assign_folders()
    
    print(f"\n📋 Updated user assignments:")
    list_all_users()

if __name__ == "__main__":
    main()