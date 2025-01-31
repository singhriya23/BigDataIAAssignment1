import os
from google.cloud import documentai_v1beta3 as documentai

# Initialize the Document AI client
client = documentai.DocumentProcessorServiceClient()

# Path to your file
file_path = "/Users/riyasingh/Desktop/PDF_PARSER/PDF_Files/Assignment(1)-Research_on_LLMs.pdf"

# Load the file into memory
with open(file_path, "rb") as document_file:
    document_content = document_file.read()

# Define project and processor details (Replace with actual values)
PROJECT_ID = "starry-tracker-449020-f2"
PROCESSOR_ID = "cb87f2d0eca6ae6a"
LOCATION = "us"  # or "eu", depending on your setup

# Configure the document request
raw_document = documentai.RawDocument(content=document_content, mime_type="application/pdf")

# Create the request object
request = documentai.ProcessRequest(
    name=f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}",
    raw_document=raw_document,
)

# Process the document
response = client.process_document(request=request)

# Extracting text content
document = response.document
text = document.text  # Extracted text from the document

# Save extracted text to a file
output_text_file = "/Users/riyasingh/Desktop/PDF_PARSER/Python_parsers/Output_files/Output_GCP/extracted_text.txt"
with open(output_text_file, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Text extracted and saved to {output_text_file}")
