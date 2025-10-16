#!/usr/bin/env python3
"""
Azure Blob Storage Downloader - General Folder
Downloads all files from the 'general' folder in the rx-norm container
"""

import os
import sys
import json
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request
import xml.etree.ElementTree as ET
from datetime import datetime

def load_azure_config():
    """Load Azure configuration from various possible sources"""
    config_files = [
        'azure_config.json',
        'config.json',
        '.azure_config.json'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    print(f"✅ Loaded Azure config from {config_file}")
                    return config
            except Exception as e:
                print(f"⚠️ Failed to load {config_file}: {e}")
                continue
    
    # If no config file found, prompt user for manual input
    print("❌ No Azure configuration file found.")
    print("Please provide the following information:")
    
    storage_account = input("Storage Account Name (e.g., rxnormstorage): ").strip()
    container_name = input("Container Name (e.g., documents): ").strip()
    sas_token = input("SAS Token (including the ? if present): ").strip()
    
    return {
        "storageAccount": storage_account,
        "containerName": container_name,
        "sasToken": sas_token
    }

def clean_sas_token(sas_token):
    """Clean and prepare SAS token"""
    if sas_token.startswith('?'):
        return sas_token[1:]
    return sas_token

def list_blobs_in_folder(storage_account, container_name, sas_token, folder_prefix="general/"):
    """List all blobs in the specified folder"""
    # Clean SAS token
    clean_token = clean_sas_token(sas_token)
    
    # Construct list URL
    list_url = f"https://{storage_account}.blob.core.windows.net/{container_name}?restype=container&comp=list&prefix={folder_prefix}&{clean_token}"
    
    print(f"🔍 Listing blobs from: {storage_account}/{container_name}/{folder_prefix}")
    
    try:
        request = Request(list_url)
        response = urlopen(request)
        
        if response.status != 200:
            raise Exception(f"Failed to list blobs: HTTP {response.status}")
        
        xml_data = response.read().decode('utf-8')
        
        # Parse XML response
        root = ET.fromstring(xml_data)
        blobs = []
        
        # Find all blob elements
        for blob in root.iter('Blob'):
            name_elem = blob.find('Name')
            size_elem = blob.find('Properties/Content-Length')
            modified_elem = blob.find('Properties/Last-Modified')
            
            if name_elem is not None:
                blob_info = {
                    'name': name_elem.text,
                    'size': int(size_elem.text) if size_elem is not None else 0,
                    'last_modified': modified_elem.text if modified_elem is not None else None
                }
                blobs.append(blob_info)
        
        print(f"✅ Found {len(blobs)} files in {folder_prefix} folder")
        return blobs
        
    except Exception as e:
        print(f"❌ Error listing blobs: {e}")
        return []

def download_file(storage_account, container_name, sas_token, blob_name, local_path):
    """Download a single file from Azure Blob Storage"""
    # Clean SAS token
    clean_token = clean_sas_token(sas_token)
    
    # Construct download URL
    download_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{blob_name}?{clean_token}"
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Download file
        request = Request(download_url)
        response = urlopen(request)
        
        if response.status != 200:
            raise Exception(f"Failed to download: HTTP {response.status}")
        
        # Write file to disk
        with open(local_path, 'wb') as f:
            f.write(response.read())
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading {blob_name}: {e}")
        return False

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def main():
    print("🚀 Azure Blob Storage Downloader - General Folder")
    print("=" * 50)
    
    # Load configuration
    config = load_azure_config()
    
    if not all(key in config for key in ['storageAccount', 'containerName', 'sasToken']):
        print("❌ Missing required configuration keys. Need: storageAccount, containerName, sasToken")
        sys.exit(1)
    
    storage_account = config['storageAccount']
    container_name = config['containerName']
    sas_token = config['sasToken']
    
    print(f"📋 Configuration:")
    print(f"   Storage Account: {storage_account}")
    print(f"   Container: {container_name}")
    print(f"   SAS Token: {'*' * 20}...{sas_token[-10:] if len(sas_token) > 10 else '*' * len(sas_token)}")
    print()
    
    # List all files in general folder
    blobs = list_blobs_in_folder(storage_account, container_name, sas_token, "general/")
    
    if not blobs:
        print("❌ No files found in general folder")
        sys.exit(1)
    
    # Create download directory
    download_dir = "downloaded_general_folder"
    os.makedirs(download_dir, exist_ok=True)
    print(f"📁 Download directory: {download_dir}")
    print()
    
    # Download files
    successful_downloads = 0
    total_size = 0
    
    print("📥 Starting downloads...")
    print("-" * 50)
    
    for i, blob in enumerate(blobs, 1):
        blob_name = blob['name']
        file_size = blob['size']
        
        # Create local file path (remove 'general/' prefix for local storage)
        local_filename = blob_name.replace('general/', '', 1)
        local_path = os.path.join(download_dir, local_filename)
        
        print(f"[{i:3d}/{len(blobs)}] {local_filename} ({format_file_size(file_size)})")
        
        if download_file(storage_account, container_name, sas_token, blob_name, local_path):
            successful_downloads += 1
            total_size += file_size
            print(f"           ✅ Downloaded to: {local_path}")
        else:
            print(f"           ❌ Download failed")
        
        print()
    
    # Summary
    print("=" * 50)
    print("📊 Download Summary:")
    print(f"   Total files found: {len(blobs)}")
    print(f"   Successfully downloaded: {successful_downloads}")
    print(f"   Failed downloads: {len(blobs) - successful_downloads}")
    print(f"   Total size downloaded: {format_file_size(total_size)}")
    print(f"   Download directory: {os.path.abspath(download_dir)}")
    
    if successful_downloads == len(blobs):
        print("🎉 All files downloaded successfully!")
    elif successful_downloads > 0:
        print("⚠️ Some files downloaded with errors")
    else:
        print("❌ No files were downloaded")

if __name__ == "__main__":
    main()
