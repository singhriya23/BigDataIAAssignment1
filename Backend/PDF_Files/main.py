from convert_to_markitdown import *
from Microsoft_doc_intelligence_API_and_S3 import extract_text
from fastapi import FastAPI, UploadFile, File, Form
from test_S3 import upload_to_s3  
from Beautiful_Soap_API import *
from lxml_API_S3 import *
from Pymupdf_Updated_with_API_and_S3 import *
from Pytesseract_with_API_and_S3 import *
from test_fastapi import *
from apify_webscraping import *
from convert_to_docling import *

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the API Router. Go to /docs to test the API"}

@app.post("/extract-pdf/")
async def extract_to_markdown(file: UploadFile = File(...)):
    return await extract_pdf(file)  
@app.post("/parse-html/")
async def parse_html(url: str = Form(...)):
    return await convert_pdf_to_markdown(url)  

@app.post("/extract-lxml/")
async def extract_lxml(url: str = Form(...)):
    return await process_webpage(url)  

@app.post("/process-doc-intelligence/")
async def process_doc_intelligence(file: UploadFile = File(...)):
    return await extract_text(file)  

@app.post("/extract-text-pytesseract/")
async def extract_text_pytesseract(file: UploadFile = File(...)):
    return await extract_ocr(file) 

@app.post("/convert_to_markdown/")
async def process_markitdown(file: UploadFile = File(...)):
    return await convert_file_to_markdown(file) 

@app.post("/convert_to_docling_markdown/")
async def process_docling(file: UploadFile = File(...)):
    return await convert_file_to_docling_markdown(file)  

@app.post("/apify-scrape/")
async def process_apify(url: str = Form(...)):
    return await scrape_and_save(url) 

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080)) 
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
