import requests
from bs4 import BeautifulSoup
import json
import fitz  # PyMuPDF
import os

# Function to download a PDF
def download_pdf(pdf_url, output_path):
    try:
        response = requests.get(pdf_url, stream=True)
        if response.status_code == 200 and "application/pdf" in response.headers.get("Content-Type", ""):
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {output_path}")
            return True
        else:
            print(f"Failed to download PDF: {pdf_url}")
            return False
    except Exception as e:
        print(f"Error downloading {pdf_url}: {e}")
        return False

# Function to convert a PDF to Markdown with images
def pdf_to_markdown_with_images(pdf_path, output_dir):
    try:
        doc = fitz.open(pdf_path)
        markdown_content = ""
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # Extract text from the page
            text = page.get_text("text")
            markdown_content += f"\n\n## Page {page_num + 1}\n\n{text}"

            # Extract images from the page
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"{base_filename}-page-{page_num + 1}-img-{img_index + 1}.{image_ext}"

                # Save the image in the output directory
                image_path = os.path.join(output_dir, image_filename)
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)

                # Embed the image in the Markdown file
                markdown_content += f"\n\n![Image {img_index + 1}](./{image_filename})"

        return markdown_content
    except Exception as e:
        print(f"Error converting {pdf_path} to Markdown with images: {e}")
        return ""

# URL for recent Machine Learning topics on arXiv
url = "https://arxiv.org/list/stat.ML/recent"

# Scraping the website
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find all article entries
articles = soup.find_all("dd")
articleInfo = []

for article in articles:
    title_tag = article.find_previous_sibling("dt").find("div", class_="list-title")
    rawTopic = title_tag.text if title_tag else "No title"
    topic = rawTopic.replace("\n", "").strip()

    abstract_tag = article.find("p", class_="mathjax")
    rawFullAbstract = abstract_tag.text if abstract_tag else "No abstract"
    fullAbstract = rawFullAbstract.replace("\n", "").strip()

    pdf_tag = article.find_previous_sibling("dt").find("a", title="Download PDF")
    pdfURL = pdf_tag['href'] if pdf_tag else "No PDF"
    pdfURL = requests.compat.urljoin(url, pdfURL)

    authors_tag = article.find("div", class_="list-authors")
    authors = [a.text for a in authors_tag.find_all("a")] if authors_tag else []

    arxivArticle = {
        "Topic": topic,
        "Abstract": fullAbstract,
        "PDF": pdfURL,
        "Authors": authors
    }

    articleInfo.append(arxivArticle)

# Save the extracted articles to a JSON file
with open("arxiv.json", "w") as jsonFile:
    json.dump(articleInfo, jsonFile, indent=4)

# Process each article and download PDFs
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

for article in articleInfo:
    pdf_url = article.get("PDF")
    if pdf_url and pdf_url != "No PDF":
        pdf_filename = pdf_url.split("/")[-1]
        pdf_path = os.path.join(output_dir, pdf_filename)
        markdown_filename = pdf_filename.replace(".pdf", ".md")
        markdown_path = os.path.join(output_dir, markdown_filename)

        # Download the PDF
        if download_pdf(pdf_url, pdf_path):
            # Convert the PDF to Markdown with images
            markdown_content = pdf_to_markdown_with_images(pdf_path, output_dir)

            # Save the Markdown content to a file
            with open(markdown_path, "w") as md_file:
                md_file.write(markdown_content)
                print(f"Converted and saved: {markdown_path}")

print("All PDFs processed and converted to Markdown with images.")
