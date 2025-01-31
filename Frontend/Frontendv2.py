import streamlit as st
import requests
import os
import sys
import tempfile
import shutil
#from .download_s3 import download_from_s3  
import pymupdf

BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))


sys.path.append(BACKEND_PATH)
print(sys.path)

from download_to_s3 import download_from_s3 


# FastAPI URLs
FAST_API_URL = "http://localhost:8003/extract-to-markdown/"
DOCLING_API_URL = "http://localhost:8080/convert/"
OCR_API_URL = "http://localhost:8004/extract-ocr/"
MS_DOCS_API_URL = "http://localhost:8005/extract_and_save_text/"

BEAUTIFUL_SOUP_API_URL = "http://localhost:8001/convert-pdf-to-markdown/"
LXML_API_URL = "http://localhost:8002/process-webpage/"

st.title("Welcome to DocParser")
st.header("Generate Markdown from PDF and Upload to S3")

# Sidebar Selection
dropdown = st.sidebar.selectbox("Select the model", ["PyMupdf", "BeautifulSoup", "Docling", "Pytesseract", "LXML","MSDOCS"])

if dropdown == "PyMupdf":
    st.sidebar.write("Upload your PDF file:")
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(FAST_API_URL, files=files)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                st.error(f"Failed to process the file: {data['error']}")
            else:
                markdown_file_path = data["s3_extracted_markdown"]
                s3_folder_path = os.path.dirname(markdown_file_path)  # Folder where files are stored
                
                st.write("### Extracted Markdown Content")
                st.write(f"**S3 Folder Path:** {s3_folder_path}")
                st.success("Markdown file uploaded to S3 successfully!")
                
                # ✅ Button to Download Extracted Folder from S3
                if st.button("Download Extracted Folder"):
                    with st.spinner("Fetching files from S3..."):
                        pdf_name = os.path.splitext(uploaded_file.name)[0]  # Extract PDF name
                        s3_folder_key = f"PDF_Files/{pdf_name}/"  # The folder key in S3
                        local_download_path = os.path.join(tempfile.gettempdir(), pdf_name)  # Temporary path
                        
                        try:
                            # Download folder from S3
                            downloaded_folder = download_from_s3(s3_folder_key, local_download_path)

                            # Create a zip file of the downloaded folder
                            zip_filename = f"{pdf_name}.zip"
                            zip_filepath = os.path.join(tempfile.gettempdir(), zip_filename)
                            shutil.make_archive(zip_filepath.replace(".zip", ""), 'zip', downloaded_folder)

                            # Provide a download button for the zip file
                            with open(zip_filepath, "rb") as f:
                                st.download_button(
                                    label="Download Folder",
                                    data=f,
                                    file_name=zip_filename,
                                    mime="application/zip"
                                )
                        except Exception as e:
                            st.error(f"Error downloading the folder: {e}")

        else:
            st.error(f"Error processing the file. Status Code: {response.status_code}")

elif dropdown == "BeautifulSoup":
    st.sidebar.write("Paste a PDF URL:")
    pdf_url = st.sidebar.text_input("Enter the URL of the PDF")
    
    if pdf_url:
        response = requests.post(BEAUTIFUL_SOUP_API_URL, params={"pdf_url": pdf_url})
        
        if response.status_code == 200:
            st.write("### Conversion Successful")
            st.write(response.text)
            
            # ✅ Button to Download Extracted Folder from S3
            if st.button("Download Extracted Folder"):
                with st.spinner("Fetching files from S3..."):
                    pdf_name = os.path.splitext(os.path.basename(pdf_url))[0]
                    s3_folder_key = f"PDF_Files/{pdf_name}/"  # The folder key in S3
                    local_download_path = os.path.join(tempfile.gettempdir(), pdf_name)  # Temporary path
                    
                    try:
                        downloaded_folder = download_from_s3(s3_folder_key, local_download_path)
                        zip_filename = f"{pdf_name}.zip"
                        zip_filepath = os.path.join(tempfile.gettempdir(), zip_filename)
                        shutil.make_archive(zip_filepath.replace(".zip", ""), 'zip', downloaded_folder)

                        with open(zip_filepath, "rb") as f:
                            st.download_button(
                                label="Download Folder",
                                data=f,
                                file_name=zip_filename,
                                mime="application/zip"
                            )
                    except Exception as e:
                        st.error(f"Error downloading the folder: {e}")

        else:
            st.error(f"Error processing the PDF URL. Status Code: {response.status_code}")

