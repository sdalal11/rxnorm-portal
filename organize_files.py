#!/usr/bin/env python3
"""
Script to organize redacted files into folders of 10 files each.
Creates folders numbered 1, 2, 3, ... with 10 files in each folder.

Usage:
    python3 organize_files.py

This script will:
1. Count all HTML files in the "redacted files" folder
2. Create new numbered folders (1, 2, 3, ...)
3. Move 10 files into each folder sequentially
4. Update the AVAILABLE_FOLDERS array in api_server.py
"""

import os
import shutil
import glob
from pathlib import Path

def organize_redacted_files():
    """Organize redacted files into folders of 10 files each"""
    
    # Configuration
    source_folder = "redacted files"
    files_per_folder = 10
    
    # Check if source folder exists
    if not os.path.exists(source_folder):
        print(f"❌ Source folder '{source_folder}' not found!")
        return False
    
    # Get all HTML files from the source folder
    html_files = glob.glob(os.path.join(source_folder, "*.html"))
    html_files.sort()  # Sort for consistent ordering
    
    print(f"📊 Found {len(html_files)} HTML files in '{source_folder}'")
    
    if len(html_files) == 0:
        print("❌ No HTML files found to organize!")
        return False
    
    # Calculate number of folders needed
    num_folders = (len(html_files) + files_per_folder - 1) // files_per_folder
    print(f"📁 Will create {num_folders} folders with {files_per_folder} files each")
    
    # Create folders and move files
    folder_names = []
    
    for folder_num in range(1, num_folders + 1):
        # Create folder name
        folder_name = str(folder_num)
        folder_path = os.path.join(source_folder, folder_name)
        folder_names.append(folder_name)
        
        # Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"📁 Created folder: {folder_path}")
        
        # Calculate file range for this folder
        start_idx = (folder_num - 1) * files_per_folder
        end_idx = min(start_idx + files_per_folder, len(html_files))
        
        files_for_folder = html_files[start_idx:end_idx]
        
        print(f"📦 Folder {folder_num}: Moving {len(files_for_folder)} files")
        
        # Move files to the folder
        for file_path in files_for_folder:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(folder_path, file_name)
            
            # Only move if file is not already in the target folder
            if not os.path.exists(dest_path):
                shutil.move(file_path, dest_path)
                print(f"  ✅ Moved: {file_name}")
            else:
                print(f"  ℹ️  Already exists: {file_name}")
    
    print(f"\n🎉 Successfully organized {len(html_files)} files into {num_folders} folders!")
    
    # Display summary
    print("\n📋 Folder Summary:")
    for i, folder_name in enumerate(folder_names, 1):
        folder_path = os.path.join(source_folder, folder_name)
        file_count = len(glob.glob(os.path.join(folder_path, "*.html")))
        print(f"  Folder {folder_name}: {file_count} files")
    
    # Generate the new AVAILABLE_FOLDERS array for api_server.py
    print(f"\n🔧 New AVAILABLE_FOLDERS array for api_server.py:")
    print("AVAILABLE_FOLDERS = [")
    for i, folder_name in enumerate(folder_names):
        if i == len(folder_names) - 1:  # Last item, no comma
            print(f'    "{folder_name}"')
        else:
            print(f'    "{folder_name}",')
    print("]")
    
    return True

def update_api_server_folders(folder_names):
    """Update the AVAILABLE_FOLDERS array in api_server.py"""
    
    api_server_file = "api_server.py"
    
    if not os.path.exists(api_server_file):
        print(f"❌ {api_server_file} not found!")
        return False
    
    try:
        # Read the current file
        with open(api_server_file, 'r') as f:
            content = f.read()
        
        # Create the new AVAILABLE_FOLDERS array
        new_folders_array = "AVAILABLE_FOLDERS = [\n"
        for i, folder_name in enumerate(folder_names):
            if i == len(folder_names) - 1:  # Last item, no comma
                new_folders_array += f'    "{folder_name}"\n'
            else:
                new_folders_array += f'    "{folder_name}",\n'
        new_folders_array += "]"
        
        # Find and replace the AVAILABLE_FOLDERS array
        import re
        pattern = r'AVAILABLE_FOLDERS\s*=\s*\[.*?\]'
        
        if re.search(pattern, content, re.DOTALL):
            updated_content = re.sub(pattern, new_folders_array, content, flags=re.DOTALL)
            
            # Write the updated content
            with open(api_server_file, 'w') as f:
                f.write(updated_content)
            
            print(f"✅ Updated AVAILABLE_FOLDERS in {api_server_file}")
            return True
        else:
            print(f"❌ Could not find AVAILABLE_FOLDERS array in {api_server_file}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {api_server_file}: {e}")
        return False

def main():
    """Main function to organize files and update configuration"""
    
    print("🚀 RxNorm File Organization Script")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("This will reorganize files in 'redacted files' folder. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled")
        return
    
    # Organize the files
    success = organize_redacted_files()
    
    if success:
        # Get the folder names for updating api_server.py
        source_folder = "redacted files"
        folders = []
        for item in os.listdir(source_folder):
            item_path = os.path.join(source_folder, item)
            if os.path.isdir(item_path) and item.isdigit():
                folders.append(item)
        
        folders.sort(key=int)  # Sort numerically
        
        # Ask if user wants to update api_server.py
        if folders:
            response = input(f"\nUpdate AVAILABLE_FOLDERS in api_server.py with {len(folders)} new folders? (y/N): ")
            if response.lower() == 'y':
                update_api_server_folders(folders)
        
        print("\n🎉 File organization completed!")
        print(f"📊 Created {len(folders)} folders with 10 files each")
        print(f"👥 This will support {len(folders)} different users with folder assignments!")
        
    else:
        print("❌ File organization failed!")

if __name__ == "__main__":
    main()