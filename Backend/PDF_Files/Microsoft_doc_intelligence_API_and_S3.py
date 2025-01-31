from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
import csv
from dotenv import load_dotenv 


load_dotenv("env")


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Extraction API!"}
AZURE_API_KEY = os.getenv("API_KEY")
AZURE_ENDPOINT = os.getenv("ENDPOINT")
if not AZURE_API_KEY or not AZURE_ENDPOINT:
    raise ValueError("Azure credentials missing! Please check your .env file.")
client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_API_KEY)
)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files")
S3_PDF_FILES_OBJECT = "PDF_Files"
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

def convert_to_markdown(extracted_text, page_number):
    markdown_text = f"## Page {page_number}\n\n"  
    for line in extracted_text:
        markdown_text += f"{line}\n"  
    return markdown_text

def upload_to_s3(file_path, s3_key):
    
    try:
        load_dotenv()
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        print(f"Uploaded {file_path} to S3 bucket {S3_BUCKET_NAME} with key {s3_key}")
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except (NoCredentialsError, PartialCredentialsError):
        print("AWS credentials not available! Please check your .env file.")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

@app.post("/extract-text/", response_class=PlainTextResponse)
async def extract_text(file: UploadFile = File(...)):

    try:
        temp_pdf_path = f"temp_{file.filename}"
        with open(temp_pdf_path, "wb") as buffer:
            buffer.write(await file.read())
        with open(temp_pdf_path, "rb") as file_buffer:
            poller = client.begin_analyze_document(
                model_id="prebuilt-document",
                document=file_buffer
            )
            result = poller.result()

      
        pdf_name = os.path.splitext(file.filename)[0]  
        s3_base_folder = f"{S3_PDF_FILES_OBJECT}/{pdf_name}/"  

       
        full_markdown_content = "# Extracted Content\n\n" 


        for page_number, page in enumerate(result.pages, start=1):
            extracted_text = [line.content for line in page.lines]  
            page_markdown = convert_to_markdown(extracted_text, page_number)  
            full_markdown_content += page_markdown + "\n\n" 
        markdown_path = f"{pdf_name}.md"
        with open(markdown_path, "w", encoding="utf-8") as file:
            file.write(full_markdown_content)     
        load_dotenv()        
        s3_markdown_key = f"{s3_base_folder}{markdown_path}"
        upload_to_s3(markdown_path, s3_markdown_key)

        s3_images_folder = f"{s3_base_folder}images/"
        for page_number, page in enumerate(result.pages, start=1):
            for image_region in page.selection_marks:
                image_metadata = {
                    "bounding_box": image_region.bounding_box,
                    "confidence": image_region.confidence
                }
                image_metadata_path = f"image_{page_number}_metadata.txt"
                with open(image_metadata_path, "w") as file:
                    file.write(str(image_metadata))
                s3_image_key = f"{s3_images_folder}{image_metadata_path}"
                upload_to_s3(image_metadata_path, s3_image_key)
                os.remove(image_metadata_path)

        s3_tables_folder = f"{s3_base_folder}tables/"
        for table_idx, table in enumerate(result.tables, start=1):
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.content)
                table_data.append(row_data)
            table_path = f"table_{table_idx}.csv"
            with open(table_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(table_data)
            
        
            load_dotenv()

            s3_table_key = f"{s3_tables_folder}{table_path}"
            upload_to_s3(table_path, s3_table_key)
            os.remove(table_path)      
        os.remove(temp_pdf_path)
        os.remove(markdown_path)
        return f"Processing successful! Files saved to S3 under '{s3_base_folder}'."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the PDF: {str(e)}")


