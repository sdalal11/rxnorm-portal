#!/usr/bin/env python3
"""
Helper script to extract Azure configuration from browser localStorage
Run this after running the main download script to see what config is saved
"""

print("""
🔧 Azure Configuration Helper

If you have already configured Azure settings in your admin panel, 
you can extract them by following these steps:

1. Open your admin panel in a web browser
2. Open Developer Tools (F12)
3. Go to Console tab
4. Run this JavaScript command:

   console.log(JSON.stringify({
     storageAccount: JSON.parse(localStorage.getItem('azureConfigPublic') || localStorage.getItem('globalAzureConfig') || '{}').storageAccount,
     containerName: JSON.parse(localStorage.getItem('azureConfigPublic') || localStorage.getItem('globalAzureConfig') || '{}').containerName,
     sasToken: JSON.parse(localStorage.getItem('azureConfigPublic') || localStorage.getItem('globalAzureConfig') || '{}').sasToken
   }, null, 2));

5. Copy the output and paste it into azure_config.json
6. Run: python download_general_folder.py

Alternatively, you can manually edit azure_config.json with your:
- Storage Account Name (e.g., rxnormstorage)
- Container Name (usually 'documents')  
- SAS Token (starts with ?sv=...)
""")