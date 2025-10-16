# Azure Blob Storage Downloader - General Folder

This script downloads all files from the "general" folder in your Azure Blob Storage container.

## Files Created

1. **`download_general_folder.py`** - Main download script
2. **`azure_config.json`** - Configuration file (needs to be edited with your credentials)
3. **`extract_config_helper.py`** - Helper to extract config from browser localStorage

## Setup Instructions

### Option 1: Extract from Browser (Recommended if you have admin panel configured)

1. Open your admin panel in a web browser
2. Open Developer Tools (F12)
3. Go to Console tab
4. Run this command:

```javascript
console.log(JSON.stringify({
  storageAccount: JSON.parse(localStorage.getItem('azureConfigPublic') || localStorage.getItem('globalAzureConfig') || '{}').storageAccount,
  containerName: JSON.parse(localStorage.getItem('azureConfigPublic') || localStorage.getItem('globalAzureConfig') || '{}').containerName,
  sasToken: JSON.parse(localStorage.getItem('azureConfigPublic') || localStorage.getItem('globalAzureConfig') || '{}').sasToken
}, null, 2));
```

5. Copy the output and replace the contents of `azure_config.json`

### Option 2: Manual Configuration

Edit `azure_config.json` and replace:

```json
{
    "storageAccount": "your-actual-storage-account-name",
    "containerName": "documents",
    "sasToken": "?sv=2021-06-08&ss=b&srt=sco&sp=rwdlacup&your-actual-token"
}
```

## Usage

Once configured, run:

```bash
python3 download_general_folder.py
```

The script will:
1. List all files in the "general/" folder
2. Create a `downloaded_general_folder` directory
3. Download all files maintaining the folder structure
4. Show progress and summary

## Features

- ✅ Downloads all files from the "general" folder
- ✅ Creates local directory structure
- ✅ Progress tracking with file sizes
- ✅ Error handling and retry logic
- ✅ Detailed logging and summary
- ✅ Handles large files efficiently
- ✅ Cross-platform compatibility (Windows, Mac, Linux)

## Requirements

- Python 3.6 or higher
- Internet connection
- Valid Azure Storage Account with SAS token permissions:
  - Read (r) permission
  - List (l) permission

## Output

Downloads will be saved to: `downloaded_general_folder/`

Example output structure:
```
downloaded_general_folder/
├── file1.html
├── file2.html
├── subfolder/
│   ├── file3.html
│   └── file4.html
└── ...
```

## Troubleshooting

### Error: "No Azure configuration file found"
- Make sure `azure_config.json` exists and is properly formatted
- Check that all required fields are filled in

### Error: "Failed to list blobs: HTTP 403"
- Check that your SAS token has list and read permissions
- Verify the storage account name is correct
- Make sure the SAS token hasn't expired

### Error: "No files found in general folder"
- Verify that files exist in the "general/" folder in your container
- Check that the container name is correct
- Ensure the folder path is "general/" (case-sensitive)

## Security Note

The `azure_config.json` file contains sensitive credentials. Make sure to:
- Never commit this file to version control
- Keep it secure and private
- Regenerate SAS tokens periodically