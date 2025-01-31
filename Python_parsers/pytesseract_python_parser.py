import os
import pdfplumber
from PIL import Image
import pytesseract

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

def extract_text_with_ocr(pdf_path, output_md_file):
    """
    Extracts text from a PDF using OCR and saves it as a Markdown file.
    """
    md_content = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            print(f"Processing page {page_number} for OCR...")

            # Convert page to an image (in-memory processing)
            page_image = page.to_image(resolution=300).original
            
            # Perform OCR using pytesseract
            ocr_text = pytesseract.image_to_string(page_image)

            # Append formatted text to markdown content
            md_content.append(f"## Page {page_number}\n\n```\n{ocr_text}\n```\n")

    # Save extracted text to Markdown file
    with open(output_md_file, "w", encoding="utf-8") as md_file:
        md_file.write("\n".join(md_content))

    print(f"OCR text extracted and saved to {output_md_file}")

def extract_tables_from_pdf(pdf_path, output_md_file):
    """
    Extracts tables from a PDF using pdfplumber and saves them as a Markdown table.
    """
    md_content = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if tables:
                md_content.append(f"## Tables from Page {page_number}\n")
                for table_index, table in enumerate(tables, start=1):
                    md_content.append(f"### Table {table_index}\n")
                    md_content.append("| " + " | ".join(["Column"] * len(table[0])) + " |")
                    md_content.append("|" + " --- |" * len(table[0]))

                    for row in table:
                        cleaned_row = [str(cell) if cell is not None else "" for cell in row]
                        md_content.append("| " + " | ".join(cleaned_row) + " |")

                    md_content.append("\n")

    # Save extracted tables to Markdown file
    with open(output_md_file, "w", encoding="utf-8") as md_file:
        md_file.write("\n".join(md_content))

    print(f"Tables extracted and saved to {output_md_file}")

def extract_images_from_pdf(pdf_path, output_dir):
    """
    Extracts embedded images from a PDF using pdfplumber and saves them to an output directory.
    """
    os.makedirs(output_dir, exist_ok=True)

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for img_index, img in enumerate(page.images, start=1):
                x0, top, x1, bottom = img["x0"], img["top"], img["x1"], img["bottom"]
                
                # Extract the image from the PDF
                extracted_img = page.crop((x0, top, x1, bottom)).to_image()
                
                # Save the extracted image
                image_path = os.path.join(output_dir, f"page_{page_number}_image_{img_index}.png")
                extracted_img.save(image_path, format="PNG")
                print(f"Saved image from Page {page_number}, Image {img_index} to {image_path}")

    print(f"All images extracted and saved to {output_dir}")

def main(pdf_path, output_dir):
    # Define output files
    output_md_text_file = os.path.join(output_dir, "ocr_extracted_text.md")
    output_md_table_file = os.path.join(output_dir, "extracted_tables.md")
    image_output_dir = os.path.join(output_dir, "images")

    os.makedirs(output_dir, exist_ok=True)

    print("Extracting text using OCR...")
    extract_text_with_ocr(pdf_path, output_md_text_file)

    print("Extracting tables...")
    extract_tables_from_pdf(pdf_path, output_md_table_file)

    print("Extracting images...")
    extract_images_from_pdf(pdf_path, image_output_dir)

if __name__ == "__main__":
    pdf_path = "/Users/riyasingh/Desktop/PDF_PARSER/PDF_Files/Assignment(1)-Research_on_LLMs.pdf"
    output_dir = "/Users/riyasingh/Desktop/PDF_PARSER/Python_parsers/Output_files/Output_pytesseract"
    main(pdf_path, output_dir)
