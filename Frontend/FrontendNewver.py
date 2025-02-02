import streamlit as st
import requests
import os
from test_S3 import upload_to_s3  

st.title("Welcome to DocGPT API Frontend")
st.header("Choose a function to process your document")

BASE_API_URL = "http://localhost:8000"
S3_BUCKET_NAME = "document-parsed-files"
S3_PDF_OBJECT = "PDF_Files"

dropdown = st.sidebar.selectbox("Select the API endpoint", [
    "PyMuPDF",
    "BeautifulSoup",
    "Extract LXML",
    "MS Docs",
    "PyTesseract"
])

if dropdown == "PyMuPDF":
    st.sidebar.write("Upload a PDF file:")
    uploaded_file = st.sidebar.file_uploader("Upload a PDF file", type=["pdf"], key="pymupdf_uploader")
    if uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}  
        response = requests.post(f"{BASE_API_URL}/extract-pdf/", files=files)
        if response.status_code == 200:
            data = response.json()
            st.write("### Extracted Markdown Content")
            markdown_content = data.get("markdown_content", "")
            preview_length = min(1000, len(markdown_content))  
            st.text_area("Markdown Preview", markdown_content[:preview_length] + "...", height=300)
            
            # Upload to S3
            markdown_file_path = data.get("markdown_file")
            if markdown_file_path:
                s3_key = f"PDF_Files/{os.path.basename(markdown_file_path)}"
                s3_url = upload_to_s3(markdown_file_path, s3_key)
                st.write(f"**S3 URL:** {s3_url}")
                st.success("Markdown file uploaded to S3 successfully!")
                with open(markdown_file_path, "rb") as f:
                    st.download_button(label="Download Processed File", data=f, file_name=os.path.basename(markdown_file_path))
        else:
            st.error("Failed to process the file.")

elif dropdown == "BeautifulSoup":
    url = st.sidebar.text_input("Enter the URL of the PDF", key="beautifulsoup_url")
    if st.sidebar.button("Process", key="beautifulsoup_process") and url:
        response = requests.post(f"{BASE_API_URL}/parse-html/", data={"url": url})
        if response.status_code == 200:
            st.write("### Extracted Content")
            content = response.text
            preview_length = min(1000, len(content))  
            st.text_area("Content Preview", content[:preview_length] + "...", height=300)
            st.download_button(label="Download Processed Content", data=content, file_name="parsed_html.txt")
        else:
            st.error("Failed to process the URL.")

elif dropdown == "Extract LXML":
    url = st.sidebar.text_input("Enter the URL", key="lxml_url")
    if st.sidebar.button("Process", key="lxml_process") and url:
        response = requests.post(f"{BASE_API_URL}/extract-lxml/", data={"url": url})
        if response.status_code == 200:
            st.write("### Extracted LXML Content")
            content = response.text
            preview_length = min(1000, len(content))  
            st.text_area("Content Preview", content[:preview_length] + "...", height=300)
            st.download_button(label="Download Processed Content", data=content, file_name="extracted_lxml.txt")
        else:
            st.error("Failed to process the URL.")

elif dropdown == "MS Docs":
    uploaded_file = st.sidebar.file_uploader("Upload a Document", type=["pdf", "docx"], key="msdocs_uploader")
    if uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}  
        response = requests.post(f"{BASE_API_URL}/process-doc-intelligence/", files=files)
        if response.status_code == 200:
            st.write("### Document Processed Successfully")
            content = response.text
            preview_length = min(1000, len(content))  
            st.text_area("Processed Data", content[:preview_length] + "...", height=300)
            st.download_button(label="Download Processed Document", data=content, file_name="processed_doc.txt")
        else:
            st.error("Failed to process the document.")

elif dropdown == "PyTesseract":
    uploaded_file = st.sidebar.file_uploader("Upload an Image (JPG, PNG, TIFF, PDF)", type=["jpg", "png", "tiff", "pdf"], key="pytesseract_uploader")
    if uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}  
        response = requests.post(f"{BASE_API_URL}/extract-text-pytesseract/", files=files)
        if response.status_code == 200:
            st.write("### Extracted OCR Text")
            content = response.text
            preview_length = min(1000, len(content))  
            st.text_area("OCR Result", content[:preview_length] + "...", height=300)
            st.download_button(label="Download OCR Extracted Text", data=content, file_name="ocr_extracted_text.txt")
        else:
            st.error("Failed to extract text from the image.")