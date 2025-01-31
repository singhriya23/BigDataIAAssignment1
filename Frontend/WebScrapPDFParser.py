import pymupdf  # PyMuPDF
import requests

def download_pdf(pdf_url, output_path):
    response = requests.get(pdf_url)
    with open(output_path, 'wb') as f:
        f.write(response.content)

def pdf_to_markdown(pdf_path):
    doc = pymupdf.open(pdf_path)
    markdown_content = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        markdown_content += f"\n\n## Page {page_num + 1}\n\n{text}"

    return markdown_content

# Example usage
pdf_url = "https://arxiv.org/pdf/2501.12957"
pdf_path = "downloaded.pdf"

# Download the PDF
download_pdf(pdf_url, pdf_path)

# Convert the PDF to Markdown
markdown_content = pdf_to_markdown(pdf_path)

# Save the Markdown content to a file
with open("output.md", "w") as md_file:
    md_file.write(markdown_content)

print("PDF has been converted to Markdown and saved to output.md")