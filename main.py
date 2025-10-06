# import re
# import json
# import csv
# import os
# import requests
# from typing import List, Dict, Optional
# from datetime import datetime
# import glob

# class LocalMedicationLLM:
#     """Medication extraction with confidence-based filtering"""
    
#     def __init__(self, medication_lexicon: Dict[str, Dict]):
#         self.medication_lexicon = medication_lexicon
#         self.generic_names = list(medication_lexicon.keys())
#         self.brand_names = self._extract_brand_names(medication_lexicon)
#         # High confidence threshold for filtering
#         self.min_confidence_threshold = 0.95
        
#     def _extract_brand_names(self, lexicon: Dict[str, Dict]) -> Dict[str, str]:
#         """Extract brand names and map to generic names"""
#         brand_to_generic = {}
#         for generic, info in lexicon.items():
#             # Add most common brand name
#             if info.get('most common brand name'):
#                 brand = info['most common brand name'].lower()
#                 brand_to_generic[brand] = generic
            
#             # Add other brand names
#             if info.get('other brand names'):
#                 other_brands = info['other brand names'].split(',')
#                 for brand in other_brands:
#                     brand = brand.strip().lower()
#                     if brand:
#                         brand_to_generic[brand] = generic
        
#         return brand_to_generic
    
#     def extract_medications(self, text: str) -> List[Dict]:
#         """Extract medication mentions from text - only high confidence results"""
#         medications = []
        
#         # Method 1: Generic name matching (highest confidence: 0.98)
#         medications.extend(self._extract_by_generic_names(text))
        
#         # Method 2: Brand name matching (high confidence: 0.96)  
#         medications.extend(self._extract_by_brand_names(text))
        
#         # Remove duplicates and filter by confidence threshold
#         medications = self._deduplicate_and_filter(medications, text)
        
#         # Filter to only keep medications with confidence >= 0.95
#         high_confidence_medications = [
#             med for med in medications 
#             if med.get('confidence', 0) >= self.min_confidence_threshold
#         ]
        
#         return high_confidence_medications
    
#     def _extract_by_generic_names(self, text: str) -> List[Dict]:
#         """Extract using generic drug names - highest confidence"""
#         medications = []
#         for generic_name in self.generic_names:
#             pattern = r'\b' + re.escape(generic_name) + r'\b'
#             for match in re.finditer(pattern, text, re.IGNORECASE):
#                 medications.append({
#                     'text': match.group(0),
#                     'start_offset': match.start(),
#                     'end_offset': match.end(),
#                     'extraction_method': 'generic_name',
#                     'confidence': 0.98,  # Very high confidence for exact generic matches
#                     'matched_generic': generic_name
#                 })
#         return medications
    
#     def _extract_by_brand_names(self, text: str) -> List[Dict]:
#         """Extract using brand drug names - high confidence"""
#         medications = []
#         for brand_name, generic_name in self.brand_names.items():
#             pattern = r'\b' + re.escape(brand_name) + r'\b'
#             for match in re.finditer(pattern, text, re.IGNORECASE):
#                 medications.append({
#                     'text': match.group(0),
#                     'start_offset': match.start(),
#                     'end_offset': match.end(),
#                     'extraction_method': 'brand_name',
#                     'confidence': 0.96,  # High confidence for known brand names
#                     'matched_generic': generic_name
#                 })
#         return medications
    
#     def _is_negated(self, text: str, start: int, end: int) -> bool:
#         """Check if medication mention is negated"""
#         context_start = max(0, start - 100)
#         context_end = min(len(text), end + 100)
#         context = text[context_start:context_end].lower()
        
#         negation_words = ['no', 'not', 'denies', 'refuses', 'stopped', 'discontinued', 
#                          'allergic', 'allergy', 'adverse', 'contraindicated', 'avoid']
        
#         return any(neg_word in context for neg_word in negation_words)
    
#     def _deduplicate_and_filter(self, medications: List[Dict], text: str) -> List[Dict]:
#         """Remove duplicates and filter out negated mentions"""
#         seen = set()
#         filtered = []
        
#         for med in medications:
#             key = (med['text'].lower(), med['start_offset'], med['end_offset'])
            
#             if (key not in seen and 
#                 len(med['text']) > 2 and 
#                 not self._is_negated(text, med['start_offset'], med['end_offset'])):
                
#                 seen.add(key)
#                 filtered.append(med)
        
#         return filtered


# class RxNormMapper:
#     """Map medication names to RxNorm CUI codes"""
    
#     def __init__(self, csv_path: str):
#         self.rxnorm_db = self._load_rxnorm_csv(csv_path)
#         self.brand_to_generic = self._create_brand_mapping()
    
