#!/usr/bin/env python3
"""
Script to reorganize data_900 files into folders of 10 files each.
Takes files from 9 folders of 100 files each and reorganizes into 90 folders of 10 files each.

Usage:
    python3 organize_data_900.py

This script will:
1. Collect all HTML files from data_900 subfolders
2. Create new numbered folders (1, 2, 3, ... 90)
3. Move 10 files into each folder sequentially
4. Create an organized_data_900 output directory
"""

import os
import shutil
import glob
from pathlib import Path

def organize_data_900_files():
    """Reorganize data_900 files into folders of 10 files each"""
    
    # Configuration
    source_folder = "data_900"
    output_folder = "organized_data_900"
    files_per_folder = 10
    
    # Check if source folder exists
    if not os.path.exists(source_folder):
        print(f"❌ Source folder '{source_folder}' not found!")
        return False
    
    # Get all HTML files from all subfolders
    html_files = []
    subfolders = [f for f in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, f))]
    subfolders.sort()  # Sort to ensure consistent order
    
    print(f"📂 Found subfolders: {subfolders}")
    
    for subfolder in subfolders:
        subfolder_path = os.path.join(source_folder, subfolder)
        files_in_subfolder = glob.glob(os.path.join(subfolder_path, "*.html"))
        files_in_subfolder.sort()  # Sort for consistent ordering
        html_files.extend(files_in_subfolder)
        print(f"  📁 {subfolder}: {len(files_in_subfolder)} files")
    
    print(f"\n📊 Total: {len(html_files)} HTML files found")
    
    if len(html_files) == 0:
        print("❌ No HTML files found to organize!")
        return False
    
    # Create output directory
    if os.path.exists(output_folder):
        print(f"⚠️  Output folder '{output_folder}' already exists. Files may be overwritten.")
    else:
        os.makedirs(output_folder)
        print(f"📁 Created output folder: {output_folder}")
    
    # Calculate number of folders needed
    num_folders = (len(html_files) + files_per_folder - 1) // files_per_folder
    print(f"📁 Will create {num_folders} folders with {files_per_folder} files each")
    
    # Create folders and move files
    folder_names = []
    moved_count = 0
    
    for folder_num in range(1, num_folders + 1):
        # Create folder name
        folder_name = str(folder_num)
        folder_path = os.path.join(output_folder, folder_name)
        folder_names.append(folder_name)
        
        # Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Calculate file range for this folder
        start_idx = (folder_num - 1) * files_per_folder
        end_idx = min(start_idx + files_per_folder, len(html_files))
        
        files_for_folder = html_files[start_idx:end_idx]
        
        print(f"📦 Folder {folder_num}: Moving {len(files_for_folder)} files")
        
        # Copy files to the folder (using copy instead of move to preserve originals)
        for file_path in files_for_folder:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(folder_path, file_name)
            
            # Copy file to new location
            if not os.path.exists(dest_path):
                shutil.copy2(file_path, dest_path)
                moved_count += 1
                print(f"  ✅ Copied: {file_name}")
            else:
                print(f"  ℹ️  Already exists: {file_name}")
    
    print(f"\n🎉 Successfully organized {moved_count} files into {num_folders} folders!")
    print(f"📂 Output directory: {output_folder}")
    
    # Display summary
    print("\n📋 Folder Summary:")
    total_organized = 0
    for i, folder_name in enumerate(folder_names, 1):
        folder_path = os.path.join(output_folder, folder_name)
        file_count = len(glob.glob(os.path.join(folder_path, "*.html")))
        total_organized += file_count
        print(f"  Folder {folder_name}: {file_count} files")
    
    print(f"\n📊 Total files organized: {total_organized}")
    
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

def main():
    print("🚀 Data_900 File Organizer")
    print("=" * 50)
    print("This script will reorganize your data_900 files:")
    print("• From: 9 folders of ~100 files each")
    print("• To: 90 folders of 10 files each")
    print("• Output: organized_data_900 directory")
    print("=" * 50)
    
    success = organize_data_900_files()
    
    if success:
        print("\n✅ Organization completed successfully!")
        print("\nNext steps:")
        print("1. Review the organized_data_900 folder")
        print("2. Update api_server.py with the new AVAILABLE_FOLDERS array shown above")
        print("3. Test the folder assignment system with the new structure")
    else:
        print("\n❌ Organization failed!")

if __name__ == "__main__":
    main()