elif dropdown == "Docling":
    st.sidebar.write("Upload your Markdown file:")
    uploaded_file = st.sidebar.file_uploader("Choose a Markdown/Text file", type=["md", "pdf", "txt"])
    
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(DOCLING_API_URL, files=files)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                st.error(f"Failed to process the file: {data['error']}")
            else:
                st.write("### Conversion Successful")
                
                # ✅ Button to Download Extracted Folder from S3
                if st.button("Download Extracted Folder"):
                    pdf_name = os.path.splitext(uploaded_file.name)[0]
                    s3_folder_key = f"PDF_Files/{pdf_name}/"
                    local_download_path = os.path.join(tempfile.gettempdir(), pdf_name)
                    
                    try:
                        downloaded_folder = download_from_s3(s3_folder_key, local_download_path)
                        zip_filename = f"{pdf_name}.zip"
                        zip_filepath = os.path.join(tempfile.gettempdir(), zip_filename)
                        shutil.make_archive(zip_filepath.replace(".zip", ""), 'zip', downloaded_folder)

                        with open(zip_filepath, "rb") as f:
                            st.download_button(
                                label="Download Folder",
                                data=f,
                                file_name=zip_filename,
                                mime="application/zip"
                            )
                    except Exception as e:
                        st.error(f"Error downloading the folder: {e}")

        else:
            st.error(f"Error processing the file. Status Code: {response.status_code}")

elif dropdown == "Pytesseract":
    st.sidebar.write("Upload your PDF file:")
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file for OCR processing", type=["pdf"])
    
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(OCR_API_URL, files=files)
        
        if response.status_code == 200:
            st.write("### OCR Processing Completed")
            
            # ✅ Button to Download Extracted Folder from S3
            if st.button("Download Extracted Folder"):
                pdf_name = os.path.splitext(uploaded_file.name)[0]
                s3_folder_key = f"PDF_Files/{pdf_name}/"
                local_download_path = os.path.join(tempfile.gettempdir(), pdf_name)
                
                try:
                    downloaded_folder = download_from_s3(s3_folder_key, local_download_path)
                    zip_filename = f"{pdf_name}.zip"
                    zip_filepath = os.path.join(tempfile.gettempdir(), zip_filename)
                    shutil.make_archive(zip_filepath.replace(".zip", ""), 'zip', downloaded_folder)

                    with open(zip_filepath, "rb") as f:
                        st.download_button(
                            label="Download Folder",
                            data=f,
                            file_name=zip_filename,
                            mime="application/zip"
                        )
                except Exception as e:
                    st.error(f"Error downloading the folder: {e}")
elif dropdown == "MSDOCS":
    st.sidebar.write("Upload your PDF file:")
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(MS_DOCS_API_URL, files=files)

        if response.status_code == 200:
            data = response.text  # Response message with S3 folder path
            pdf_name = os.path.splitext(uploaded_file.name)[0]  # Extract PDF name
            s3_folder_key = f"PDF_Files/{pdf_name}/"  # Folder key in S3

            st.write("### Extraction Completed!")
            st.write(data)
            st.success("Files uploaded to S3 successfully!")

            # ✅ Button to Download Extracted Folder from S3
            if st.button("Download Extracted Folder"):
                with st.spinner("Fetching files from S3..."):
                    local_download_path = os.path.join(tempfile.gettempdir(), pdf_name)  # Temporary local path

                    try:
                        # Download folder from S3
                        downloaded_folder = download_from_s3(s3_folder_key, local_download_path)

                        # Create ZIP archive
                        zip_filename = f"{pdf_name}.zip"
                        zip_filepath = os.path.join(tempfile.gettempdir(), zip_filename)
                        shutil.make_archive(zip_filepath.replace(".zip", ""), 'zip', downloaded_folder)

                        # Provide a download button for the ZIP file
                        with open(zip_filepath, "rb") as f:
                            st.download_button(
                                label="Download Folder",
                                data=f,
                                file_name=zip_filename,
                                mime="application/zip"
                            )
                    except Exception as e:
                        st.error(f"Error downloading the folder: {e}")

        else:
            st.error(f"Error processing the file. Status Code: {response.status_code}")
        

        
        