#     def _load_rxnorm_csv(self, csv_path: str) -> Dict[str, Dict]:
#         """Load RxNorm data from CSV"""
#         rxnorm_db = {}
        
#         try:
#             with open(csv_path, 'r', encoding='utf-8') as csvfile:
#                 reader = csv.DictReader(csvfile)
#                 for row in reader:
#                     generic_name = row['generic'].strip().lower()
#                     rxnorm_db[generic_name] = {
#                         'rx_cui': row['RxCUI'].strip(),
#                         'normalized_name': row['generic'].strip(),
#                         'cui_type': row.get('RxCUI term type (single or multi ingredient)', 'IN'),
#                         'brand_name': row.get('most common brand name', '').strip(),
#                         'other_brands': row.get('other brand names', '').strip()
#                     }
#         except FileNotFoundError:
#             print(f"Warning: RxNorm CSV file not found at {csv_path}")
#             rxnorm_db = {}
        
#         return rxnorm_db
    
#     def _create_brand_mapping(self) -> Dict[str, str]:
#         """Create mapping from brand names to generic names"""
#         brand_mapping = {}
        
#         for generic, info in self.rxnorm_db.items():
#             # Map primary brand name
#             if info.get('brand_name'):
#                 brand_mapping[info['brand_name'].lower()] = generic
            
#             # Map other brand names
#             if info.get('other_brands'):
#                 other_brands = info['other_brands'].split(',')
#                 for brand in other_brands:
#                     brand = brand.strip().lower()
#                     if brand:
#                         brand_mapping[brand] = generic
        
#         return brand_mapping
    
#     def map_to_cui(self, medications: List[Dict]) -> List[Dict]:
#         """Map medication mentions to RxNorm CUI codes - maintains confidence filtering"""
#         mapped_medications = []
        
#         for med in medications:
#             mapping_result = self._lookup_medication(med)
#             med.update(mapping_result)
#             mapped_medications.append(med)
        
#         return mapped_medications
    
#     def _lookup_medication(self, med: Dict) -> Dict:
#         """Lookup individual medication in RxNorm database"""
#         med_text = med['text'].lower().strip()
        
#         # First, try direct generic name lookup
#         if med_text in self.rxnorm_db:
#             rxnorm_info = self.rxnorm_db[med_text]
#             return {
#                 'rx_cui': rxnorm_info['rx_cui'],
#                 'normalized_name': rxnorm_info['normalized_name'],
#                 'cui_type': rxnorm_info['cui_type'],
#                 'mapping_method': 'direct_generic',
#                 'mapping_confidence': 1.0
#             }
        
#         # Try brand name lookup
#         if med_text in self.brand_to_generic:
#             generic_name = self.brand_to_generic[med_text]
#             rxnorm_info = self.rxnorm_db[generic_name]
#             return {
#                 'rx_cui': rxnorm_info['rx_cui'],
#                 'normalized_name': rxnorm_info['normalized_name'],
#                 'cui_type': rxnorm_info['cui_type'],
#                 'mapping_method': 'brand_to_generic',
#                 'mapping_confidence': 0.95
#             }
        
#         # No match found
#         return {
#             'rx_cui': None,
#             'normalized_name': med['text'],
#             'cui_type': None,
#             'mapping_method': 'no_match',
#             'mapping_confidence': 0.0,
#             'flag': 'unrecognized_medication'
#         }


# class MedicationExtractionPipeline:
#     """Complete pipeline with confidence-based filtering"""
    
#     def __init__(self, rxnorm_csv_path: str = "Medication-label-set.csv"):
#         # self.deidentifier = HIPAADeidentifier()
        
#         # Load RxNorm data and initialize components
#         self.rxnorm_mapper = RxNormMapper(rxnorm_csv_path)
#         self.medication_extractor = LocalMedicationLLM(self.rxnorm_mapper.rxnorm_db)
    
#     def process_single_file(self, file_path: str) -> Dict:
#         """Process a single HTML medical record file"""
#         try:
#             # Read the input file
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 raw_text = file.read()
            
#             # Step 1: De-identify PHI
#             # clean_text = self.deidentifier.deidentify_text(raw_html)
            
#             # Step 2: Extract medication mentions (automatically filters confidence >= 0.95)
#             medications = self.medication_extractor.extract_medications(raw_text)
            
#             # Step 3: Map to RxNorm CUIs
#             final_medications = self.rxnorm_mapper.map_to_cui(medications)
            
#             # Format output according to Turmerik specifications
#             output = {
#                 'document_id': os.path.basename(file_path),
#                 'medications': final_medications,
#                 'processing_metadata': {
#                     'total_medications_found': len(final_medications),
#                     'successful_mappings': len([m for m in final_medications if m.get('rx_cui')]),
#                     'flagged_items': len([m for m in final_medications if m.get('flag')]),
#                     'confidence_threshold': 0.95,
#                     'processing_timestamp': datetime.now().isoformat()
#                 }
#             }
            
