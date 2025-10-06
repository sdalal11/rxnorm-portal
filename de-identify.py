import re
import os
import glob
import argparse

class HeaderRemover:
    """Remove header section before Table of Contents"""
    
    def __init__(self):
        pass
    
    def remove_header_section(self, text: str) -> str:
        """Remove everything before 'Table of Contents' and preserve HTML structure"""
        # Find the Table of Contents section
        toc_pattern = r'<h2><a name="toc">Table of Contents</a></h2>'
        toc_match = re.search(toc_pattern, text, re.IGNORECASE)
        
        if toc_match:
            # Keep HTML head and opening body tag, then start from Table of Contents
            html_head_pattern = r'(<!DOCTYPE[^>]*>.*?<body[^>]*>)'
            head_match = re.search(html_head_pattern, text, re.DOTALL)
            
            if head_match:
                html_head = head_match.group(1)
                content_from_toc = text[toc_match.start():]
                
                # Find closing body and html tags
                closing_tags = re.search(r'(</body></html>)$', text, re.IGNORECASE)
                if closing_tags:
                    closing = closing_tags.group(1)
                else:
                    closing = '</body></html>'
                
                # Combine: HTML head + Table of Contents onwards + closing tags
                return html_head + '\n' + content_from_toc.replace('</body></html>', '') + '\n' + closing
            else:
                # Fallback: just keep from Table of Contents onwards
                return content_from_toc
        else:
            print("Warning: Table of Contents not found. Keeping entire document.")
            return text

    def process_file(self, input_path: str, output_path: str):
        """Process a single file"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            processed_text = self.remove_header_section(original_text)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            
            print(f"✅ Header removed: {input_path} → {output_path}")
            
        except Exception as e:
            print(f"❌ Error processing {input_path}: {e}")

    def process_folder(self, input_folder: str, output_folder: str):
        """Process all HTML files in a folder"""
        os.makedirs(output_folder, exist_ok=True)
        
        html_files = glob.glob(os.path.join(input_folder, "*.html"))
        
        if not html_files:
            print("No HTML files found in input folder.")
            return
        
        print(f"Processing {len(html_files)} files...")
        
        for html_file in html_files:
            filename = os.path.basename(html_file)
            output_filename = filename.replace('.html', '_clean.html')
            output_path = os.path.join(output_folder, output_filename)
            
            self.process_file(html_file, output_path)
        
        print(f"\n🎉 Header removal complete! Files saved to {output_folder}")


def main():
    """Main function for header removal"""
    parser = argparse.ArgumentParser(description='Remove header section before Table of Contents')
    parser.add_argument('--input', '-i', required=True, help='Input file or folder')
    parser.add_argument('--output', '-o', required=True, help='Output file or folder')
    
    args = parser.parse_args()
    
    header_remover = HeaderRemover()
    
    if os.path.isfile(args.input):
        # Process single file
        header_remover.process_file(args.input, args.output)
    elif os.path.isdir(args.input):
        # Process folder
        header_remover.process_folder(args.input, args.output)
    else:
        print(f"Error: {args.input} is not a valid file or directory")


if __name__ == "__main__":
    # For testing without command line args
    if len(os.sys.argv) == 1:
        # Test with sample text
        header_remover = HeaderRemover()
        sample_text = """
        <!DOCTYPE html>
        <html><head><title>Test</title></head><body>
        <h1>Patient Header Info</h1>
        <table>
            <tr><td>Patient Name</td><td>John Smith</td></tr>
            <tr><td>DOB</td><td>03/15/1980</td></tr>
        </table>
        <h2><a name="toc">Table of Contents</a></h2>
        <ul><li><a href="#medications">Medications</a></li></ul>
        <h3><a name="medications">Medications</a></h3>
        <p>Patient takes metformin 500mg daily.</p>
        </body></html>
        """
        
        print("Original text:")
        print(sample_text)
        print("\n" + "="*50 + "\n")
        
        processed = header_remover.remove_header_section(sample_text)
        
        print("Text with header removed:")
        print(processed)
    else:
        main()
