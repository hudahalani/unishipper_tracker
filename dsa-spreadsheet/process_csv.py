import csv
import os
from datetime import datetime
import re
from io import StringIO
import pandas as pd

def process_csv_file():
    # Get the CSV file from the current directory
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the current directory")
        return
    
    csv_file = csv_files[0]  # Use the first CSV file found
    print(f"Processing file: {csv_file}")
    
    # Extract date from filename (format: MM_DD_YYYY HH_MM AM/PM.csv)
    # Extract just the date part: MM_DD_YYYY
    date_match = re.search(r'(\d{2}_\d{2}_\d{4})', csv_file)
    if not date_match:
        print("Could not extract date from filename")
        return
    
    filename_date = date_match.group(1)
    print(f"Date from filename: {filename_date}")
    
    # Convert filename date to datetime for comparison
    filename_datetime = datetime.strptime(filename_date, '%m_%d_%Y')
    
    # Store matching records
    matching_records = []
    
    # Try different encodings to handle the file
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    file_content = None
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as file:
                file_content = file.read()
            print(f"Successfully read file with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        print("Could not read file with any encoding")
        return
    
    # Parse CSV from the content
    reader = csv.DictReader(StringIO(file_content))
    
    for row in reader:
        status = row.get('Status', '').strip()
        created_date_str = row.get('Created Date', '').strip()
        bol_number = row.get('BOL #', '').strip()
        pro_number = row.get('PRO/Tracking#', '').strip()
        
        # Skip if status is VOID
        if status.upper() == 'VOID':
            continue
        
        # Parse created date
        try:
            created_datetime = datetime.strptime(created_date_str, '%Y-%m-%d %H:%M:%S')
            created_date_only = created_datetime.strftime('%m_%d_%Y')
            
            # Check if created date matches filename date
            if created_date_only == filename_date:
                matching_records.append({
                    'BOL #': bol_number,
                    'PRO/Tracking#': pro_number,
                    'Created Date': created_date_str,
                    'Status': status
                })
                print(f"Match found: BOL {bol_number}, PRO {pro_number}")
                
        except ValueError as e:
            print(f"Error parsing date '{created_date_str}': {e}")
            continue
    
    # Write results to Excel file
    output_filename = f"filtered_results_{filename_date}.xlsx"
    
    if matching_records:
        # Create DataFrame from matching records
        df = pd.DataFrame(matching_records)
        
        # Reorder columns for better presentation
        df = df[['BOL #', 'PRO/Tracking#', 'Created Date', 'Status']]
        
        # Write to Excel with formatting
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Filtered Results', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Filtered Results']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Add header formatting
            from openpyxl.styles import Font, PatternFill
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.font = Font(bold=True, color="FFFFFF")
        
        print(f"\nResults written to: {output_filename}")
        print(f"Total matching records: {len(matching_records)}")
    else:
        # Create empty DataFrame with headers
        df = pd.DataFrame(columns=['BOL #', 'PRO/Tracking#', 'Created Date', 'Status'])
        df.to_excel(output_filename, sheet_name='Filtered Results', index=False)
        print(f"\nNo matching records found. Empty Excel file created: {output_filename}")

if __name__ == "__main__":
    process_csv_file() 