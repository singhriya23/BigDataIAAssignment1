from fastapi import FastAPI, UploadFile, File
import pymupdf
from io import BytesIO
import os
from pathlib import Path
from datetime import datetime
from test_S3 import upload_to_s3  # Importing the S3 upload function from test_S3.py

app = FastAPI()

# Ensure the directory exists
BASE_DIR = Path(os.getcwd()) / "PDF_Files"
BASE_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
def root():
    return {"message": "Welcome to PDF to Markdown API. Go to /docs to test the API"}

@app.post("/extract-to-markdown/")
async def extract_to_markdown(file: UploadFile = File(...)):
    # Create a timestamped Markdown file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file_name = f"Extracted_{timestamp}.md"
    markdown_file_path = BASE_DIR / markdown_file_name  

    # Read the uploaded PDF file
    pdf_content = await file.read()
    pdf_file = BytesIO(pdf_content)

    # Open the PDF
    pdf_document = pymupdf.open(stream=pdf_file, filetype="pdf")

    extracted_text = ""  # Store extracted text here

    # Extract text and write to the Markdown file
    with open(markdown_file_path, "w", encoding="utf-8") as markdown_file:
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text("text")
            
            extracted_text += f"# Page {page_num + 1}\n{text}\n\n---\n\n"
            markdown_file.write(f"# Page {page_num + 1}\n{text}\n\n---\n\n")

    pdf_document.close()

    # Now upload the Markdown file to S3
    s3_key = f"PDF_Files/{markdown_file_name}"
    
    try:
        s3_url = upload_to_s3(str(markdown_file_path), s3_key)  
        return {
            "message": "Text extracted, saved as Markdown, and uploaded to S3.",
            "markdown_content": extracted_text,  
            "markdown_file": str(markdown_file_path),
            "s3_url": s3_url
        }
    except Exception as e:
        return {
            "message": "Text extracted and saved as Markdown, but upload to S3 failed.",
            "error": str(e),
            "markdown_content": extracted_text,  
            "markdown_file": str(markdown_file_path)
        }
