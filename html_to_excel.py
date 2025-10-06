import pandas as pd
from bs4 import BeautifulSoup
import os
import glob
import argparse
from typing import List, Dict, Any

class HTMLToExcelConverter:
    """Convert HTML files to Excel format"""
    
    def __init__(self):
        pass
    
    def parse_html_tables(self, html_content: str) -> Dict[str, List[List[str]]]:
        """Parse HTML content and extract all tables"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        
        parsed_tables = {}
        
        for i, table in enumerate(tables):
            table_name = f"Table_{i+1}"
            
            # Try to find a preceding header to name the table
            prev_element = table.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if prev_element and prev_element.get_text(strip=True):
                table_name = prev_element.get_text(strip=True).replace(' ', '_')
            
            # Extract table data
            rows = []
            
            # Get all rows
            table_rows = table.find_all('tr')
            
            for row in table_rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:  # Only add non-empty rows
                    rows.append(row_data)
            
            if rows:  # Only add tables with data
                parsed_tables[table_name] = rows
        
        return parsed_tables
    
    def parse_html_content(self, html_content: str) -> Dict[str, Any]:
        """Parse HTML content and extract structured data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = "Unknown Document"
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Extract tables
        tables = self.parse_html_tables(html_content)
        
        # Extract all text content organized by sections
        sections = {}
        
        # Find all headers and their content
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for header in headers:
            section_name = header.get_text(strip=True)
            
            # Get content after this header until next header
            content = []
            current = header.next_sibling
            
            while current:
                if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                
                if current.name == 'p':
                    text = current.get_text(strip=True)
                    if text:
                        content.append(text)
                elif current.name == 'ul':
                    # Handle lists
                    list_items = current.find_all('li')
                    for item in list_items:
                        text = item.get_text(strip=True)
                        if text:
                            content.append(f"• {text}")
                
                current = current.next_sibling
            
            if content:
                sections[section_name] = content
        
        return {
            'title': title,
            'tables': tables,
            'sections': sections
        }
    
    def convert_file_to_excel(self, html_file: str, excel_file: str):
        """Convert a single HTML file to Excel"""
        try:
            # Read HTML file
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML content
            parsed_data = self.parse_html_content(html_content)
            
            # Create Excel writer
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                
                # Sheet 1: Document Info
                doc_info = pd.DataFrame({
                    'Property': ['Title', 'Source File'],
                    'Value': [parsed_data['title'], os.path.basename(html_file)]
                })
                doc_info.to_excel(writer, sheet_name='Document_Info', index=False)
                
                # Sheet 2: All Tables (if any)
                if parsed_data['tables']:
                    # Combine all tables into one sheet
                    all_tables_data = []
                    
                    for table_name, table_data in parsed_data['tables'].items():
                        # Add table header
                        all_tables_data.append([f"=== {table_name} ==="])
                        all_tables_data.append([])  # Empty row
                        
                        # Add table data
                        for row in table_data:
                            # Ensure all rows have the same number of columns
                            max_cols = max(len(row) for row in table_data) if table_data else 1
                            padded_row = row + [''] * (max_cols - len(row))
                            all_tables_data.append(padded_row)
                        
                        all_tables_data.append([])  # Empty row between tables
                    
                    # Create DataFrame
                    if all_tables_data:
                        max_cols = max(len(row) for row in all_tables_data)
                        for row in all_tables_data:
                            row.extend([''] * (max_cols - len(row)))
                        
                        tables_df = pd.DataFrame(all_tables_data)
                        tables_df.to_excel(writer, sheet_name='Tables', index=False, header=False)
                
                # Sheet 3: Text Content by Sections
                if parsed_data['sections']:
                    sections_data = []
                    
                    for section_name, content_list in parsed_data['sections'].items():
                        sections_data.append({'Section': section_name, 'Content': '\n'.join(content_list)})
                    
                    sections_df = pd.DataFrame(sections_data)
                    sections_df.to_excel(writer, sheet_name='Sections', index=False)
                
                # Individual sheets for each table (if there are tables)
                for table_name, table_data in parsed_data['tables'].items():
                    if table_data:
                        # Create DataFrame from table data
                        df = pd.DataFrame(table_data)
                        
                        # Use first row as headers if it looks like headers
                        if len(table_data) > 1:
                            first_row = table_data[0]
                            # Check if first row contains typical header words
                            header_words = ['date', 'type', 'name', 'description', 'department', 'care', 'team']
                            if any(word in str(cell).lower() for cell in first_row for word in header_words):
                                df.columns = first_row
                                df = df.iloc[1:]  # Remove header row from data
                        
                        # Clean sheet name (Excel sheet names have restrictions)
                        clean_name = table_name.replace('/', '_').replace('\\', '_')[:31]
                        df.to_excel(writer, sheet_name=clean_name, index=False)
            
            print(f"✅ Converted: {html_file} → {excel_file}")
            
        except Exception as e:
            print(f"❌ Error converting {html_file}: {e}")
    
    def convert_folder_to_excel(self, input_folder: str, output_folder: str):
        """Convert all HTML files in a folder to Excel"""
        os.makedirs(output_folder, exist_ok=True)
        
        html_files = glob.glob(os.path.join(input_folder, "*.html"))
        
        if not html_files:
            print("No HTML files found in input folder.")
            return
        
        print(f"Converting {len(html_files)} HTML files to Excel...")
        
        for html_file in html_files:
            filename = os.path.basename(html_file)
            excel_filename = filename.replace('.html', '.xlsx')
            excel_path = os.path.join(output_folder, excel_filename)
            
            self.convert_file_to_excel(html_file, excel_path)
        
        print(f"\n🎉 Conversion complete! Excel files saved to {output_folder}")


def main():
    """Main function for HTML to Excel conversion"""
    parser = argparse.ArgumentParser(description='Convert HTML files to Excel format')
    parser.add_argument('--input', '-i', required=True, help='Input HTML file or folder')
    parser.add_argument('--output', '-o', required=True, help='Output Excel file or folder')
    
    args = parser.parse_args()
    
    converter = HTMLToExcelConverter()
    
    if os.path.isfile(args.input):
        # Convert single file
        converter.convert_file_to_excel(args.input, args.output)
    elif os.path.isdir(args.input):
        # Convert folder
        converter.convert_folder_to_excel(args.input, args.output)
    else:
        print(f"Error: {args.input} is not a valid file or directory")


if __name__ == "__main__":
    # For testing without command line args
    if len(os.sys.argv) == 1:
        # Test conversion
        converter = HTMLToExcelConverter()
        
        # Test with sample HTML
        sample_html = """
        <!DOCTYPE html>
        <html><head><title>Medical Record</title></head><body>
        <h2><a name="toc">Table of Contents</a></h2>
        <ul><li><a href="#encounter">Encounter Details</a></li></ul>
        
        <h3>Encounter Details</h3>
        <table>
            <tr><td>Date</td><td>Type</td><td>Department</td></tr>
            <tr><td>09/04/2024</td><td>Office Visit</td><td>Cardiology</td></tr>
        </table>
        
        <h3>Medications</h3>
        <p>Patient takes metformin 500mg daily.</p>
        </body></html>
        """
        
        # Save sample HTML
        with open('test_sample.html', 'w') as f:
            f.write(sample_html)
        
        # Convert to Excel
        converter.convert_file_to_excel('test_sample.html', 'test_output.xlsx')
        
        # Clean up
        os.remove('test_sample.html')
        
        print("Test conversion completed! Check test_output.xlsx")
    else:
        main()