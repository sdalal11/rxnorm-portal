import re
from bs4 import BeautifulSoup
from datetime import datetime
import os

class HIPAADeidentifier:
    def __init__(self):
        # Patterns for identifying HIPAA data
        self.patterns = {
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'fax': r'\b(?:fax|FAX)[:\s]*\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'zip_code': r'\b\d{5}(?:-\d{4})?\b',
            'mrn': r'\b(?:MRN|Medical Record|Account|Member ID)[:\s#]*[\dA-Z-]+\b',
            'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
            'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        }
        
    def is_proper_name(self, text):
        """Check if text appears to be a human name (first name and/or surname)"""
        text = text.strip()
        
        # Remove common titles if present (without regex)
        title_prefixes = ['Dr.', 'Dr', 'Doctor', 'Mr.', 'Mr', 'Mrs.', 'Mrs', 'Ms.', 'Ms', 'Miss']
        for prefix in title_prefixes:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
                break
        
        words = text.split()
        if len(words) < 1 or len(words) > 4:
            return False
        
        # Extensive exclusion list for medical terms and non-name words
        exclusions = {
            # Titles and common words
            'DR', 'DOCTOR', 'PATIENT', 'MR', 'MRS', 'MS', 'MISS', 'MALE', 'FEMALE', 'PROVIDER',
            'LEFT', 'RIGHT', 'ANTERIOR', 'POSTERIOR', 'LATERAL', 'MEDIAL', 'SUPERIOR', 'INFERIOR',
            
            # Months and days
            'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY',
            'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER',
            'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY',
            
            # Medical facilities and organizations
            'INSTITUTE', 'HOSPITAL', 'CLINIC', 'CENTER', 'MEDICAL', 'HEALTH', 'CARE',
            'DEPARTMENT', 'UNIT', 'SERVICES', 'GROUP', 'ASSOCIATES', 'PHARMACY',
            
            # Medical specialties
            'CARDIOLOGY', 'NEUROLOGY', 'RADIOLOGY', 'PATHOLOGY', 'SURGERY', 'ONCOLOGY',
            'PULMONOLOGY', 'NEPHROLOGY', 'GASTROENTEROLOGY', 'DERMATOLOGY', 'ORTHOPEDICS',
            
            # Body parts and organs
            'BLOOD', 'HEART', 'LUNG', 'LIVER', 'KIDNEY', 'BRAIN', 'STOMACH', 'CHEST',
            'HEAD', 'NECK', 'BACK', 'ABDOMEN', 'PELVIS', 'EXTREMITIES', 'SKIN','BREAST', 'SPINE','JOINT','MUSCLE','BONE','TISSUE','CARTILAGE','VEIN','ARTERY','NERVE','LYMPH','TRACHEA','ESOPHAGUS','DIAPHRAGM','COLON','INTESTINE','PANCREAS','SPLEEN','GALLBLADDER','BLADDER','URETER','URETHRA','PROSTATE','OVARY','UTERUS','CERVIX', 'EYE','EAR','NOSE','THROAT','MOUTH','TEETH','TONGUE','LIP','FINGER','TOE',          
            # Medical conditions (comprehensive list)
            'DIABETES', 'HYPERTENSION', 'COPD', 'ASTHMA', 'CANCER', 'STROKE', 'SEPSIS',
            'PNEUMONIA', 'INFECTION', 'DISEASE', 'DISORDER', 'SYNDROME', 'CONDITION',
            'DYSPNEA', 'EDEMA', 'PAIN', 'FEVER', 'NAUSEA', 'VOMITING', 'DIARRHEA',
            'HYPERCHOLESTEREMIA', 'CHOLESTEROL', 'TRIGLYCERIDES', 'GLUCOSE',
            
            # Medications and substances (add common ones)
            'ASPIRIN', 'INSULIN', 'METFORMIN', 'ATORVASTATIN', 'LOSARTAN', 'LISINOPRIL',
            'METOPROLOL', 'AMLODIPINE', 'SIMVASTATIN', 'GABAPENTIN', 'FUROSEMIDE',
            'OMEPRAZOLE', 'PANTOPRAZOLE', 'ALBUTEROL', 'PREDNISONE', 'WARFARIN',
            'CLOPIDOGREL', 'LEVOTHYROXINE', 'TRAMADOL', 'HYDROCODONE', 'OXYCODONE',
            'CALCIUM', 'MAGNESIUM', 'POTASSIUM', 'SODIUM', 'VITAMIN', 'SUPPLEMENT',
            'CARBONATE', 'CHLORIDE', 'OXIDE', 'SULFATE', 'PHOSPHATE', 'CITRATE',
            'EZETIMIBE', 'ISOSORBIDE', 'MONONITRATE', 'NITROSTAT', 'NITROGLYCERIN',
            'VENTOLIN', 'NOVOLIN', 'LANTUS', 'HUMALOG', 'HUMULIN', 'VITAMINS',
            
            # Brand names
            'WATCHMAN', 'ACCOLADE', 'PACEMAKER', 'STENT', 'IMPLANT', 'DEVICE',
            
            # Medical descriptors
            'NORMAL', 'ABNORMAL', 'POSITIVE', 'NEGATIVE', 'STABLE', 'ACTIVE', 'CHRONIC',
            'ACUTE', 'MILD', 'MODERATE', 'SEVERE', 'CONTROLLED', 'UNCONTROLLED',
            'ELEVATED', 'DECREASED', 'INCREASED', 'HIGH', 'LOW',
            
            # Procedures and tests
            'CATHETERIZATION', 'SURGERY', 'PROCEDURE', 'TEST', 'EXAM', 'EXAMINATION',
            'ECHO', 'ECHOCARDIOGRAM', 'STRESS', 'NUCLEAR', 'CATH', 'ANGIOGRAM',
            
            # Common non-name words
            'THE', 'AND', 'FOR', 'WITH', 'WITHOUT', 'FROM', 'ORAL', 'TABLET', 'CAPSULE',
            'INJECTION', 'INHALATION', 'TOPICAL', 'SUBLINGUAL', 'TRANSDERMAL',
            
            # Medical abbreviations that might be capitalized
            'MG', 'ML', 'MCG', 'UNIT', 'UNITS', 'DOSE', 'DOSAGE', 'ER', 'SR', 'XR', 'HCL'
        }
        
        # Check each word
        for word in words:
            word_upper = word.upper()
            
            # If word is in exclusions, not a name
            if word_upper in exclusions:
                return False
            
            # Word must start with capital letter
            if not word[0].isupper():
                return False
            
            # Check if word contains valid name characters (without regex)
            for idx, char in enumerate(word):
                if not (char.isalpha() or (char in ['-', "'"] and idx > 0)):
                    return False
        
        # If we get here, it looks like a human name
        # Additional check: at least one word should be 2+ characters (exclude initials-only)
        if all(len(w) <= 2 for w in words):
            return False
            
        return True
    
    def extract_date_components(self, text):
        """Extract dates and check if age > 89"""
        dates = re.findall(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', text)
        current_year = datetime.now().year
        
        for date_match in dates:
            month, day, year = date_match
            year = int(year)
            if year < 100:
                year += 2000 if year < 50 else 1900
            
            age = current_year - year
            if age > 89:
                # Redact dates for ages > 89
                text = re.sub(r'\b' + month + r'[/-]' + day + r'[/-]' + str(date_match[2]) + r'\b', 
                            '[DATE REDACTED - AGE >89]', text)
        
        return text
    
    def redact_addresses(self, text):
        """Redact street addresses and geographic subdivisions"""
        # Street patterns
        street_patterns = [
            r'\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl)\.?\s*(?:,\s*)?(?:STE|Suite|Apt|Unit)?\s*\d*',
            r'\b\d{1,5}\s+[A-Z\s]+(?:ST|AVE|RD|DR|LN|BLVD|WAY|CT|CIR|PL)\b'
        ]
        
        for pattern in street_patterns:
            text = re.sub(pattern, '[ADDRESS REDACTED]', text, flags=re.IGNORECASE)
        
        # City, State, ZIP pattern
        text = re.sub(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b', 
                     '[CITY, STATE, ZIP REDACTED]', text)
        
        return text
    
    def redact_phone_numbers(self, text):
        """Redact phone and fax numbers"""
        text = re.sub(self.patterns['phone'], '[PHONE REDACTED]', text)
        text = re.sub(self.patterns['fax'], '[FAX REDACTED]', text)
        return text
    
    def redact_identifiers(self, text):
        """Redact various identifiers"""
        # Email
        text = re.sub(self.patterns['email'], '[EMAIL REDACTED]', text)
        # SSN
        text = re.sub(self.patterns['ssn'], '[SSN REDACTED]', text)
        # URLs
        text = re.sub(self.patterns['url'], '[URL REDACTED]', text)
        # IP addresses
        text = re.sub(self.patterns['ip'], '[IP REDACTED]', text)
        # ZIP codes (when not part of address already redacted)
        text = re.sub(r'\bZIP[:\s]+\d{5}(?:-\d{4})?\b', 'ZIP: [REDACTED]', text, flags=re.IGNORECASE)
        
        return text
    
    def redact_names_in_text(self, text):
        """Redact human names (first name and surname patterns) from text"""
        # First, handle common patterns with titles
        text = re.sub(r'\b(?:Dr\.?|Doctor|Mr\.?|Mrs\.?|Ms\.?|Miss)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b', 
                     '[NAME REDACTED]', text)
        
        # Split text into tokens while preserving delimiters
        tokens = re.split(r'(\s+|[,;:.()\[\]{}])', text)
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Skip delimiters and short tokens
            if not token.strip() or len(token) <= 1:
                result.append(token)
                i += 1
                continue
            
            # Check if this token is all delimiters
            if re.match(r'^[\s,;:.()\[\]{}]+$', token):
                result.append(token)
                i += 1
                continue
            
            # Look ahead for potential multi-word names (up to 3 words)
            name_candidate = []
            temp_idx = i
            word_count = 0
            
            while temp_idx < len(tokens) and word_count < 3:
                t = tokens[temp_idx]
                
                # If we hit a delimiter, check if it's a space (continue) or other (break)
                if re.match(r'^[\s]+$', t):
                    if name_candidate:  # Only add space if we have words
                        name_candidate.append(t)
                    temp_idx += 1
                    continue
                elif re.match(r'^[,;:.()\[\]{}]+$', t):
                    break
                
                # Check if token looks like part of a name
                if re.match(r'^[A-Z][a-z]+(?:[-\'][A-Z]?[a-z]*)*$', t):
                    name_candidate.append(t)
                    word_count += 1
                    temp_idx += 1
                else:
                    break
            
            # Check if we found a valid name
            if name_candidate:
                name_text = ''.join(name_candidate).strip()
                if self.is_proper_name(name_text):
                    result.append('[NAME REDACTED]')
                    i = temp_idx
                    continue
            
            # Not a name, keep original token
            result.append(token)
            i += 1
        
        return ''.join(result)
    
    def process_html(self, html_content):
        """Process HTML and redact HIPAA identifiers"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Process all text nodes
        for element in soup.find_all(text=True):
            if element.parent.name in ['script', 'style']:
                continue
            
            text = str(element)
            
            # Apply redactions in order
            text = self.redact_addresses(text)
            text = self.redact_phone_numbers(text)
            text = self.redact_identifiers(text)
            text = self.extract_date_components(text)
            text = self.redact_names_in_text(text)
            
            element.replace_with(text)
        
        return str(soup)
    
    def process_file(self, input_path, output_path=None):
        """Process a single HTML file"""
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_deidentified{ext}"
        
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        deidentified_html = self.process_html(html_content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(deidentified_html)
        
        print(f"Processed: {input_path} -> {output_path}")
        return output_path
    
    def process_directory(self, input_dir, output_dir=None):
        """Process all HTML files in a directory"""
        if output_dir is None:
            output_dir = os.path.join(input_dir, 'deidentified')
        
        os.makedirs(output_dir, exist_ok=True)
        
        for filename in os.listdir(input_dir):
            if filename.endswith('.html') or filename.endswith('.htm'):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                self.process_file(input_path, output_path)


# Usage example
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='De-identify HIPAA data from HTML medical records')
    parser.add_argument('--input', '-i', required=True, help='Input file or directory path')
    parser.add_argument('--output', '-o', help='Output file or directory path (optional)')
    parser.add_argument('--mode', '-m', choices=['file', 'directory'], default='file',
                       help='Processing mode: file (single file) or directory (all HTML files)')
    
    args = parser.parse_args()
    
    deidentifier = HIPAADeidentifier()
    
    if args.mode == 'file':
        deidentifier.process_file(args.input, args.output)
    else:
        deidentifier.process_directory(args.input, args.output)