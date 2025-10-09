#!/usr/bin/env python3
"""
Simplified Google Cloud DLP PHI redaction script
Uses only built-in info types for reliability
"""

import os
import argparse
from datetime import datetime
from google.cloud import dlp_v2

class SimpleDLPRedactor:
    """Simplified DLP redactor using only built-in info types"""
    
    def __init__(self, project_id):
        """Initialize the DLP client"""
        self.project_id = project_id
        self.client = dlp_v2.DlpServiceClient()
        self.parent = f"projects/{project_id}"
        
        # Healthcare-focused built-in info types including addresses
        self.phi_info_types = [
            dlp_v2.InfoType(name="PERSON_NAME"),
            dlp_v2.InfoType(name="PHONE_NUMBER"),
            dlp_v2.InfoType(name="EMAIL_ADDRESS"),
            dlp_v2.InfoType(name="US_SOCIAL_SECURITY_NUMBER"),
            dlp_v2.InfoType(name="DATE_OF_BIRTH"),
            dlp_v2.InfoType(name="US_HEALTHCARE_NPI"),
            dlp_v2.InfoType(name="DATE"),
            dlp_v2.InfoType(name="US_DRIVERS_LICENSE_NUMBER"),
            dlp_v2.InfoType(name="CREDIT_CARD_NUMBER"),
            dlp_v2.InfoType(name="US_BANK_ROUTING_MICR"),
            dlp_v2.InfoType(name="US_DEA_NUMBER"),
            # Address and location types
            dlp_v2.InfoType(name="LOCATION"),
            dlp_v2.InfoType(name="STREET_ADDRESS"),
            dlp_v2.InfoType(name="US_STATE"),
            dlp_v2.InfoType(name="US_TOLLFREE_PHONE_NUMBER"),
            # Additional healthcare identifiers
            dlp_v2.InfoType(name="MEDICAL_RECORD_NUMBER"),
            dlp_v2.InfoType(name="US_PASSPORT"),
            dlp_v2.InfoType(name="AGE"),
        ]
    
    def create_inspect_config(self):
        """Create inspection configuration"""
        return dlp_v2.InspectConfig(
            info_types=self.phi_info_types,
            min_likelihood=dlp_v2.Likelihood.POSSIBLE,
            include_quote=True,
            limits=dlp_v2.InspectConfig.FindingLimits(
                max_findings_per_request=0  # No limit
            )
        )
    
    def create_deidentify_config(self):
        """Create de-identification configuration"""
        return dlp_v2.DeidentifyConfig(
            info_type_transformations=dlp_v2.InfoTypeTransformations(
                transformations=[
                    dlp_v2.InfoTypeTransformations.InfoTypeTransformation(
                        info_types=self.phi_info_types,
                        primitive_transformation=dlp_v2.PrimitiveTransformation(
                            replace_config=dlp_v2.ReplaceValueConfig(
                                new_value=dlp_v2.Value(string_value="[REDACTED]")
                            )
                        )
                    )
                ]
            )
        )
    
    def redact_html_content(self, html_content):
        """Redact PHI from HTML content"""
        inspect_config = self.create_inspect_config()
        deidentify_config = self.create_deidentify_config()
        
        item = dlp_v2.ContentItem(value=html_content)
        
        request = dlp_v2.DeidentifyContentRequest(
            parent=self.parent,
            deidentify_config=deidentify_config,
            inspect_config=inspect_config,
            item=item
        )
        
        response = self.client.deidentify_content(request=request)
        
        # Count findings
        redaction_count = len(response.overview.transformation_summaries[0].results) if response.overview.transformation_summaries else 0
        
        return response.item.value, redaction_count
    
    def process_file(self, input_path, output_path):
        """Process a single HTML file"""
        try:
            # Read input file
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Redact PHI
            redacted_content, redaction_count = self.redact_html_content(html_content)
            
            # Write output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(redacted_content)
            
            return redaction_count, None
            
        except Exception as e:
            return 0, str(e)
    
    def process_folder(self, input_folder, output_folder):
        """Process all HTML files in a folder"""
        print("🔒 GOOGLE CLOUD DLP PHI REDACTION")
        print("=" * 50)
        print(f"📁 Input: {input_folder}")
        print(f"📁 Output: {output_folder}")
        print(f"🌍 Project: {self.project_id}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create output folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"📁 Created output folder: {output_folder}")
        
        # Get HTML files
        html_files = [f for f in os.listdir(input_folder) if f.endswith('.html')]
        
        if not html_files:
            print("❌ No HTML files found!")
            return
        
        print(f"🔍 Found {len(html_files)} HTML files to process")
        print("\n" + "=" * 50)
        
        # Process files
        total_files = len(html_files)
        successful_files = 0
        total_redactions = 0
        errors = []
        
        for i, filename in enumerate(html_files, 1):
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)
            
            print(f"📄 [{i}/{total_files}] Processing: {filename}")
            
            redactions, error = self.process_file(input_file_path, output_file_path)
            
            if error:
                errors.append((input_file_path, error))
                print(f"❌ Error: {error}")
            else:
                successful_files += 1
                total_redactions += redactions
                print(f"✅ Completed: {redactions} redactions")
        
        # Summary
        print("\n" + "=" * 70)
        print("GOOGLE CLOUD DLP PHI REDACTION SUMMARY")
        print("=" * 70)
        print(f"Total files processed: {total_files}")
        print(f"Successfully processed: {successful_files}")
        print(f"Failed: {len(errors)}")
        print(f"Total PHI elements redacted: {total_redactions}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if errors:
            print("\nERRORS:")
            for file_path, error in errors:
                print(f"  - {os.path.basename(file_path)}: {error}")
        
        print(f"\n✓ Google Cloud DLP PHI redaction process completed!")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Simple Google Cloud DLP PHI redaction')
    parser.add_argument('--project', '-p', required=True, help='Google Cloud Project ID')
    parser.add_argument('--input', '-i', default='clean-data', help='Input folder')
    parser.add_argument('--output', '-o', default='dlp-redacted', help='Output folder')
    
    args = parser.parse_args()
    
    # Create redactor
    redactor = SimpleDLPRedactor(args.project)
    
    # Process files
    redactor.process_folder(args.input, args.output)


if __name__ == "__main__":
    main()