# import json
# import csv
# import glob
# import os
# import re

# input_folder = "labelled-json-batch2"  # Folder with your JSON files
# output_csv = "labelled-sheet-batch2.csv"

# # Collect all JSON files
# json_files = glob.glob(os.path.join(input_folder, "*.json"))

# all_rows = []
# for file in json_files:
#     with open(file, "r") as f:
#         data = json.load(f)
#         for med in data.get("medications", []):
#             row = {
#                 "file": data.get("file"),
#                 "text": med.get("text"),
#                 "rx_cui": med.get("rx_cui"),
#                 "normalized_name": med.get("normalized_name"),
#                 "active_status": med.get("active_status"),  
#             }
#             all_rows.append(row)

# # Sort by file name (encounter1, encounter2, etc.)
# def extract_encounter_number(filename):
#     """Extract number from encounter filename for proper sorting"""
#     match = re.search(r'encounter(\d+)', filename.lower())
#     return int(match.group(1)) if match else 0

# all_rows.sort(key=lambda x: extract_encounter_number(x["file"]))

# # Write to CSV
# if all_rows:
#     with open(output_csv, "w", newline="") as f:
#         writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
#         writer.writeheader()
#         writer.writerows(all_rows)
#     print(f"✅ Converted {len(json_files)} files into {output_csv} (sorted by encounter number)")
# else:
#     print("No medication data found in JSON files.")


import json
import pandas as pd
import glob
import os
import re

input_folder = "labelled-json-batch2"  # Folder with your JSON files
output_excel = "labelled-sheet-batch2.xlsx"  # Single Excel file with multiple tabs

# Collect all JSON files
json_files = glob.glob(os.path.join(input_folder, "*.json"))

# Sort JSON files by name for consistent tab ordering
json_files.sort()

# Create Excel file with multiple tabs (one per JSON file)
if json_files:
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        
        total_medications = 0
        tab_count = 0
        
        for file in json_files:
            with open(file, "r") as f:
                data = json.load(f)
                
                # Extract medications for this specific file
                file_rows = []
                for med in data.get("medications", []):
                    row = {
                        "file": data.get("file"),
                        "text": med.get("text"),
                        "rx_cui": med.get("rx_cui"),
                        "normalized_name": med.get("normalized_name"),
                        "active_status": med.get("active_status"),  
                    }
                    file_rows.append(row)
                
                # Create DataFrame for this specific file (even if empty)
                if file_rows:
                    file_df = pd.DataFrame(file_rows)
                else:
                    # Create empty DataFrame with column headers
                    file_df = pd.DataFrame(columns=["file", "text", "rx_cui", "normalized_name", "active_status"])
                
                # Use actual filename as sheet name (without .json extension)
                sheet_name = os.path.basename(file).replace('.json', '').replace('_medications', '')
                
                # Excel sheet names have a 31 character limit, so truncate if necessary
                if len(sheet_name) > 31:
                    sheet_name = sheet_name[:31]
                
                # Replace any invalid characters for Excel sheet names
                invalid_chars = ['[', ']', ':', '*', '?', '/', '\\']
                for char in invalid_chars:
                    sheet_name = sheet_name.replace(char, '_')
                
                # Write this file's medications to its own tab (even if empty)
                file_df.to_excel(writer, sheet_name=sheet_name, index=False)
                total_medications += len(file_rows)
                tab_count += 1
                
                if file_rows:
                    print(f"✅ Tab {tab_count}: '{sheet_name}' - {len(file_rows)} medications")
                else:
                    print(f"📝 Tab {tab_count}: '{sheet_name}' - BLANK (no medications found)")
    
    print(f"\n🎉 Excel file created: {output_excel}")
    print(f"📊 Total tabs created: {tab_count}")
    print(f"💊 Total medications across all tabs: {total_medications}")
    print(f"\n📋 Each tab represents one JSON file (blank tabs for files with no medications)")
    
else:
    print("No JSON files found in the folder.")