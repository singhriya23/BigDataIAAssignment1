import streamlit as st
import requests
import os
import boto3
import pymupdf  # PyMuPDF
from io import BytesIO
import asyncio
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File

# Initialize FastAPI app
app = FastAPI()

# Ensure the directory exists
BASE_DIR = Path(os.getcwd()) / "PDF_Files"
BASE_DIR.mkdir(parents=True, exist_ok=True)

# S3 Upload Function
def upload_to_s3(file_path: str, s3_key: str):
    s3 = boto3.client('s3', region_name='us-east-2')
    try:
        s3.upload_file(Filename=file_path, Bucket='document-parsed-files', Key=s3_key)
        return f"s3://document-parsed-files/{s3_key}"
    except Exception as e:
        raise Exception(f"Error uploading file to S3: {e}")

# PDF Extraction Function
def extract_to_markdown(file: UploadFile):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file_name = f"Extracted_{timestamp}.md"
    markdown_file_path = BASE_DIR / markdown_file_name
    
    pdf_content =  file.read()
    pdf_file = BytesIO(pdf_content)
    pdf_document = pymupdf.open(stream=pdf_file, filetype="pdf")
    
    with open(markdown_file_path, "w", encoding="utf-8") as markdown_file:
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text("text")
            markdown_file.write(f"# Page {page_num + 1}\n")
            markdown_file.write(text + "\n\n---\n\n")
    
    pdf_document.close()
    s3_key = f"PDF_Files/{markdown_file_name}"
    
    try:
        s3_url = upload_to_s3(str(markdown_file_path), s3_key)
        return markdown_file_name, s3_url
    except Exception as e:
        return markdown_file_name, str(e)

st.title("Welcome to DocGPT")
st.header("Generate Markdown from PDF and Upload to S3")

dropdown = st.sidebar.selectbox("Select the model", ["PyMupdf", "BeautifulSoup"])

if dropdown == "PyMupdf":
    st.sidebar.write("Upload your PDF file:")
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded_file is not None:
        markdown_file_name, s3_url = extract_to_markdown(uploaded_file)
        
        st.write("### Generated Markdown")
        st.write(f"Markdown File Name: {markdown_file_name}")
        st.write(f"S3 URL: {s3_url}")
        st.success("Markdown file uploaded to S3 successfully!")
        st.download_button("Download Markdown File", markdown_file_name, file_name=markdown_file_name)

elif dropdown == "BeautifulSoup":
    st.sidebar.write("Paste a PDF URL:")
    pdf_url = st.sidebar.text_input("Enter the URL of the PDF")
    if pdf_url:
        pdf_path = "downloaded.pdf"
        response = requests.get(pdf_url)
        if response.status_code == 200:
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            markdown_file_name, s3_url = extract_to_markdown(UploadFile(filename=pdf_path, file=open(pdf_path, "rb")))
            os.remove(pdf_path)
            
            st.write("### Generated Markdown")
            st.write(f"Markdown File Name: {markdown_file_name}")
            st.write(f"S3 URL: {s3_url}")
            st.success("Markdown file uploaded to S3 successfully!")
            st.download_button("Download Markdown File", markdown_file_name, file_name=markdown_file_name)
