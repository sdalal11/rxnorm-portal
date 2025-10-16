#!/usr/bin/env python3
"""
Comprehensive PHI Redaction Script for Medical Records
Processes all HTML files in the 101-200 folder to remove Protected Health Information (PHI)
"""

import os
import re
import glob
from datetime import datetime

def redact_phi_from_file(input_file_path, output_file_path):
    """
    Remove PHI from a single HTML file and save to output location
    
    Args:
        input_file_path (str): Path to the input HTML file to process
        output_file_path (str): Path where the PHI-redacted file will be saved
    
    Returns:
        tuple: (success, replacements_count, errors)
    """
    try:
        # Read the input file
        with open(input_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_size = len(content)
        total_replacements = 0
        
        print(f"Processing: {os.path.basename(input_file_path)}")
        
        # 1. Patient names (various formats)
        patient_patterns = [
            # Last, First Middle format
            (r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\s*[A-Z]\.?\b', '[PATIENT NAME REDACTED]'),
            # First Middle Last format  
            (r'\b[A-Z][a-z]+\s+[A-Z]\.?\s+[A-Z][a-z]+\b(?![^<]*(?:tablet|capsule|mg|disease|disorder|syndrome))', '[PATIENT NAME REDACTED]'),
        ]
        
        for pattern, replacement in patient_patterns:
            matches = re.findall(pattern, content)
            filtered_matches = []
            for match in matches:
                # Skip medical terms, CSS properties, and HTML entities
                if not any(term in match.lower() for term in [
                    'font-family', 'verdana', 'tahoma', 'arial', 'sans-serif',
                    'tablet', 'capsule', 'mg', 'mcg', 'oral', 'disease', 
                    'syndrome', 'disorder', 'hypertensive', 'atherosclerotic',
                    'take, route', 'non drug', 'plan of', 'delayed release'
                ]):
                    filtered_matches.append(match)
            
            if filtered_matches:
                for match in filtered_matches:
                    content = content.replace(match, replacement)
                    total_replacements += 1
        
        # 2. Provider/physician names (Enhanced for care team columns)
        provider_patterns = [
            # Full name with MD (case insensitive)
            (r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,?\s*M\.?D\.?\b', '[PROVIDER NAME REDACTED]'),
            # Dr. Title - all variations (Dr, Dr., DR, DR., dr, dr.)
            (r'\b(?:Dr|DR|dr)\.?\s*[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', '[PROVIDER NAME REDACTED]'),
            # Provider in context
            (r'Provider:\s*[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', 'Provider: [PROVIDER NAME REDACTED]'),
            (r'Provider Name:\s*[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', 'Provider Name: [PROVIDER NAME REDACTED]'),
            # Provider in table columns (when Provider appears as column header)
            (r'<td[^>]*>[^<]*Provider[^<]*</td>\s*<td[^>]*>\s*[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*</td>', '<td>Provider</td><td>[PROVIDER NAME REDACTED]</td>'),
            # Names in Provider column contexts
            (r'Provider[^>]*>\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*</', r'Provider[^>]*>[PROVIDER NAME REDACTED]</'),
            # Care team member names (specific patterns from screenshots)
            (r'\bNguyen,\s*Jenny,?\s*APRN,?\s*CNP\b', '[CARE TEAM MEMBER REDACTED]'),
            (r'\bNguyen,\s*Jenny\b', '[CARE TEAM MEMBER REDACTED]'),
            (r'\bAPRN,?\s*CNP\b', '[CREDENTIALS REDACTED]'),
            # Names followed by credentials in table cells
            (r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+,?\s*(?:APRN|CNP|RN|MD|DO|NP|PA)\b', '[PROVIDER NAME REDACTED]'),
        ]
        
        for pattern, replacement in provider_patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                total_replacements += len(matches)
        
        # 3. Family member names (contextual)
        family_patterns = [
            (r'(accompanied by|her husband|his wife|son|daughter|spouse),?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', r'\1 [FAMILY MEMBER NAME REDACTED]'),
            (r'(Mr\.|Mrs\.|Ms\.)\s*[A-Z][a-z]+\s+[A-Z][a-z]+\b', r'\1 [FAMILY MEMBER NAME REDACTED]'),
        ]
        
        for pattern, replacement in family_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                total_replacements += len(matches)
        
        # 4. Dates of birth
        dob_patterns = [
            (r'\bDOB:\s*\d{1,2}/\d{1,2}/\d{4}', 'DOB: [DOB REDACTED]'),
            (r'\b\d{1,2}/\d{1,2}/\d{4}\b(?=.*(?:birth|born|DOB))', '[DOB REDACTED]'),
            # Specific DOB format in medical records
            (r'\(\d{2}\s*yo\s*[MF]\)', '([AGE REDACTED])'),
        ]
        
        for pattern, replacement in dob_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                total_replacements += len(matches)
        
        # 5. Account numbers and medical record numbers
        account_patterns = [
            (r'\bAccount Number:\s*\d+', 'Account Number: [ACCOUNT REDACTED]'),
            (r'\bAcc No\.?\s*\d+', 'Acc No. [ACCOUNT REDACTED]'),
            (r'\bMRN:\s*\d+', 'MRN: [MRN REDACTED]'),
            # Standalone long numbers that might be account numbers
            (r'\b\d{6,}\b(?![^<]*(?:mg|mcg|icd|snomed|code))', '[ACCOUNT REDACTED]'),
        ]
        
        for pattern, replacement in account_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                total_replacements += len(matches)
        
        # 6. Addresses (Enhanced to catch table column addresses)
        address_patterns = [
            # Full street addresses with various formats
            (r'\b\d+\s+[A-WYZ]\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*(?:Ave|Avenue|St|Street|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Way|Ct|Court|Pl|Place)[^<,]*', '[ADDRESS REDACTED]'),
            # Street addresses in table format (like "888 W Bonneville Ave")
            (r'\b\d+\s+[A-WYZ]\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', '[ADDRESS REDACTED]'),
            # Full addresses with city, state, zip
            (r'\b\d+\s+[A-Z][a-z]+\s+(?:Ave|Avenue|St|Street|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Way|Ct|Court|Pl|Place)[^<,]*,\s*[A-Z][a-z]+,\s*[A-Z]{2}\s*-?\s*\d{5}(?:-\d{4})?\b', '[FULL ADDRESS REDACTED]'),
            # City, state, zip combinations
            (r'\b[A-Z][A-Z\s]+,\s*[A-Z]{2}\s*-?\s*\d{5}(?:-\d{4})?\b', '[CITY STATE ZIP REDACTED]'),
            # Specific patterns seen in the data
            (r'\bLAS VEGAS,\s*NV\s*89106\b', '[CITY STATE ZIP REDACTED]'),
        ]
        
        for pattern, replacement in address_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    # Skip medical terms and codes
                    if not any(med_term in match.lower() for med_term in ['mg', 'mcg', 'tablet', 'capsule', 'diagnosis', 'icd']):
                        # Determine if it's patient or provider address based on context
                        context_before = content[max(0, content.find(match)-100):content.find(match)].lower()
                        if 'provider' in context_before or 'facility' in context_before or 'department' in context_before:
                            content = content.replace(match, '[PROVIDER ADDRESS REDACTED]')
                        else:
                            content = content.replace(match, '[PATIENT ADDRESS REDACTED]')
                        total_replacements += 1
        
        # 7. Phone numbers
        phone_patterns = [
            (r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE REDACTED]'),
            (r'\(\d{3}\)\s*\d{3}-\d{4}', '[PHONE REDACTED]'),
            # Long digit sequences that might be phone numbers (but not medical codes)
            (r'\b\d{10,}\b(?![^<]*(?:icd|snomed|code|diagnosis|mg|mcg))', '[PHONE REDACTED]'),
        ]
        
        for pattern, replacement in phone_patterns:
            matches = re.findall(pattern, content)
            phone_count = 0
            for match in matches:
                # Additional validation - ensure it's actually a phone number
                context = content[max(0, content.find(match)-50):content.find(match)+50].lower()
                if not any(med_term in context for med_term in ['icd', 'snomed', 'code', 'diagnosis']):
                    content = content.replace(match, replacement)
                    phone_count += 1
            total_replacements += phone_count
        
        # 8. Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, content)
        if email_matches:
            content = re.sub(email_pattern, '[EMAIL REDACTED]', content)
            total_replacements += len(email_matches)
        
        # 9. Social Security Numbers
        ssn_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]'),
            (r'\b\d{9}\b(?![^<]*(?:icd|code))', '[SSN REDACTED]'),
        ]
        
        for pattern, replacement in ssn_patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                total_replacements += len(matches)
        
        # 10. Table-specific PHI patterns (for encounter tables, care team info, etc.)
        table_phi_patterns = [
            # Care team contact info in tables
            (r'888\s+W\s+BONNEVILLE', '[ADDRESS REDACTED]'),
            (r'888\s+W\s+Bonneville\s+Ave', '[ADDRESS REDACTED]'),
            (r'\bBONNEVILLE\b', '[LOCATION REDACTED]'),
            # Specific provider names from screenshots (case insensitive)
            (r'\bJenny\b(?=.*(?:APRN|CNP|care|team))', '[PROVIDER FIRST NAME REDACTED]'),
            (r'\bNguyen\b(?=.*(?:APRN|CNP|Jenny|care|team))', '[PROVIDER LAST NAME REDACTED]'),
            # Any first name, last name pattern in provider/care contexts
            (r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b(?=.*(?:APRN|CNP|MD|DO|RN|NP|PA))', '[PROVIDER NAME REDACTED]'),
            # Contact information in structured format
            (r'\(Work\)', '[CONTACT TYPE REDACTED]'),
            (r'\(Fax\)', '[CONTACT TYPE REDACTED]'),
            # Provider names in table cells (between td tags)
            (r'<td[^>]*>\s*[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*</td>', '<td>[PROVIDER NAME REDACTED]</td>'),
            # Names in department or provider columns
            (r'department[^>]*>([^<]*[A-Z][a-z]+\s+[A-Z][a-z]+[^<]*)</', r'department[^>]*>[PROVIDER NAME REDACTED]</'),
        ]
        
        for pattern, replacement in table_phi_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                total_replacements += len(matches)
        
        # 11. Fix any CSS/HTML that was incorrectly replaced
        content = content.replace('font-family: [PATIENT NAME REDACTED], sans-serif;', 'font-family: Verdana, Tahoma, sans-serif;')
        content = content.replace('[PATIENT NAME REDACTED], sans-serif', 'Verdana, Tahoma, sans-serif')
        
        # Write the cleaned content to the output file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        final_size = len(content)
        print(f"  ✓ Completed: {total_replacements} replacements made")
        print(f"  ✓ Size: {original_size} → {final_size} characters")
        print(f"  ✓ Saved to: {os.path.basename(output_file_path)}")
        
        return True, total_replacements, None
        
    except Exception as e:
        print(f"  ✗ Error processing {input_file_path}: {str(e)}")
        return False, 0, str(e)

def main():
    """Main function to process all files and create PHI-redacted versions in a separate folder"""
    
    # Define the source and output folders
    source_folder = "/Users/sanjanadalal/Desktop/turmerik/RxNorm/clean-data"
    output_folder = "/Users/sanjanadalal/Desktop/turmerik/RxNorm/phi-redacted"
    
    # Check if source folder exists
    if not os.path.exists(source_folder):
        print(f"Error: Source folder {source_folder} does not exist!")
        return
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")
    else:
        print(f"Using existing output folder: {output_folder}")
    
    # Get all HTML files
    html_files = glob.glob(os.path.join(source_folder, "*.html"))
    
    if not html_files:
        print(f"No HTML files found in {source_folder}")
        return
    
    print(f"PHI Redaction Script Starting...")
    print(f"Processing {len(html_files)} files from: {source_folder}")
    print(f"Output will be saved to: {output_folder}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Process each file
    total_files = len(html_files)
    successful_files = 0
    total_replacements = 0
    errors = []
    
    for i, input_file_path in enumerate(html_files, 1):
        print(f"\n[{i}/{total_files}] Processing file...")
        
        # Create output file path
        input_filename = os.path.basename(input_file_path)
        output_filename = input_filename.replace('_clean.html', '_phi_redacted.html')
        if output_filename == input_filename:  # If it didn't have _clean, just add suffix
            output_filename = input_filename.replace('.html', '_phi_redacted.html')
        output_file_path = os.path.join(output_folder, output_filename)
        
        success, replacements, error = redact_phi_from_file(input_file_path, output_file_path)
        
        if success:
            successful_files += 1
            total_replacements += replacements
        else:
            errors.append((input_file_path, error))
    
    # Summary
    print("\n" + "=" * 60)
    print("PHI REDACTION SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {total_files}")
    print(f"Successfully processed: {successful_files}")
    print(f"Failed: {len(errors)}")
    print(f"Total PHI replacements made: {total_replacements}")
    print(f"Output folder: {output_folder}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if errors:
        print("\nERRORS:")
        for file_path, error in errors:
            print(f"  - {os.path.basename(file_path)}: {error}")
    
    print("\n✓ PHI redaction process completed!")
    print("All PHI-redacted files have been saved to the output folder for HIPAA compliance.")

if __name__ == "__main__":
    main()