from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import requests
from lxml import html
import pymupdf  # PyMuPDF
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from urllib.parse import urlparse
import logging
from dotenv import load_dotenv  # ✅ Import dotenv

# ✅ Load environment variables from .env file
load_dotenv("env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Extraction API!"}

# ✅ AWS S3 Configuration from .env
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files-1")
S3_WEBPAGES_OBJECT = "Webpages"

# ✅ Initialize S3 client with credentials from .env
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

def get_pdf_links(url, max_pdfs=3):
    """
    Extracts all PDF links from a webpage using LXML.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        logger.info(f"Fetching webpage: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        tree = html.fromstring(response.content)
        pdf_links = tree.xpath("//a[contains(@href, 'pdf')]/@href")  # Extract PDF URLs

        if not pdf_links:
            logger.info("No PDF links found on the webpage.")
            return []

        # Convert relative links to absolute URLs
        pdf_links = [requests.compat.urljoin(url, link) for link in pdf_links]

        return pdf_links[:max_pdfs]  # Return only the first `max_pdfs` links
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve webpage: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to retrieve webpage: {e}")

def download_pdf(pdf_url, output_path):
    """
    Downloads the PDF file from the provided URL.
    """
    try:
        logger.info(f"Downloading PDF from URL: {pdf_url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(pdf_url, headers=headers, stream=True)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        logger.info(f"PDF downloaded and saved to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download PDF: {e}")
        return False

def pdf_to_markdown(pdf_path, folder_name):
    """
    Converts a PDF to Markdown format using PyMuPDF and extracts images/tables.
    """
    try:
        logger.info(f"Opening PDF: {pdf_path}")
        doc = pymupdf.open(pdf_path)
        markdown_content = "# Extracted PDF Content\n\n"
        image_count = 0

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

        return markdown_content, image_count
    except Exception as e:
        logger.error(f"Error during PDF to Markdown conversion: {e}")
        raise HTTPException(status_code=500, detail=f"Error during PDF to Markdown conversion: {e}")

def upload_to_s3(file_path, s3_key):
    """
    Uploads a file to the specified S3 bucket.
    """
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
    """
    Derives a folder name from the PDF URL.
    """
    parsed_url = urlparse(pdf_url)
    return os.path.splitext(os.path.basename(parsed_url.path))[0]

@app.post("/process-webpage/", response_class=PlainTextResponse)
async def process_webpage(url: str, max_pdfs: int = 3):
    """
    Endpoint to process a webpage, extract PDF links, download the PDFs,
    convert them to Markdown, and upload the results to S3.
    """
    try:
        url = url.strip()
        if not url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid URL. Please provide a valid HTTP/HTTPS URL.")

        # ✅ Extract LXML content
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        extracted_text = tree.text_content().strip()

        # ✅ Extract filename from URL and ensure a unique folder is created in S3
        folder_name = get_folder_name_from_url(url)
        logger.info(f"Folder name for storage: {folder_name}")

        # ✅ Save LXML extracted content to a local file before uploading
        lxml_filename = f"{folder_name}_extracted_lxml.txt"
        lxml_filepath = os.path.join("lxml_extracted", lxml_filename)
        os.makedirs(os.path.dirname(lxml_filepath), exist_ok=True)
        
        with open(lxml_filepath, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        # ✅ Upload LXML extracted content to S3
        s3_lxml_key = f"{S3_WEBPAGES_OBJECT}/{folder_name}/{lxml_filename}"
        upload_to_s3(lxml_filepath, s3_lxml_key)
        os.remove(lxml_filepath)

        # ✅ Process PDF links
        pdf_links = get_pdf_links(url, max_pdfs=max_pdfs)
        if not pdf_links:
            raise HTTPException(status_code=400, detail="No PDF links found on the webpage.")

        for idx, pdf_url in enumerate(pdf_links):
            try:
                pdf_path = f"downloaded_{idx+1}.pdf"
                if not download_pdf(pdf_url, pdf_path):
                    logger.error(f"Skipping conversion for: {pdf_url}")
                    continue

                pdf_folder_name = get_folder_name_from_url(pdf_url)
                logger.info(f"Folder name: {pdf_folder_name}")

                markdown_content, image_count = pdf_to_markdown(pdf_path, pdf_folder_name)

                markdown_name = f"{pdf_folder_name}.md"
                markdown_path = os.path.join("markdown", markdown_name)
                os.makedirs(os.path.dirname(markdown_path), exist_ok=True)
                with open(markdown_path, "w", encoding="utf-8") as md_file:
                    md_file.write(markdown_content)

                s3_markdown_key = f"{S3_WEBPAGES_OBJECT}/{pdf_folder_name}/{markdown_name}"
                upload_to_s3(markdown_path, s3_markdown_key)
                os.remove(markdown_path)
                os.remove(pdf_path)

                logger.info(f"Processed PDF: {pdf_url}")
            except Exception as e:
                logger.error(f"Error processing PDF {pdf_url}: {e}")
                continue

        return f"Processing successful! Extracted LXML content and processed {len(pdf_links)} PDFs. Data is saved in S3 under '{S3_WEBPAGES_OBJECT}/{folder_name}/'."

    except Exception as e:
        logger.error(f"Error in process_webpage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run the FastAPI app with:
# uvicorn script_name:app --reload
