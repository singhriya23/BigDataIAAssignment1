import fitz  # PyMuPDF
import os
 
# Input PDF path
pdf_file_path = "/Users/kaushikj/Downloads/Text_file(1).pdf"
 
# Output Markdown file path
output_markdown_file = "/Users/kaushikj/Desktop/PDF Parser.md"
 
# Open the PDF
pdf_document = fitz.open(pdf_file_path)
 
# Create and open the Markdown file for writing
with open(output_markdown_file, "w", encoding="utf-8") as markdown_file:
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
 
        # --- Extract Text ---
        text = page.get_text("text")
 
        # Write extracted text to the Markdown file
        markdown_file.write(f"# Page {page_num + 1}\n")
        markdown_file.write(text + "\n\n")
        markdown_file.write("---\n\n")  # Markdown separator for pages
 
# Close the PDF document
pdf_document.close()
 
print(f"Text extracted and saved to {output_markdown_file}")