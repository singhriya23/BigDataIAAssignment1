from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF
import os
import csv
import shutil
import boto3
from botocore.exceptions import NoCredentialsError

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Extraction API!"}


# AWS S3 Configuration
S3_BUCKET_NAME = "document-parsed-files"
S3_PDF_OBJECT = "PDF_Files"
s3_client = boto3.client("s3")  # Make sure AWS credentials are configured

@app.post("/extract-pdf/")
async def extract_pdf(file: UploadFile = File(...)):
    """
    API endpoint to upload a PDF, extract text, tables, and images, 
    and store everything in an S3 bucket.
    """
    pdf_name = os.path.splitext(file.filename)[0]
    pdf_s3_folder = f"{S3_PDF_OBJECT}/{pdf_name}/"

    # Save the uploaded PDF temporarily
    temp_pdf_path = f"/tmp/{file.filename}"
    with open(temp_pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload original PDF to S3
    try:
        s3_client.upload_file(temp_pdf_path, S3_BUCKET_NAME, f"{pdf_s3_folder}{file.filename}")
    except NoCredentialsError:
        return {"error": "AWS credentials not found. Please configure them properly."}

    # Create temporary directories for processing
    output_markdown_file = f"/tmp/{pdf_name}_Extracted_Content.md"
    output_images_folder = f"/tmp/{pdf_name}_Images"
    output_tables_folder = f"/tmp/{pdf_name}_Tables"

    os.makedirs(output_images_folder, exist_ok=True)
    os.makedirs(output_tables_folder, exist_ok=True)

    # Open the PDF document
    pdf_document = fitz.open(temp_pdf_path)

    # Process the PDF
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

                    # Upload table file to S3
                    s3_table_path = f"{pdf_s3_folder}Tables/{table_filename}"
                    s3_client.upload_file(table_filepath, S3_BUCKET_NAME, s3_table_path)

                    # Reference the table file in Markdown
                    markdown_file.write(f"[Extracted Table {table_index+1}](Tables/{table_filename})\n\n")
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
                    
                    # Save the image file locally
                    with open(img_path, "wb") as img_file:
                        img_file.write(img_bytes)

                    # Upload image to S3
                    s3_image_path = f"{pdf_s3_folder}Images/{img_filename}"
                    s3_client.upload_file(img_path, S3_BUCKET_NAME, s3_image_path)

                    # Add image reference to Markdown
                    markdown_file.write(f"![Extracted Image {img_index+1}](Images/{img_filename})\n\n")
            else:
                markdown_file.write("_No images found on this page._\n\n")

            markdown_file.write("---\n\n")  # Markdown separator for pages

    # Close the PDF document
    pdf_document.close()

    # Upload the extracted Markdown file to S3
    s3_markdown_path = f"{pdf_s3_folder}Extracted_Content.md"
    s3_client.upload_file(output_markdown_file, S3_BUCKET_NAME, s3_markdown_path)

    # Return response with S3 locations
    return {
        "message": "PDF processed successfully and stored in S3!",
        "s3_pdf_path": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}{file.filename}",
        "s3_extracted_markdown": f"s3://{S3_BUCKET_NAME}/{s3_markdown_path}",
        "s3_extracted_tables_folder": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}Tables/",
        "s3_extracted_images_folder": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}Images/"
    }

# Run the API using:
# uvicorn script_name:app --reload