#             return output
            
#         except Exception as e:
#             return {
#                 'document_id': os.path.basename(file_path),
#                 'error': str(e),
#                 'medications': [],
#                 'processing_metadata': {
#                     'processing_timestamp': datetime.now().isoformat()
#                 }
#             }
    
#     def process_batch(self, input_folder: str, output_folder: str):
#         """Process all HTML files in input folder"""
#         os.makedirs(output_folder, exist_ok=True)
        
#         # Find all HTML files
#         html_files = glob.glob(os.path.join(input_folder, "*.html"))
        
#         if not html_files:
#             print(f"No HTML files found in {input_folder}")
#             return
        
#         print(f"Processing {len(html_files)} files with confidence threshold ≥ 0.95...")
        
#         for html_file in html_files:
#             filename = os.path.basename(html_file)
#             output_filename = filename.replace('.html', '_medications.json')
#             output_path = os.path.join(output_folder, output_filename)
            
#             print(f"Processing {filename}...")
            
#             # Process the file
#             result = self.process_single_file(html_file)
            
#             # Save JSON output
#             with open(output_path, 'w', encoding='utf-8') as f:
#                 json.dump(result, f, indent=2, ensure_ascii=False)
            
#             # Print summary
#             med_count = len(result.get('medications', []))
#             mapped_count = len([m for m in result.get('medications', []) if m.get('rx_cui')])
#             print(f"  ✅ Found {med_count} high-confidence medications, mapped {mapped_count} to RxCUI")
        
#         print(f"\n🎉 Batch processing complete! High-confidence results saved to {output_folder}")


# def main():
#     """Main function to run the medication extraction pipeline"""
#     import argparse
    
#     parser = argparse.ArgumentParser(description='Turmerik Medication Extraction Pipeline (Confidence ≥ 0.95)')
#     parser.add_argument('--input', '-i', required=True, help='Input file or folder')
#     parser.add_argument('--output', '-o', required=True, help='Output folder')
#     parser.add_argument('--rxnorm-csv', default='Medication-label-set.csv', 
#                        help='Path to RxNorm CSV file')
    
#     args = parser.parse_args()
    
#     # Initialize pipeline
#     pipeline = MedicationExtractionPipeline(args.rxnorm_csv)
    
#     # Check if input is file or folder
#     if os.path.isfile(args.input):
#         # Process single file
#         result = pipeline.process_single_file(args.input)
        
#         # Save result
#         os.makedirs(args.output, exist_ok=True)
#         output_filename = os.path.basename(args.input).replace('.html', '_medications.json')
#         output_path = os.path.join(args.output, output_filename)
        
#         with open(output_path, 'w', encoding='utf-8') as f:
#             json.dump(result, f, indent=2, ensure_ascii=False)
        
#         print(f"✅ Processed single file: {output_path}")
#         print(f"Found {len(result['medications'])} high-confidence medications")
        
#     elif os.path.isdir(args.input):
#         # Process batch
#         pipeline.process_batch(args.input, args.output)
        
#     else:
#         print(f"Error: {args.input} is not a valid file or directory")


# if __name__ == "__main__":
#     # For testing without command line args
#     if len(os.sys.argv) == 1:
#         # Test with sample data
#         pipeline = MedicationExtractionPipeline("Medication-label-set.csv")
        
#         # Test on sample text
#         sample_text = "Patient was prescribed aspirin 81mg daily and some unknown medication XYZ123."
        
#         # Simulate the pipeline
#         clean_text = pipeline.deidentifier.deidentify_text(sample_text)
#         medications = pipeline.medication_extractor.extract_medications(clean_text)
#         final_result = pipeline.rxnorm_mapper.map_to_cui(medications)
        
#         print("High-Confidence Pipeline Test (≥0.95):")
#         print(json.dumps({
#             'original_text': sample_text,
#             'deidentified_text': clean_text,
#             'high_confidence_medications': final_result
#         }, indent=2))
#     else:
#         main()



from typing import List, Dict, Optional
from datetime import datetime
import os
import glob
import argparse
import json
import re

