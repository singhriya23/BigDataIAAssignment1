import streamlit as st
import requests
import os
from test_S3 import upload_to_s3
from test_fastapi import extract_to_markdown
import pymupdf
from WebScrapPDFParser import download_pdf, pdf_to_markdown  # Import the new functions

st.title("Welcome to DocGPT")
st.header("Generate Markdown from PDF and Upload to S3")

dropdown = st.sidebar.selectbox("Select the model", ["PyMupdf", "BeautifulSoup"])
FAST_API_URL = "http://localhost:8000/extract-to-markdown/"

if dropdown == "PyMupdf":
    st.sidebar.write("Upload your PDF file:")
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}  # Prepare file for API request
        response = requests.post(FAST_API_URL, files=files)
        
        if response.status_code == 200:
            data = response.json()

            if "error" in data:
                st.error(f"Failed to process the file: {data['error']}")
            else:
                markdown_content = data["markdown_content"]
                markdown_file_path = data["markdown_file"]
                s3_url = data["s3_url"]

                st.write("### Extracted Markdown Content")
                st.text_area("Markdown Preview", markdown_content, height=300)  # ✅ Display extracted content
                st.write(f"**Markdown File Path:** {markdown_file_path}")
                st.write(f"**S3 URL:** {s3_url}")
                st.success("Markdown file uploaded to S3 successfully!")
                st.download_button("Download Markdown File", markdown_content, file_name=os.path.basename(markdown_file_path))
        else:
            st.error(f"Error processing the file. Status Code: {response.status_code}")

elif dropdown == "BeautifulSoup":
    st.sidebar.write("Paste a PDF URL:")
    pdf_url = st.sidebar.text_input("Enter the URL of the PDF")
    if pdf_url:
        pdf_path = "downloaded.pdf"
        download_pdf(pdf_url, pdf_path)  # Call the function to download the PDF
        markdown_content = pdf_to_markdown(pdf_path)  # Convert PDF to Markdown
        os.remove(pdf_path)  # Clean up the downloaded file
        
        st.write("### Extracted Markdown Content")
        st.text_area("Markdown Preview", markdown_content, height=300)
        
        # Save Markdown file
        markdown_file_path = "output.md"
        with open(markdown_file_path, "w") as md_file:
            md_file.write(markdown_content)
        
        # ✅ Upload the Markdown file to S3
        s3_key = f"PDF_Files/{os.path.basename(markdown_file_path)}"
        s3_url = upload_to_s3(markdown_file_path, s3_key)
        
        st.success("Markdown file uploaded to S3 successfully!")
        st.write(f"**S3 URL:** {s3_url}")
        st.download_button("Download Markdown File", markdown_content, file_name=os.path.basename(markdown_file_path))
