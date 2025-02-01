from fastapi import FastAPI, UploadFile, File
import subprocess
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError
from tempfile import NamedTemporaryFile
import os
import shutil  # Add this import
from pathlib import Path

load_dotenv("env")

app = FastAPI()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files")
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

@app.post("/convert_to_markdown/")
async def convert_file_to_markdown(file: UploadFile = File(...)):
    load_dotenv()

    temp_file_path = None  # Initialize the variable
    markdown_output_path = None  # Initialize the variable

    try:
        # Use a temporary file for conversion
        with NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            # Write the uploaded file content to the temporary file
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        # Define the output Markdown file name
        markdown_output_filename = f"{Path(file.filename).stem}.md"

        # Use another temporary file for the Markdown output
        with NamedTemporaryFile(delete=False, suffix=f"_{markdown_output_filename}") as markdown_temp_file:
            markdown_output_path = markdown_temp_file.name

            # Run MarkItDown to convert the uploaded file to Markdown
            subprocess.run(
                ["markitdown", temp_file_path],
                stdout=open(markdown_output_path, "w"),
                check=True
            )
        
        pdf_name = os.path.splitext(file.filename)[0]
        pdf_s3_folder = f"{S3_CONVERTED_OBJECT}/{pdf_name}/"
        temp_pdf_path = f"/tmp/{file.filename}"
        with open(temp_pdf_path, "wb") as buffer:
         shutil.copyfileobj(file.file, buffer)

        # Upload the original file to S3
        s3_original_file_path = f"{S3_CONVERTED_OBJECT}/{file.filename}"
        try:
            s3_client.upload_file(temp_file_path, S3_BUCKET_NAME, f"{pdf_s3_folder}{file.filename}")
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

    except subprocess.CalledProcessError as e:
        return {"error": f"Conversion to Markdown failed: {e.stderr}"}
    finally:
        # Clean up temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if markdown_output_path and os.path.exists(markdown_output_path):
            os.unlink(markdown_output_path)