class LocalMedicationLLM:
    """Medication extraction with confidence-based filtering and active/non-active tagging"""

    def __init__(self, medication_lexicon: Dict[str, Dict]):
        self.medication_lexicon = medication_lexicon
        self.generic_names = list(medication_lexicon.keys())
        self.brand_names = self._extract_brand_names(medication_lexicon)
        self.min_confidence_threshold = 0.95

    def _extract_brand_names(self, lexicon: Dict[str, Dict]) -> Dict[str, str]:
        """Extract brand names and map to generic names"""
        brand_to_generic = {}
        for generic, info in lexicon.items():
            if 'brand_names' in info:
                for brand in info['brand_names']:
                    brand_to_generic[brand.lower()] = generic
        return brand_to_generic

    def extract_medications(self, text: str) -> List[Dict]:
        """Extract medication mentions from text - only high confidence results"""
        medications = []
        # Method 1: Generic name matching (highest confidence: 0.98)
        medications.extend(self._extract_by_generic_names(text))
        # Method 2: Brand name matching (high confidence: 0.96)
        medications.extend(self._extract_by_brand_names(text))
        # Remove duplicates and filter by confidence threshold, tag active/non-active
        medications = self._deduplicate_and_filter(medications, text)
        # Filter to only keep medications with confidence >= 0.95
        high_confidence_medications = [
            med for med in medications
            if med.get('confidence', 0) >= self.min_confidence_threshold
        ]
        return high_confidence_medications

    def _extract_by_generic_names(self, text: str) -> List[Dict]:
        """Extract using generic drug names - highest confidence"""
        medications = []
        lowered_text = text.lower()
        for generic_name in self.generic_names:
            idx = 0
            while True:
                idx = lowered_text.find(generic_name.lower(), idx)
                if idx == -1:
                    break
                medications.append({
                    'text': text[idx:idx+len(generic_name)],
                    'start_offset': idx,
                    'end_offset': idx+len(generic_name),
                    'confidence': 0.98,
                    'match_type': 'generic'
                })
                idx += len(generic_name)
        return medications

    def _extract_by_brand_names(self, text: str) -> List[Dict]:
        """Extract using brand drug names - high confidence"""
        medications = []
        lowered_text = text.lower()
        for brand_name, generic_name in self.brand_names.items():
            idx = 0
            while True:
                idx = lowered_text.find(brand_name.lower(), idx)
                if idx == -1:
                    break
                medications.append({
                    'text': text[idx:idx+len(brand_name)],
                    'start_offset': idx,
                    'end_offset': idx+len(brand_name),
                    'confidence': 0.96,
                    'match_type': 'brand',
                    'generic_name': generic_name
                })
                idx += len(brand_name)
        return medications

    # def _is_non_active(self, text: str, start: int, end: int) -> bool:
    #     """Check if medication mention is non-active (negated, discontinued, or in past history section)"""
    #     context_start = max(0, start - 100)
    #     context_end = min(len(text), end + 100)
    #     context = text[context_start:context_end].lower()

    #     # Section-based detection
    #     section_context = text[max(0, start-500):start].lower()
    #     past_section_headers = [
    #         "past medical history", "past medications", "previous medications",
    #         "history of present illness", "medications previously taken"
    #     ]
    #     for header in past_section_headers:
    #         if header in section_context[-200:]:
    #             return True

    #     # Context-based detection
    #     non_active_words = [
    #         'no longer', 'stopped', 'discontinued', 'not taking', 'previously took',
    #         'allergic', 'allergy', 'refused', 'denies', 'avoid', 'contraindicated'
    #     ]
    #     return any(word in context for word in non_active_words)


    import re

    def _is_non_active(self, text: str, start: int, end: int) -> bool:
        """Check if medication mention is non-active (comprehensive pattern detection)"""
        context_start = max(0, start - 150)
        context_end = min(len(text), end + 150)
        context = text[context_start:context_end].lower()
        
        # Get medication name for specific checks
        med_text = text[start:end].lower()

        # Treatment failure patterns that should be non-active
        treatment_failure_patterns = [
            r'no\s+improvement\s+with\s+\w*\s*' + re.escape(med_text),
            r'no\s+response\s+to\s+\w*\s*' + re.escape(med_text),
            r'ineffective\s+\w*\s*' + re.escape(med_text),
            r'not\s+working\s+\w*\s*' + re.escape(med_text),
            r'failed\s+\w*\s*' + re.escape(med_text),
            r'no\s+benefit\s+(from|with)\s+\w*\s*' + re.escape(med_text),
            r'minimal\s+improvement\s+with\s+\w*\s*' + re.escape(med_text),
            r'poor\s+response\s+to\s+\w*\s*' + re.escape(med_text),
        ]

        # Check for treatment failure patterns
        for pattern in treatment_failure_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return True  # Mark as non-active

        strong_active_patterns = [
            r'maintain\s+(his|her|their|the)?\s*\w*\s*' + re.escape(med_text),
            r'continue\s+(his|her|their|the)?\s*\w*\s*' + re.escape(med_text),
            r'continuing\s+(his|her|their|the)?\s*\w*\s*' + re.escape(med_text),
            r'keep\s+(him|her|them|patient)?\s*on\s*\w*\s*' + re.escape(med_text),
            r'remain\s+on\s+\w*\s*' + re.escape(med_text),
            r'stay\s+on\s+\w*\s*' + re.escape(med_text),
        ]
        
        # If we find strong active language, override section-based logic
        for pattern in strong_active_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return False  # Force ACTIVE status
        
        # PRIORITY 2: Check for broader context of maintaining medications
        # Look for "maintain" in a wider context around this medication
        wider_context_start = max(0, start - 500)
        wider_context_end = min(len(text), end + 500)
        wider_context = text[wider_context_start:wider_context_end].lower()
        
        maintain_context_patterns = [
            r'maintain.*?' + re.escape(med_text),
            r'having.*?maintain.*?' + re.escape(med_text),
            r'continue.*?' + re.escape(med_text),
        ]
        
        for pattern in maintain_context_patterns:
            if re.search(pattern, wider_context, re.IGNORECASE):
                return False  # Force ACTIVE status
        
        # PRIORITY 3: Your existing section and pattern detection
        # Section-based detection
        section_context = text[max(0, start-500):start].lower()
        
        # Only mark as non-active if in discontinuation section AND no maintain language
        discontinuation_headers = [
            "medications discontinued during this encounter",
            "discontinued medications", "stopped medications"
        ]
        
        for header in discontinuation_headers:
            if header in section_context[-300:]:
                # But check if there's maintain language in broader context
                if 'maintain' not in wider_context:
                    return True  # Only if no maintain language found
        

        # NEW: Check if we're in a medications table/list (should be active)
        table_indicators = [
            '<table', '</table>', '<tr>', '</tr>', '<td>', '</td>',
            'medications:', 'current medications', 'medication list',
            'sig (take, route, frequency, duration)', 'status', 'active'
        ]
        
        if any(indicator in context for indicator in table_indicators):
            # We're likely in a current medications table
            # Check if explicitly marked as non-active in table
            if any(word in context for word in ['not-taking', 'discontinued', 'completed','stopped']):
                return True
            else:
                return False  # Assume active if in medications table
        

        current_medication_patterns = [
            r'(current|currently|taking|on)\s+\w*\s*' + re.escape(med_text),
            r'continue\s+' + re.escape(med_text),
            r'refill\s+' + re.escape(med_text),
            r'maintain\s+' + re.escape(med_text),
            r'high\s+dose.*?' + re.escape(med_text),  # "on High dose still with symptoms"
            r'still\s+(on|taking|with).*?' + re.escape(med_text),
        ]
        
        # If it shows current use despite "started on" language, keep it active
        for pattern in current_medication_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return False  # Keep as ACTIVE
            

        dose_adjustment_context = text[max(0, start - 300):min(len(text), end + 300)].lower()
    
        dose_change_patterns = [
            r'(increase|decrease|adjust|titrate|change\s+dose|modify\s+dose|raise|lower)\s+\w*\s*' + re.escape(med_text),
            r'increase\s+' + re.escape(med_text),
            r'decrease\s+' + re.escape(med_text),
            r'adjust\s+' + re.escape(med_text),
            r'titrate\s+' + re.escape(med_text),
            r'escalate\s+' + re.escape(med_text),
            r'reduce\s+' + re.escape(med_text),
            r'continue\s+' + re.escape(med_text),
            r'refill\s+' + re.escape(med_text),
            r'maintain\s+' + re.escape(med_text),
        ]
        
        # If it's a dose adjustment, keep it active (return False)
        for pattern in dose_change_patterns:
            if re.search(pattern, dose_adjustment_context, re.IGNORECASE):
                # Check if this mention comes after "increase/start" keywords
                text_before_med = text[max(0, start-100):start].lower()
                text_after_med = text[end:min(len(text), end+100)].lower()
                
                # If "increase", "start", "begin", "new" appears before this mention
                increase_keywords = ['increase', 'start', 'begin', 'new', 'change to', 'adjust to']
                if any(keyword in text_before_med[-50:] for keyword in increase_keywords):
                    return False  # This is the NEW active dose
                
                # If "stop", "discontinue" appears before this mention
                stop_keywords = ['stop', 'discontinue', 'old', 'previous']
                if any(keyword in text_before_med[-50:] for keyword in stop_keywords):
                    return True 
        
        # Section-based detection
        section_context = text[max(0, start-500):start].lower()
        past_section_headers = [
            "past medical history", "past medications", "previous medications",
            "history of present illness", "medications previously taken",
            "previous drug history", "prior medications", "past drug therapy"
        ]
        for header in past_section_headers:
            if header in section_context[-200:]:
                return True
        
        # Enhanced pattern detection with regex
        non_active_patterns = [
            # Past tense patterns - ADD THESE
            r'took\s+\w*\s*' + re.escape(med_text),  # "took apixaban"
            r'was\s+taking\s+\w*\s*' + re.escape(med_text),  # "was taking apixaban"
            r'had\s+taken\s+\w*\s*' + re.escape(med_text),  # "had taken apixaban"
            r'has\s+taken\s+\w*\s*' + re.escape(med_text),  # "has taken apixaban"
            
            # Duration patterns indicating past use - ADD THESE
            r'took\s+\w*\s*' + re.escape(med_text) + r'\s+for\s+\d+',  # "took med for 3 months"
            r'was\s+on\s+\w*\s*' + re.escape(med_text) + r'\s+for\s+\d+',  # "was on med for 3 months"
            r'taking\s+\w*\s*' + re.escape(med_text) + r'\s+for\s+\d+\s+(months?|weeks?|days?)',  # past duration
            r'had\s+been\s+\w*\s*' + re.escape(med_text) + r'\s+for\s+\d+\s+(months?|weeks?|days?)',  # past duration
            # Past tense patterns
            r'(was|were)\s+(on|taking|prescribed)\s+\w*\s*' + re.escape(med_text),
            r'had\s+(been\s+)?(taking|on|prescribed)\s+\w*\s*' + re.escape(med_text),
            r'used\s+to\s+(take|be\s+on)\s+\w*\s*' + re.escape(med_text),
            r'previously\s+(took|taking|on|prescribed)\s+\w*\s*' + re.escape(med_text),
            r'formerly\s+(took|taking|on)\s+\w*\s*' + re.escape(med_text),
            
            # Discontinuation patterns
            r'(discontinued|stopped|ceased|quit|ended)\s+\w*\s*' + re.escape(med_text),
            r'no\s+longer\s+(taking|on)\s+\w*\s*' + re.escape(med_text),
            r'came\s+off\s+(of\s+)?\w*\s*' + re.escape(med_text),
            r'weaned\s+off\s+(of\s+)?\w*\s*' + re.escape(med_text),
            r'tapered\s+off\s+(of\s+)?\w*\s*' + re.escape(med_text),
            
            # Refusal/avoidance patterns
            r'(refusing|refused|denies|declines)\s+\w*\s*' + re.escape(med_text),
            r'wants?\s+to\s+(remain\s+)?off\s+(of\s+)?\w*\s*' + re.escape(med_text),
            r'(avoid|avoiding|stayed\s+away\s+from)\s+\w*\s*' + re.escape(med_text),
            r'not\s+(currently\s+)?(taking|on)\s+\w*\s*' + re.escape(med_text),
            r'off\s+(of\s+)?\w*\s*' + re.escape(med_text),
            
            # Allergy/contraindication patterns
            r'(allergic|allergy)\s+to\s+\w*\s*' + re.escape(med_text),
            r'contraindicated\s+\w*\s*' + re.escape(med_text),
            r'intolerant\s+to\s+\w*\s*' + re.escape(med_text),
            r'adverse\s+reaction\s+to\s+\w*\s*' + re.escape(med_text),
            
            # Temporal indicators of past use
            r'in\s+the\s+past\s+\w*\s*' + re.escape(med_text),
            r'historically\s+\w*\s*' + re.escape(med_text),
            r'prior\s+to\s+\w*\s*' + re.escape(med_text),
            r'before\s+\w*\s*' + re.escape(med_text),
            
            # Trial/temporary use patterns
            r'tried\s+\w*\s*' + re.escape(med_text),
            r'attempted\s+\w*\s*' + re.escape(med_text),
            r'briefly\s+(took|on)\s+\w*\s*' + re.escape(med_text),
            r'short\s+trial\s+of\s+\w*\s*' + re.escape(med_text),
            
            # Failed therapy patterns
            r'failed\s+\w*\s*' + re.escape(med_text),
            r'ineffective\s+\w*\s*' + re.escape(med_text),
            r'did\s+not\s+tolerate\s+\w*\s*' + re.escape(med_text),
            r'could\s+not\s+tolerate\s+\w*\s*' + re.escape(med_text),
            
            # Switching medications patterns
            r'(his|her|their|the)?\s*' + re.escape(med_text) + r'\s+was\s+(changed|switched)\s+to',
            r'change\s+(from\s+)?' + re.escape(med_text) + r'\s+to',
            r'switch\s+(from\s+)?' + re.escape(med_text) + r'\s+to',
            r'replaced\s+' + re.escape(med_text) + r'\s+with',
            r'substitute\s+' + re.escape(med_text) + r'\s+with',
            r'transition\s+(from\s+)?' + re.escape(med_text) + r'\s+to',

            
            # Including/listing patterns (often non-active)
            r'including\s+\w*\s*' + re.escape(med_text),
            r'such\s+as\s+\w*\s*' + re.escape(med_text),
            r'like\s+\w*\s*' + re.escape(med_text),
        ]
        
        # Check for any matching pattern
        for pattern in non_active_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return True
        
        # Simple word-based detection (fallback)
        non_active_words = [
            'was changed to', 'was switched to', 'changed from', 'switched from',
            'replaced with', 'substituted with', 'transitioned to',
            'no improvement with', 'no response to', 'not working',
            'failed', 'ineffective', 'no benefit from', 'poor response',
            'minimal improvement', 'not helping','no longer', 'stopped','completed', 'discontinued', 'not taking', 'previously took',
            'allergic', 'allergy', 'refused', 'denies', 'avoid', 'contraindicated',
            'was on', 'had been taking', 'used to take', 'wants to remain off',
            'came off', 'weaned off', 'tapered off', 'tried', 'failed', 'ineffective',
            'switched from', 'changed from', 'intolerant', 'adverse reaction',
            'briefly took', 'short trial', 'historically', 'in the past',
            'prior to', 'before', 'formerly', 'attempted', 'could not tolerate', 'no need', 'DC','dc', 'previously'
        ]
        
        return any(word in context for word in non_active_words)

    def _deduplicate_and_filter(self, medications: List[Dict], text: str) -> List[Dict]:
        """Remove duplicates (by offset) and tag as active/non-active"""
        seen = set()
        filtered = []
        for med in medications:
            key = (med['text'].lower(), med['start_offset'], med['end_offset'])
            if key not in seen and len(med['text']) > 2:
                seen.add(key)
                med['active_status'] = 'non-active' if self._is_non_active(text, med['start_offset'], med['end_offset']) else 'active'
                filtered.append(med)
        return filtered


