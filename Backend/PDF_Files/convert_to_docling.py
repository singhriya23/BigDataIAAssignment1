from fastapi import FastAPI, UploadFile, File
import shutil
from pathlib import Path
import os
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError
from tempfile import NamedTemporaryFile

load_dotenv("env")

app = FastAPI()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files-1")
S3_PDF_OBJECT = "PDF_Files"
S3_CONVERTED_OBJECT = "Converted_Files"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

@app.get("/")
async def root():
    return {"message": "File Converter API is running"}

@app.post("/convert_to_docling_markdown/")
async def convert_file_to_docling_markdown(file: UploadFile = File(...)):
    load_dotenv()

    temp_file_path = None  # Initialize variable
    markdown_output_path = None  # Initialize variable

    try:
        # Use a temporary file to save the uploaded file
        with NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        # Initialize the Docling converter
        converter = DocumentConverter()

        # Convert the uploaded file to Markdown using Docling
        result = converter.convert(temp_file_path)
        markdown_content = result.document.export_to_markdown()

        # Create a temporary file for Markdown output
        with NamedTemporaryFile(delete=False, suffix=f"_{Path(file.filename).stem}.md") as markdown_temp_file:
            markdown_output_path = markdown_temp_file.name

            # Write Markdown content to the file
            with open(markdown_output_path, "w") as md_file:
                md_file.write(markdown_content)

        # Define S3 paths
        pdf_name = os.path.splitext(file.filename)[0]
        pdf_s3_folder = f"{S3_CONVERTED_OBJECT}/{pdf_name}/"

        # Upload the original file to S3
        s3_original_file_path = f"{pdf_s3_folder}{file.filename}"
        try:
            s3_client.upload_file(temp_file_path, S3_BUCKET_NAME, s3_original_file_path)
        except NoCredentialsError:
            return {"error": "AWS credentials not found. Please configure them properly."}

        # Upload the converted Markdown file to S3
        s3_markdown_file_path = f"{pdf_s3_folder}Extracted_Content.md"
        try:
            s3_client.upload_file(markdown_output_path, S3_BUCKET_NAME, s3_markdown_file_path)
        except NoCredentialsError:
            return {"error": "AWS credentials not found. Please configure them properly."}

        return {
            "message": "File converted to Markdown successfully and stored in S3!",
            "s3_original_file": f"s3://{S3_BUCKET_NAME}/{s3_original_file_path}",
            "s3_markdown_file": f"s3://{S3_BUCKET_NAME}/{s3_markdown_file_path}",
        }

    except Exception as e:
        return {"error": f"Conversion using Docling failed: {str(e)}"}
    
    finally:
        # Clean up temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if markdown_output_path and os.path.exists(markdown_output_path):
            os.unlink(markdown_output_path)
