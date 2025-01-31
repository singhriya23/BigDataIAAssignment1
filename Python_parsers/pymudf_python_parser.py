import fitz  # PyMuPDF
import os
import csv

# Input PDF path
pdf_file_path = "/Users/riyasingh/Desktop/PDF_PARSER/PDF_Files/Assignment(1)-Research_on_LLMs.pdf"

# Output file paths
output_markdown_file = "/Users/riyasingh/Desktop/PDF_PARSER/Python_parsers/Output_files/Output_pymupdf/extracted_text.md"
output_images_folder = "/Users/riyasingh/Desktop/PDF_PARSER/Python_parsers/Output_files/Output_pymupdf/extracted_images"
output_tables_folder = "/Users/riyasingh/Desktop/PDF_PARSER/Python_parsers/Output_files/Output_pymupdf/extracted_tables"

# Create output directories if they don't exist
os.makedirs(output_images_folder, exist_ok=True)
os.makedirs(output_tables_folder, exist_ok=True)

# Open the PDF
pdf_document = fitz.open(pdf_file_path)

# Open Markdown file for writing
with open(output_markdown_file, "w", encoding="utf-8") as markdown_file:
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        markdown_file.write(f"# Page {page_num + 1}\n")

        # --- Extract Text ---
        text = page.get_text("text")
        markdown_file.write("## Extracted Text\n")
        markdown_file.write(text + "\n\n")

        # --- Extract Tables ---
        markdown_file.write("## Extracted Tables\n")
        tables = page.find_tables()

        if tables and len(tables.tables) > 0:
            for table_index, table in enumerate(tables.tables):
                table_filename = f"page_{page_num+1}_table_{table_index+1}.csv"
                table_filepath = os.path.join(output_tables_folder, table_filename)

                # Save table as CSV
                with open(table_filepath, "w", newline="", encoding="utf-8") as csv_file:
                    csv_writer = csv.writer(csv_file)
                    for row in table.extract():
                        csv_writer.writerow(row)

                # Reference the table file in Markdown
                markdown_file.write(f"[Extracted Table {table_index+1}](extracted_tables/{table_filename})\n\n")
        else:
            markdown_file.write("_No tables found on this page._\n\n")

        # --- Extract Images ---
        markdown_file.write("## Extracted Images\n")
        image_list = page.get_images(full=True)
        if image_list:
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                img_bytes = base_image["image"]
                img_ext = base_image["ext"]
                img_filename = f"page_{page_num+1}_image_{img_index+1}.{img_ext}"
                img_path = os.path.join(output_images_folder, img_filename)
                
                # Save the image file
                with open(img_path, "wb") as img_file:
                    img_file.write(img_bytes)

                # Add image reference to Markdown
                markdown_file.write(f"![Extracted Image {img_index+1}](extracted_images/{img_filename})\n\n")
        else:
            markdown_file.write("_No images found on this page._\n\n")

        markdown_file.write("---\n\n")  # Markdown separator for pages

# Close the PDF document
pdf_document.close()

print(f"Text extracted to {output_markdown_file}")
print(f"Tables saved in {output_tables_folder}")
print(f"Images saved in {output_images_folder}")