class RxNormMapper:
    """Map medication names to RxNorm CUI codes"""

    def __init__(self, csv_path: str):
        self.rxnorm_db = self._load_rxnorm_csv(csv_path)
        self.brand_to_generic = self._create_brand_mapping()

    # def _load_rxnorm_csv(self, csv_path: str) -> Dict[str, Dict]:
    #     """Load RxNorm data from CSV"""
    #     rxnorm_db = {}
    #     try:
    #         import csv
    #         with open(csv_path, newline='', encoding='utf-8') as csvfile:
    #             reader = csv.DictReader(csvfile)
    #             for row in reader:
    #                 generic = row['generic_name'].lower()
    #                 rxnorm_db[generic] = {
    #                     'rx_cui': row.get('rx_cui'),
    #                     'brand_names': [b.strip().lower() for b in row.get('brand_names', '').split('|') if b.strip()],
    #                     'cui_type': row.get('cui_type')
    #                 }
    #     except FileNotFoundError:
    #         print(f"RxNorm CSV file not found: {csv_path}")
    #     return rxnorm_db

    def _load_rxnorm_csv(self, csv_path: str) -> Dict[str, Dict]:
        """Load RxNorm data from CSV"""
        rxnorm_db = {}
        try:
            import csv
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    generic = row['generic'].strip().lower()
                    rxnorm_db[generic] = {
                        'rx_cui': row.get('RxCUI'),
                        'brand_names': [
                            b.strip().lower() for b in (
                                (row.get('most common brand name') or '') + ',' +
                                (row.get('other brand names') or '')
                            ).split(',') if b.strip()
                        ],
                        'cui_type': row.get('RxCUI term type (single or multi ingredient)')
                    }
        except FileNotFoundError:
            print(f"RxNorm CSV file not found: {csv_path}")
        return rxnorm_db

    def _create_brand_mapping(self) -> Dict[str, str]:
        """Create mapping from brand names to generic names"""
        brand_mapping = {}
        for generic, info in self.rxnorm_db.items():
            for brand in info.get('brand_names', []):
                brand_mapping[brand] = generic
        return brand_mapping

    def map_to_cui(self, medications: List[Dict]) -> List[Dict]:
        """Map medication mentions to RxNorm CUI codes - maintains confidence filtering"""
        mapped_medications = []
        for med in medications:
            mapped = self._lookup_medication(med)
            mapped['text'] = med['text']
            mapped['confidence'] = med.get('confidence', 0)
            mapped['active_status'] = med.get('active_status', 'unknown')
            mapped['start_offset'] = med.get('start_offset')
            mapped['end_offset'] = med.get('end_offset')
            mapped_medications.append(mapped)
        return mapped_medications

    def _lookup_medication(self, med: Dict) -> Dict:
        """Lookup individual medication in RxNorm database"""
        med_text = med['text'].lower().strip()
        # First, try direct generic name lookup
        if med_text in self.rxnorm_db:
            info = self.rxnorm_db[med_text]
            return {
                'rx_cui': info['rx_cui'],
                'normalized_name': med_text,
                'cui_type': info.get('cui_type'),
                'mapping_method': 'generic_name',
                'mapping_confidence': 1.0,
                'flag': None
            }
        # Try brand name lookup
        if med_text in self.brand_to_generic:
            generic = self.brand_to_generic[med_text]
            info = self.rxnorm_db.get(generic, {})
            return {
                'rx_cui': info.get('rx_cui'),
                'normalized_name': generic,
                'cui_type': info.get('cui_type'),
                'mapping_method': 'brand_name',
                'mapping_confidence': 0.96,
                'flag': None
            }
        # No match found
        return {
            'rx_cui': None,
            'normalized_name': med['text'],
            'cui_type': None,
            'mapping_method': 'no_match',
            'mapping_confidence': 0.0,
            'flag': 'unrecognized_medication'
        }


