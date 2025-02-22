from fastapi import FastAPI, HTTPException
import boto3
import os
from apify_client import ApifyClient
from dotenv import load_dotenv
from fastapi.responses import PlainTextResponse
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv("env")

app = FastAPI()

# Initialize Apify client
client = ApifyClient("apify_api_mvmGFBtCxks7iY3OM7jt02IW5T8cqd2cENI4")

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files-1")
S3_FOLDER_NAME = "Webpages"
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

# Upload function for S3
def upload_to_s3(file_path, s3_key):
    try:
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        print(f"Uploaded {file_path} to S3 bucket {S3_BUCKET_NAME} with key {s3_key}")
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

# Improved function to extract a structured folder name from any URL
def extract_folder_name_from_url(url: str):
    """
    Extracts a meaningful folder name from the URL.
    Uses the domain name and first path segment to create a structured name.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(".", "_")  # Replace dots to avoid folder issues
    path_segments = parsed_url.path.strip("/").split("/")
    
    if path_segments and path_segments[0]:
        folder_name = f"{domain}_{path_segments[0]}"  # Take the first meaningful path segment
    else:
        folder_name = domain  # Use domain if no path exists

    return folder_name

@app.get("/")
async def root():
    return {"message": "Welcome to the Web Scraping API!"}

@app.post("/apify-scrape/")
async def scrape_and_save(url: str):
    try:
        # Extract folder name from URL
        folder_name = extract_folder_name_from_url(url)

        # Define the input for the Apify web scraping actor
        run = client.actor("apify/web-scraper").call(run_input={
            "startUrls": [{"url": url}],  # Use the user-provided URL
            "linkSelector": "a",
            "pageFunction": """async function pageFunction(context) {
                const $ = context.jQuery;
                const pageTitle = $('title').first().text();
                return {
                    url: context.request.url,
                    pageTitle,
                };
            }"""
        })

        # Fetch results and save them to a markdown file
        markdown_content = "# Scraped Data\n\n## Webpage Data\n\n"

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            markdown_content += f"### URL: {item.get('url', 'No URL found')}\n"
            markdown_content += f"**Page Title**: {item.get('pageTitle', 'No title found')}\n"
            markdown_content += "\n" + "-" * 50 + "\n\n"
        
        # Save results to a markdown file
        markdown_filename = "scraped_data.md"
        with open(markdown_filename, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_content)

        # Define the S3 path for the markdown file inside the extracted folder
        s3_key = f"{S3_FOLDER_NAME}/{folder_name}/{markdown_filename}"

        # Upload the markdown file to S3
        upload_to_s3(markdown_filename, s3_key)

        # Clean up: Remove local markdown file after upload
        os.remove(markdown_filename)

        return {"message": f"Scraping successful! Results saved to S3 under '{S3_FOLDER_NAME}/{folder_name}/'."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during scraping: {str(e)}")
