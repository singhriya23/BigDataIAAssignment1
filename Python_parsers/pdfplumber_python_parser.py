import pdfplumber
import csv

# File paths
pdf_path = "/Users/riyasingh/Desktop/PDF_PARSER/PDF_Files/PDF_File(2).pdf"
output_table_file = "/Users/riyasingh/Desktop/PDF_PARSER/Python_parsers/Output_files/Output_pdfplumber/extracted_tables"

# Open the PDF file
with pdfplumber.open(pdf_path) as pdf:
    # Open CSV file to write tables
    with open(output_table_file, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        table_found = False  # Flag to track if tables were found

        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            if tables:  # If tables exist on the page
                table_found = True
                for table in tables:
                    csv_writer.writerow([f"--- Page {page_num} ---"])  # Add page header
                    csv_writer.writerows(table)  # Write table rows
                    csv_writer.writerow([])  # Add blank line between tables

        if not table_found:
            print("No tables found in the PDF.")

print(f"Tables extracted and saved to {output_table_file}")
