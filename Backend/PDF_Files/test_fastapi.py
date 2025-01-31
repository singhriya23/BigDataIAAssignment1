from fastapi import FastAPI, UploadFile, File
import fitz  # PyMuPDF
from io import BytesIO
from pathlib import Path
import os
from datetime import datetime
from test_S3 import upload_to_s3  # Importing the S3 upload function from test_S3.py

app = FastAPI()

# Ensure the directory exists
BASE_DIR = Path(os.getcwd())
BASE_DIR.mkdir(parents=True, exist_ok=True)  # Ensures the directory exists

@app.get("/")
async def root():
    return {"message": "Welcome to PDF to Markdown API. Go to /docs to test the API"}

@app.post("/extract-to-markdown/")
async def extract_to_markdown(file: UploadFile = File(...)):
    # Create a timestamped Markdown file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file_name = f"Extracted_{timestamp}.md"
    markdown_file_path = BASE_DIR / markdown_file_name  # This ensures file is saved in BASE_DIR
    
    # Read the uploaded PDF file
    pdf_content = await file.read()
    pdf_file = BytesIO(pdf_content)
    
    # Open the PDF
    pdf_document = fitz.open(stream=pdf_file, filetype="pdf")
    
    # Extract text and write to the Markdown file
    with open(markdown_file_path, "w", encoding="utf-8") as markdown_file:
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Extract text from the page
            text = page.get_text("text")
            
            # Write the text to the Markdown file
            markdown_file.write(f"# Page {page_num + 1}\n")
            markdown_file.write(text + "\n\n")
            markdown_file.write("---\n\n")  # Markdown separator for pages
    
    # Close the PDF document
    pdf_document.close()

    # Now upload the Markdown file to S3 using the upload_to_s3 function from test_S3.py
    s3_key = f"PDF_Files/{markdown_file_name}"  # Set the S3 key (e.g., directory in S3)
    
    try:
        # Upload the file to S3 and get the S3 URL
        s3_url = upload_to_s3(str(markdown_file_path), s3_key)  # Upload the file to S3
        return {
            "message": "Text extracted, saved as Markdown, and uploaded to S3.",
            "markdown_file": str(markdown_file_path),
            "s3_url": s3_url
        }
    except Exception as e:
        # Handle the error if upload fails
        return {
            "message": "Text extracted and saved as Markdown, but upload to S3 failed.",
            "error": str(e),
            "markdown_file": str(markdown_file_path)
        }
