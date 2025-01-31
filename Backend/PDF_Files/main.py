from Microsoft_doc_intelligence_API_and_S3 import extract_text
from fastapi import FastAPI, UploadFile, File, Form
from test_S3 import upload_to_s3  # Importing the S3 upload function from test_S3.py
from Beautiful_Soap_API import *
from lxml_API_S3 import *
#from Microsoft_doc_intelligence_API_and_S3 import *
from Pymupdf_Updated_with_API_and_S3 import *
from Pytesseract_with_API_and_S3 import *
from test_fastapi import *

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the API Router. Go to /docs to test the API"}

@app.post("/extract-to-markdown/")
async def extract_to_markdown(file: UploadFile = File(...)):
    return await extract_pdf(file)  # Calls function from Pymupdf_Updated_with_API_and_S3
@app.post("/parse-html/")
async def parse_html(url: str = Form(...)):
    return await convert_pdf_to_markdown(url)  # Calls function from Beautiful_Soap_API

@app.post("/extract-lxml/")
async def extract_lxml(url: str = Form(...)):
    return await process_webpage(url)  # Calls function from lxml_API_S3

@app.post("/process-doc-intelligence/")
async def process_doc_intelligence(file: UploadFile = File(...)):
    return await extract_text(file)  # Calls function from Microsoft_doc_intelligence_API_and_S3

@app.post("/extract-text-pytesseract/")
async def extract_text_pytesseract(file: UploadFile = File(...)):
    return await extract_ocr(file)  # Calls function from Pytesseract_with_API_and_S3
