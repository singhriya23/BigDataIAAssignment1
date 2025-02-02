from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import pymupdf  # PyMuPDF
import requests
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from urllib.parse import urlparse
import logging
from dotenv import load_dotenv  # ✅ Import dotenv
import uuid
from datetime import datetime

def get_folder_name_from_url(pdf_url):
    """
    Generate a unique folder name based on the original file name, timestamp, and UUID.
    This ensures that each upload is stored in a separate folder, even if the file name is the same.
    """
    parsed_url = urlparse(pdf_url)
    base_name = os.path.splitext(os.path.basename(parsed_url.path))[0]

    # ✅ Add timestamp and UUID to prevent overwriting previous uploads
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]  # Use only first 8 characters for brevity
    unique_folder_name = f"{base_name}_{timestamp}_{unique_id}"
    
    return unique_folder_name

# ✅ Load environment variables from .env file
load_dotenv("env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ✅ AWS S3 Configuration from .env
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files")
S3_WEBPAGES_OBJECT = "Webpages"

# ✅ Initialize S3 client with credentials from .env
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

def download_pdf(pdf_url, output_path):
    try:
        logger.info(f"Downloading PDF from URL: {pdf_url}")
        response = requests.get(pdf_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"PDF downloaded and saved to {output_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {e}")

def pdf_to_markdown(pdf_path, folder_name):
    try:
        logger.info(f"Opening PDF: {pdf_path}")
        doc = pymupdf.open(pdf_path)
        markdown_content = ""
        image_count = 0
        table_count = 0

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            markdown_content += f"\n\n## Page {page_num + 1}\n\n{text}"

            # Extract images
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_name = f"image_{page_num + 1}_{img_index + 1}.{image_ext}"
                image_path = os.path.join("images", image_name)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)

                # ✅ Reload .env before S3 upload
                load_dotenv()

                s3_image_key = f"{S3_WEBPAGES_OBJECT}/{folder_name}/images/{image_name}"
                upload_to_s3(image_path, s3_image_key)
                os.remove(image_path)
                image_count += 1

        return markdown_content, image_count, table_count
    except Exception as e:
        logger.error(f"Error during PDF to Markdown conversion: {e}")
        raise HTTPException(status_code=500, detail=f"Error during PDF to Markdown conversion: {e}")

def upload_to_s3(file_path, s3_key):
    try:
        logger.info(f"Uploading {file_path} to S3 with key {s3_key}")

        # ✅ Reload .env before S3 upload
        load_dotenv()

        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        logger.info(f"Uploaded {file_path} to S3 bucket {S3_BUCKET_NAME} with key {s3_key}")
    except FileNotFoundError:
        logger.error(f"The file {file_path} was not found.")
    except (NoCredentialsError, PartialCredentialsError):
        logger.error("Credentials not available for S3 upload.")
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")

def get_folder_name_from_url(pdf_url):
    parsed_url = urlparse(pdf_url)
    base_name = os.path.splitext(os.path.basename(parsed_url.path))[0]
    return base_name

@app.post("/convert-pdf-to-markdown/", response_class=PlainTextResponse)
async def convert_pdf_to_markdown(pdf_url: str):
    pdf_path = "downloaded.pdf"
    
    try:
        # ✅ Download the PDF
        download_pdf(pdf_url, pdf_path)
        
        # ✅ Get a unique folder name to avoid overwriting previous files
        folder_name = get_folder_name_from_url(pdf_url)
        logger.info(f"Unique folder name: {folder_name}")
        
        # ✅ Convert the PDF to Markdown and extract images/tables
        markdown_content, image_count, table_count = pdf_to_markdown(pdf_path, folder_name)

        # ✅ Save the Markdown file to S3
        markdown_name = f"{folder_name}.md"
        markdown_path = os.path.join("markdown", markdown_name)
        os.makedirs(os.path.dirname(markdown_path), exist_ok=True)
        with open(markdown_path, "w") as md_file:
            md_file.write(markdown_content)

        # ✅ Use the unique folder name for S3 storage
        s3_markdown_key = f"{S3_WEBPAGES_OBJECT}/{folder_name}/{markdown_name}"
        upload_to_s3(markdown_path, s3_markdown_key)
        os.remove(markdown_path)
        
        # ✅ Clean up the downloaded PDF file
        os.remove(pdf_path)
        
        return f"Conversion successful! Extracted {image_count} images and {table_count} tables. Files saved in S3 under '{S3_WEBPAGES_OBJECT}/{folder_name}'."
    
    except Exception as e:
        logger.error(f"Error in convert_pdf_to_markdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# To run the FastAPI app, use the following command:
# uvicorn script_name:app --reload
