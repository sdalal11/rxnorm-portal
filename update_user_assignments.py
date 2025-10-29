#!/usr/bin/env python3
"""
Script to assign folders to existing users who don't have folder assignments.
Assigns folders based on registration order (registered_at timestamp).
"""

import psycopg2
import os
from datetime import datetime

# Use the direct connection string
DATABASE_URL = "postgresql://postgres:Sanjana123!@db.ynbsbpmyzubwkmfgdzes.supabase.co:5432/postgres"

def update_user_assignments():
    """Update existing users with folder assignments based on registration order"""
    try:
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        # Get all users ordered by registration timestamp (oldest first)
        cursor.execute('''
            SELECT id, username, email, name, registered_at, assigned_folder, assignment_order
            FROM users 
            ORDER BY registered_at ASC
        ''')
        
        users = cursor.fetchall()
        print(f"📊 Found {len(users)} users in database")
        
        updated_count = 0
        
        for index, user in enumerate(users):
            user_id, username, email, name, registered_at, assigned_folder, assignment_order = user
            
            # Skip users who already have assignments
            if assigned_folder and assignment_order:
                print(f"✅ User {username} already assigned to folder {assigned_folder} (order: {assignment_order})")
                continue
            
            # Calculate assignment based on registration order (folders 1-90, then cycle back)
            new_assignment_order = index + 1  # 1-based
            folder_number = ((index) % 90) + 1  # Folders 1-90, then cycle back to 1
            new_assigned_folder = str(folder_number)
            
            # Update the user
            cursor.execute('''
                UPDATE users 
                SET assigned_folder = %s, assignment_order = %s 
                WHERE id = %s
            ''', (new_assigned_folder, new_assignment_order, user_id))
            
            print(f"📁 Updated {username} -> Folder: {new_assigned_folder}, Order: {new_assignment_order}")
            updated_count += 1
        
        # Commit all changes
        conn.commit()
        print(f"\n✅ Successfully updated {updated_count} users with folder assignments!")
        
        # Show final assignment summary
        cursor.execute('''
            SELECT assigned_folder, COUNT(*) as user_count 
            FROM users 
            WHERE assigned_folder IS NOT NULL
            GROUP BY assigned_folder 
            ORDER BY assigned_folder
        ''')
        
        folder_summary = cursor.fetchall()
        print(f"\n📈 Folder Assignment Summary:")
        for folder, count in folder_summary:
            print(f"   {folder}: {count} users")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error updating user assignments: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 RxNorm User Folder Assignment Updater")
    print("=" * 60)
    update_user_assignments()
    print("=" * 60)
    print("🎉 Assignment update completed!")