class MedicationExtractionPipeline:
    """Complete pipeline with confidence-based filtering"""

    def __init__(self, rxnorm_csv_path: str = "Medication-label-set.csv"):
        # self.deidentifier = HIPAADeidentifier()
        self.rxnorm_mapper = RxNormMapper(rxnorm_csv_path)
        self.medication_extractor = LocalMedicationLLM(self.rxnorm_mapper.rxnorm_db)

    def process_single_file(self, file_path: str) -> Dict:
        """Process a single HTML medical record file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_text = f.read()
            # clean_text = self.deidentifier.deidentify_text(html_text)
            clean_text = html_text  # If no deidentifier
            medications = self.medication_extractor.extract_medications(clean_text)
            mapped = self.rxnorm_mapper.map_to_cui(medications)
            return {
                'file': os.path.basename(file_path),
                'medications': mapped
            }
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return {'file': os.path.basename(file_path), 'medications': [], 'error': str(e)}

    def process_batch(self, input_folder: str, output_folder: str):
        """Process all HTML files in input folder"""
        os.makedirs(output_folder, exist_ok=True)
        html_files = glob.glob(os.path.join(input_folder, "*.html"))
        if not html_files:
            print("No HTML files found in input folder.")
            return
        print(f"Processing {len(html_files)} files with confidence threshold ≥ 0.95...")
        for html_file in html_files:
            result = self.process_single_file(html_file)
            output_filename = os.path.basename(html_file).replace('.html', '_medications.json')
            output_path = os.path.join(output_folder, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"✅ Processed: {output_path}")
        print(f"\n🎉 Batch processing complete! High-confidence results saved to {output_folder}")


def main():
    """Main function to run the medication extraction pipeline"""
    parser = argparse.ArgumentParser(description='Turmerik Medication Extraction Pipeline (Confidence ≥ 0.95)')
    parser.add_argument('--input', '-i', required=True, help='Input file or folder')
    parser.add_argument('--output', '-o', required=True, help='Output folder')  # Changed back to --output
    parser.add_argument('--rxnorm-csv', default='Medication-label-set.csv',
                       help='Path to RxNorm CSV file')
    args = parser.parse_args()
    pipeline = MedicationExtractionPipeline(args.rxnorm_csv)
    if os.path.isfile(args.input):
        result = pipeline.process_single_file(args.input)
        os.makedirs(args.output, exist_ok=True)  # Fixed: use args.output
        output_filename = os.path.basename(args.input).replace('.html', '_medications.json')
        output_path = os.path.join(args.output, output_filename)  # Fixed: use args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Processed single file: {output_path}")
        print(f"Found {len(result['medications'])} high-confidence medications")
    elif os.path.isdir(args.input):
        pipeline.process_batch(args.input, args.output)  # Fixed: use args.output
    else:
        print(f"Error: {args.input} is not a valid file or directory")

if __name__ == "__main__":
    # For testing without command line args
    if len(os.sys.argv) == 1:
        pipeline = MedicationExtractionPipeline("Medication-label-set.csv")
        sample_text = (
            "Past Medical History: Patient previously took metformin but discontinued due to GI upset. "
            "Currently taking aspirin 81mg daily. "
            "Patient was prescribed Lasix last year, but is not taking it now."
        )
        # clean_text = pipeline.deidentifier.deidentify_text(sample_text)
        clean_text = sample_text
        medications = pipeline.medication_extractor.extract_medications(clean_text)
        final_result = pipeline.rxnorm_mapper.map_to_cui(medications)
        print("High-Confidence Pipeline Test (≥0.95):")
        print(json.dumps(final_result, indent=2))
    else:
        main()