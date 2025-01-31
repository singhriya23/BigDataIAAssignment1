from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from config import API_KEY, ENDPOINT  # Import from config.py

# Initialize the Form Recognizer client
client = DocumentAnalysisClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(API_KEY)
)

def convert_to_markdown(extracted_text, page_number):
    """
    Convert extracted text to markdown format, organizing it page by page.
    """
    markdown_text = f"## Page {page_number}\n\n"  # Add a header for each page

    for line in extracted_text:
        markdown_text += f"{line}\n"  # Add each line of the page to the markdown file
    
    return markdown_text

def extract_and_save_text(pdf_file_path, output_md_path):
    """
    Sends a PDF file to Azure Form Recognizer, extracts text, converts it to markdown,
    and saves it to a .md file, page by page.
    """
    with open(pdf_file_path, "rb") as file:
        poller = client.begin_analyze_document(
            model_id="prebuilt-document",
            document=file
        )
        result = poller.result()

    # Initialize a list to hold all pages' markdown content
    full_markdown_content = "# Extracted Content\n\n"  # Start the markdown file with a title

    # Extract text page by page
    for page_number, page in enumerate(result.pages, start=1):
        extracted_text = [line.content for line in page.lines]  # Extract text for the page
        page_markdown = convert_to_markdown(extracted_text, page_number)  # Convert the page's text to markdown
        full_markdown_content += page_markdown + "\n\n"  # Add the page's content to the full markdown

    # Save the markdown content to a file
    with open(output_md_path, "w", encoding="utf-8") as file:
        file.write(full_markdown_content)

    print(f"Markdown formatted content saved to {output_md_path}")

if __name__ == "__main__":
    pdf_path = "/Users/riyasingh/Desktop/PDF_PARSER/PDF_Files/Text_file(1).pdf"
    output_md = "/Users/riyasingh/Desktop/PDF_PARSER/Python_parsers/Output_files/Output_MSDocs/output.md"
    
    extract_and_save_text(pdf_path, output_md)