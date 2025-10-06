import pandas as pd
import json
import os
import glob
from typing import List, Dict

def consolidate_json_to_excel(json_folder: str, output_excel: str):
    """Consolidate all medication JSON files into a single Excel file"""
    
    # Find all JSON files in the folder
    json_files = glob.glob(os.path.join(json_folder, "*.json"))
    
    if not json_files:
        print(f"No JSON files found in {json_folder}")
        return
    
    print(f"Found {len(json_files)} JSON files to process...")
    
    # List to store all medication records
    all_medications = []
    
    # Process each JSON file
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract file information
            source_file = data.get('file', os.path.basename(json_file))
            medications = data.get('medications', [])
            
            # Process each medication in the file
            for med in medications:
                medication_record = {
                    'source_file': source_file,
                    'rx_cui': med.get('rx_cui', ''),
                    'normalized_name': med.get('normalized_name', ''),
                    'text': med.get('text', ''),
                    'active_status': med.get('active_status', ''),
                    'confidence': med.get('confidence', ''),
                    'mapping_method': med.get('mapping_method', ''),
                    'mapping_confidence': med.get('mapping_confidence', ''),
                    'cui_type': med.get('cui_type', ''),
                    'start_offset': med.get('start_offset', ''),
                    'end_offset': med.get('end_offset', ''),
                    'flag': med.get('flag', '')
                }
                all_medications.append(medication_record)
            
            print(f"✅ Processed: {os.path.basename(json_file)} ({len(medications)} medications)")
            
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    if not all_medications:
        print("No medications found to consolidate")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_medications)
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        
        # Sheet 1: Requested fields only (rx_cui, normalized_name, text, active_status)
        requested_fields = df[['source_file', 'rx_cui', 'normalized_name', 'text', 'active_status']].copy()
        requested_fields.to_excel(writer, sheet_name='Medications_Summary', index=False)
        

    print(f"\n🎉 Consolidation complete!")
    print(f"💾 Excel file saved: {output_excel}")
    

def create_filtered_excel(json_folder: str, output_excel: str, fields_only: bool = False):
    """Create Excel with only the requested fields"""
    
    json_files = glob.glob(os.path.join(json_folder, "*.json"))
    all_medications = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            medications = data.get('medications', [])
            source_file = data.get('file', os.path.basename(json_file))
            
            for med in medications:
                if fields_only:
                    # Only requested fields
                    record = {
                        'source_file': source_file,
                        'rx_cui': med.get('rx_cui', ''),
                        'normalized_name': med.get('normalized_name', ''),
                        'text': med.get('text', ''),
                        'active_status': med.get('active_status', '')
                    }
                else:
                    # All fields
                    record = {
                        'source_file': source_file,
                        'rx_cui': med.get('rx_cui', ''),
                        'normalized_name': med.get('normalized_name', ''),
                        'text': med.get('text', ''),
                        'active_status': med.get('active_status', ''),
                        'confidence': med.get('confidence', ''),
                        'mapping_method': med.get('mapping_method', ''),
                        'mapping_confidence': med.get('mapping_confidence', ''),
                        'cui_type': med.get('cui_type', ''),
                        'start_offset': med.get('start_offset', ''),
                        'end_offset': med.get('end_offset', '')
                    }
                all_medications.append(record)
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Create DataFrame and save
    df = pd.DataFrame(all_medications)
    df.to_excel(output_excel, index=False)
    
    print(f"✅ Excel file created: {output_excel}")
    print(f"📊 Total records: {len(df)}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Consolidate medication JSON files to Excel')
    parser.add_argument('--input', '-i', default='labelled-json-batch2', help='Input folder with JSON files')
    parser.add_argument('--output', '-o', default='consolidated_medications.xlsx', help='Output Excel file')
    parser.add_argument('--fields-only', action='store_true', help='Include only rx_cui, normalized_name, text, active_status')
    
    args = parser.parse_args()
    
    if args.fields_only:
        create_filtered_excel(args.input, args.output, fields_only=True)
    else:
        consolidate_json_to_excel(args.input, args.output)

if __name__ == "__main__":
    # Quick run for your specific case
    json_folder = "labelled-json-batch2"
    output_file = "batch2_medications_consolidated.xlsx"
    
    print("Consolidating JSON files from batch2...")
    consolidate_json_to_excel(json_folder, output_file)
    
    # Also create a simple version with only requested fields
    simple_output = "batch2_medications_simple.xlsx"
    create_filtered_excel(json_folder, simple_output, fields_only=True)
    
    print(f"\n📁 Files created:")
    print(f"   • Full details: {output_file}")
    print(f"   • Simple version: {simple_output}")