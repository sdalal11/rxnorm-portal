import pandas as pd
import requests
import os
import glob
from html_to_excel import HTMLToExcelConverter

def download_from_google_drive(file_id, destination):
    """Download file from Google Drive using file ID"""
    URL = "https://drive.google.com/drive/folders/1shL_iHvPBcw9F9rtKmiAg_by95ydIw0n?usp=drive_link"
    
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break
    
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    
    return destination

# Example usage:
# file_id = "your_google_drive_file_id"
# download_from_google_drive(file_id, "downloaded_file.html")