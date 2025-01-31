from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from config import API_KEY, ENDPOINT  # Import from config.py
import boto3
from botocore.exceptions import NoCredentialsError
import os
import csv

# Initialize the FastAPI app
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Extraction API!"}

# Initialize the Form Recognizer client
client = DocumentAnalysisClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(API_KEY)
)

# Initialize the S3 client
s3_client = boto3.client('s3')
S3_BUCKET_NAME = "document-parsed-files"
S3_PDF_FILES_OBJECT = "PDF_Files"

def convert_to_markdown(extracted_text, page_number):
    """
    Convert extracted text to markdown format, organizing it page by page.
    """
    markdown_text = f"## Page {page_number}\n\n"  # Add a header for each page

    for line in extracted_text:
        markdown_text += f"{line}\n"  # Add each line of the page to the markdown file
    
    return markdown_text

def upload_to_s3(file_path, s3_key):
    """
    Uploads a file to the specified S3 bucket.
    """
    try:
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        print(f"Uploaded {file_path} to S3 bucket {S3_BUCKET_NAME} with key {s3_key}")
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except NoCredentialsError:
        print("Credentials not available for S3 upload.")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

@app.post("/extract-text/", response_class=PlainTextResponse)
async def extract_text(file: UploadFile = File(...)):
    """
    API endpoint to upload a PDF file, extract text using Azure Document Intelligence,
    and save the content in Markdown format, along with images and tables, to S3.
    """
    try:
        # Save the uploaded file temporarily
        temp_pdf_path = f"temp_{file.filename}"
        with open(temp_pdf_path, "wb") as buffer:
            buffer.write(await file.read())

        # Analyze the PDF using Azure Document Intelligence
        with open(temp_pdf_path, "rb") as file_buffer:
            poller = client.begin_analyze_document(
                model_id="prebuilt-document",
                document=file_buffer
            )
            result = poller.result()

        # Create a folder structure in S3 based on the PDF name
        pdf_name = os.path.splitext(file.filename)[0]  # Remove the .pdf extension
        s3_base_folder = f"{S3_PDF_FILES_OBJECT}/{pdf_name}/"  # Folder structure within the PDF_Files object

        # Initialize a list to hold all pages' markdown content
        full_markdown_content = "# Extracted Content\n\n"  # Start the markdown file with a title

        # Extract text page by page
        for page_number, page in enumerate(result.pages, start=1):
            extracted_text = [line.content for line in page.lines]  # Extract text for the page
            page_markdown = convert_to_markdown(extracted_text, page_number)  # Convert the page's text to markdown
            full_markdown_content += page_markdown + "\n\n"  # Add the page's content to the full markdown

        # Save the markdown content to a local file
        markdown_path = f"{pdf_name}.md"
        with open(markdown_path, "w", encoding="utf-8") as file:
            file.write(full_markdown_content)

        # Upload the markdown file to S3
        s3_markdown_key = f"{s3_base_folder}{markdown_path}"
        upload_to_s3(markdown_path, s3_markdown_key)

        # Extract and save images (if any)
        s3_images_folder = f"{s3_base_folder}images/"
        for page_number, page in enumerate(result.pages, start=1):
            for image_region in page.selection_marks:
                # Save image metadata (Document Intelligence does not extract actual images)
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

        # Extract and save tables (if any)
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
            s3_table_key = f"{s3_tables_folder}{table_path}"
            upload_to_s3(table_path, s3_table_key)
            os.remove(table_path)

        # Clean up temporary files
        os.remove(temp_pdf_path)
        os.remove(markdown_path)

        return f"Processing successful! Files saved to S3 under '{s3_base_folder}'."

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the PDF: {str(e)}")

# To run the FastAPI app, use the following command:
# uvicorn your_script_name:app --reload