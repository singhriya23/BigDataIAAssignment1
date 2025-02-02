from fastapi import FastAPI, UploadFile, File
import shutil
from pathlib import Path
import os
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv 
import boto3

load_dotenv("env")

app = FastAPI()

UPLOAD_DIR = Path(os.getcwd())



@app.get("/")
async def root():
    return {"message": "File Converter API is running"}
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files")  
S3_PDF_OBJECT = "PDF_Files"
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

# Endpoint to convert files to Markdown using Docling
@app.post("/convert_to_docling_markdown/")
async def convert_file_to_docling_markdown(file: UploadFile = File(...)):
    load_dotenv()
    # Save uploaded file
    local_file_path = UPLOAD_DIR / file.filename
    with local_file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Initialize the Docling converter
    converter = DocumentConverter()
    
    try:
        # Convert the uploaded file to Markdown using Docling
        result = converter.convert(str(local_file_path))
        markdown_content = result.document.export_to_markdown()

        # Define output path for the converted Markdown file
        markdown_output_path = UPLOAD_DIR / f"{local_file_path.stem}_docling.md"
        
        # Save the Markdown content to the file
        with open(markdown_output_path, "w") as md_file:
            md_file.write(markdown_content)

        return {"message": "File converted to Markdown successfully using Docling", "markdown_file": str(markdown_output_path)}

    except Exception as e:
        return {"error": f"Conversion using Docling failed: {str(e)}"}
