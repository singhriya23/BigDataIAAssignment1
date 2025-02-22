from fastapi import FastAPI, File, UploadFile
import pdfplumber
import pytesseract
from PIL import Image
import os
import boto3
import csv
from io import StringIO
from botocore.exceptions import NoCredentialsError

# Set the correct path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# AWS S3 Configuration
S3_BUCKET_NAME = "document-parsed-files"
S3_PDF_OBJECT = "PDF_Files"
s3_client = boto3.client("s3")  # Ensure AWS credentials are configured

app = FastAPI()

def extract_text_with_ocr(pdf_path, image_folder, table_folder, pdf_s3_folder):
    """
    Extracts text from a PDF using OCR, extracts tables, saves images, and uploads to S3.
    """
    md_content = []

    # Ensure directories exist
    os.makedirs(image_folder, exist_ok=True)
    os.makedirs(table_folder, exist_ok=True)

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            print(f"Processing page {page_number} for OCR and table extraction...")

            # Convert page to an image
            page_image = page.to_image(resolution=300).original

            # Perform OCR
            ocr_text = pytesseract.image_to_string(page_image)

            # Save image locally
            image_filename = f"page_{page_number}.png"
            image_path = os.path.join(image_folder, image_filename)
            page_image.save(image_path)

            # Upload image to S3
            s3_image_path = f"{pdf_s3_folder}Images/{image_filename}"
            try:
                s3_client.upload_file(image_path, S3_BUCKET_NAME, s3_image_path)
            except NoCredentialsError:
                print("AWS credentials not found! Skipping image upload.")

            # Extract tables and save as CSV
            tables = page.extract_tables()
            if tables:
                for table_idx, table in enumerate(tables):
                    csv_filename = f"page_{page_number}_table_{table_idx + 1}.csv"
                    csv_path = os.path.join(table_folder, csv_filename)

                    with open(csv_path, "w", newline="") as csvfile:
                        csv_writer = csv.writer(csvfile)
                        csv_writer.writerows(table)

                    # Upload CSV to S3
                    s3_csv_path = f"{pdf_s3_folder}Tables/{csv_filename}"
                    try:
                        s3_client.upload_file(csv_path, S3_BUCKET_NAME, s3_csv_path)
                    except NoCredentialsError:
                        print("AWS credentials not found! Skipping table upload.")

                    # Append table info to Markdown
                    md_content.append(f"### Table from Page {page_number}, Table {table_idx + 1}\n")
                    for row in table:
                        md_content.append(f"| {' | '.join(row)} |")
                    md_content.append("\n")

            # Append OCR text to Markdown
            md_content.append(f"## Page {page_number}\n\n```\n{ocr_text}\n```\n![Extracted Image](s3://{S3_BUCKET_NAME}/{s3_image_path})\n")

    return "\n".join(md_content)

@app.post("/extract-text-pytesseract/")
async def extract_ocr(file: UploadFile = File(...)):
    """
    API endpoint to receive a PDF file, process it using OCR and table extraction, and store results in S3.
    """
    pdf_name = os.path.splitext(file.filename)[0]
    pdf_s3_folder = f"{S3_PDF_OBJECT}/{pdf_name}/"

    # Create local temp paths
    temp_pdf_path = f"/tmp/{file.filename}"
    image_folder = f"/tmp/{pdf_name}_Images"
    table_folder = f"/tmp/{pdf_name}_Tables"

    os.makedirs(image_folder, exist_ok=True)
    os.makedirs(table_folder, exist_ok=True)

    with open(temp_pdf_path, "wb") as buffer:
        buffer.write(file.file.read())

    # Upload original PDF to S3
    try:
        s3_client.upload_file(temp_pdf_path, S3_BUCKET_NAME, f"{pdf_s3_folder}{file.filename}")
    except NoCredentialsError:
        return {"error": "AWS credentials not found. Please configure them properly."}

    # Extract OCR text and tables
    extracted_markdown = extract_text_with_ocr(temp_pdf_path, image_folder, table_folder, pdf_s3_folder)

    # Save extracted content as Markdown file
    output_markdown_file = f"/tmp/{pdf_name}_Extracted_Content.md"
    with open(output_markdown_file, "w", encoding="utf-8") as md_file:
        md_file.write(extracted_markdown)

    # Upload Markdown file to S3
    s3_markdown_path = f"{pdf_s3_folder}Extracted_Content.md"
    s3_client.upload_file(output_markdown_file, S3_BUCKET_NAME, s3_markdown_path)

    return {
        "message": "OCR and table extraction completed and stored in S3!",
        "s3_pdf_path": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}{file.filename}",
        "s3_extracted_markdown": f"s3://{S3_BUCKET_NAME}/{s3_markdown_path}",
        "s3_extracted_images_folder": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}Images/",
        "s3_extracted_tables_folder": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}Tables/"
    }
