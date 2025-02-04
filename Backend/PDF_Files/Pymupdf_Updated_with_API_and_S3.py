from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF
import os
import csv
import shutil
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv  

load_dotenv("env")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Extraction API!"}

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files-1")  
S3_PDF_OBJECT = "PDF_Files"
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

@app.post("/extract-pdf/")
async def extract_pdf(file: UploadFile = File(...)):
    load_dotenv()

    # ✅ Extract filename without extension
    original_filename = file.filename  
    pdf_name, file_extension = os.path.splitext(original_filename)

    # ✅ Ensure correct S3 folder naming
    pdf_s3_folder = f"{S3_PDF_OBJECT}/{pdf_name}/"
    temp_pdf_path = f"/tmp/{original_filename}"  

    # ✅ Save uploaded file locally
    with open(temp_pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # ✅ Upload the original file to the correct folder in S3
        s3_client.upload_file(temp_pdf_path, S3_BUCKET_NAME, f"{pdf_s3_folder}{original_filename}")
    except NoCredentialsError:
        return {"error": "AWS credentials not found. Please configure them properly."}

    # ✅ Upload extracted markdown content to S3
    s3_markdown_path = f"{pdf_s3_folder}Extracted_Content.md"
    s3_client.upload_file(temp_pdf_path, S3_BUCKET_NAME, s3_markdown_path)

    return {
        "message": "PDF processed successfully and stored in S3!",
        "s3_pdf_path": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}{original_filename}",
        "s3_extracted_markdown": f"s3://{S3_BUCKET_NAME}/{s3_markdown_path}",
    }
