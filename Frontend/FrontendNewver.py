import streamlit as st
import requests
import os
from test_S3 import upload_to_s3  
import boto3

from dotenv import load_dotenv

st.title("Welcome to DocGPT API Frontend")
st.header("Choose a function to process your document")

BASE_API_URL = "http://localhost:8000"
S3_BUCKET_NAME = "document-parsed-files-1"
S3_PDF_OBJECT = "PDF_Files"

load_dotenv(dotenv_path="env")

# S3 Configuration
S3_BUCKET_NAME = "document-parsed-files-1"
S3_FOLDER_PATH = "PDF_Files"

# AWS Credentials from Env
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

dropdown = st.sidebar.selectbox("Select the API endpoint", [
    "PyMuPDF",
    "BeautifulSoup",
    "Extract LXML",
    "MS Docs",
    "PyTesseract",
    "APIFY",
    
    "MarkItDown"
])

if dropdown == "PyMuPDF":
    st.sidebar.write("Upload a PDF file:")
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}  
        response = requests.post(f"{BASE_API_URL}/extract-pdf/", files=files)

        if response.status_code == 200:
            data = response.json()
            st.write("### Extracted Markdown Content")
            markdown_content = data.get("markdown_content", "")
            preview_length = min(1000, len(markdown_content))  
            st.text_area("Markdown Preview", markdown_content[:preview_length] + "...", height=300)

            # Extract filename (without extension) for S3 folder retrieval
            file_name = os.path.splitext(uploaded_file.name)[0]  

            st.write(f"📂 **Processing Folder in S3:** `{S3_BUCKET_NAME}/{S3_FOLDER_PATH}/{file_name}/`")  

            # Generate S3 Download URL for the folder
            if st.button("Download Full Processed Folder"):
                folder_prefix = f"{S3_FOLDER_PATH}/{file_name}/"
                
                try:
                    # List all objects inside the folder
                    objects = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=folder_prefix)

                    if "Contents" not in objects:
                        st.error("❌ No files found in S3. Check if the folder exists.")
                    else:
                        zip_file_name = f"{file_name}.zip"
                        local_zip_path = f"./{zip_file_name}"

                        # Download all files and zip them locally
                        import zipfile
                        with zipfile.ZipFile(local_zip_path, "w") as zipf:
                            for obj in objects["Contents"]:
                                key = obj["Key"]
                                file_name_in_s3 = key.split("/")[-1]
                                local_file_path = f"./{file_name_in_s3}"

                                # Download each file
                                s3_client.download_file(S3_BUCKET_NAME, key, local_file_path)
                                zipf.write(local_file_path, arcname=file_name_in_s3)
                                os.remove(local_file_path)  # Cleanup downloaded files

                        st.success(f"✅ Folder '{file_name}' downloaded successfully!")

                        # Offer the ZIP file for download
                        with open(local_zip_path, "rb") as f:
                            st.download_button(label="Download Folder as ZIP", data=f, file_name=zip_file_name)

                        os.remove(local_zip_path)  # Cleanup ZIP after download

                except Exception as e:
                    st.error(f"❌ Failed to download from S3: {str(e)}")

        else:
            st.error("❌ Failed to process the file. Please try again.")

elif dropdown == "BeautifulSoup":
    st.sidebar.write("Enter the URL of the PDF:")
    url = st.sidebar.text_input("Enter the webpage URL", key="beautifulsoup_url")

    if url:
        response = requests.post(f"{BASE_API_URL}/parse-html/", data={"url": url})

        if response.status_code == 200:
            try:
                # ✅ Ensure response is parsed as JSON
                data = response.json()
                
                # ✅ Check if the response is a dictionary before calling `.get()`
                if isinstance(data, dict):
                    content_preview = data.get("parsed_html", "No extracted content available.")
                else:
                    content_preview = str(data)  # ✅ Convert response to string if it's not a dictionary

                st.write("### Extracted HTML Content")
                preview_length = min(1000, len(content_preview))
                st.text_area("Content Preview", content_preview[:preview_length] + "...", height=300)

                # Extract filename (from URL) for S3 folder retrieval
                file_name = os.path.splitext(os.path.basename(url))[0]  

                st.write(f"📂 **Processing Folder in S3:** `{S3_BUCKET_NAME}/Webpages/{file_name}/`")  

                # ✅ Generate S3 Download URL for the folder
                if st.button("Download Full Processed Folder"):
                    folder_prefix = f"Webpages/{file_name}/"
                    
                    try:
                        # ✅ List all objects inside the folder
                        objects = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=folder_prefix)

                        if "Contents" not in objects:
                            st.error("❌ No files found in S3. Check if the folder exists.")
                        else:
                            zip_file_name = f"{file_name}.zip"
                            local_zip_path = f"./{zip_file_name}"

                            # ✅ Download all files and zip them locally
                            import zipfile
                            with zipfile.ZipFile(local_zip_path, "w") as zipf:
                                for obj in objects["Contents"]:
                                    key = obj["Key"]
                                    file_name_in_s3 = key.split("/")[-1]
                                    local_file_path = f"./{file_name_in_s3}"

                                    # ✅ Download each file from S3
                                    s3_client.download_file(S3_BUCKET_NAME, key, local_file_path)
                                    zipf.write(local_file_path, arcname=file_name_in_s3)
                                    os.remove(local_file_path)  # Cleanup downloaded files

                            st.success(f"✅ Folder '{file_name}' downloaded successfully!")

                            # ✅ Offer the ZIP file for download
                            with open(local_zip_path, "rb") as f:
                                st.download_button(label="Download Folder as ZIP", data=f, file_name=zip_file_name)

                            os.remove(local_zip_path)  # Cleanup ZIP after download

                    except Exception as e:
                        st.error(f"❌ Failed to download from S3: {str(e)}")

            except Exception as e:
                st.error(f"❌ Error while processing API response: {str(e)}")

        else:
            st.error(f"❌ Failed to process the file. Server Response: {response.text}")

















elif dropdown == "Extract LXML":
    url = st.sidebar.text_input("Enter the URL", key="lxml_url")

    # ✅ Ensure session state is properly initialized
    if "zip_file_path" not in st.session_state:
        st.session_state["zip_file_path"] = None  

    if "content_preview" not in st.session_state:
        st.session_state["content_preview"] = None  

    if st.sidebar.button("Process", key="lxml_process") and url:
        response = requests.post(f"{BASE_API_URL}/extract-lxml/", data={"url": url})  # ✅ Fix: Send JSON instead of form data

        if response.status_code == 200:
            try:
                # ✅ Ensure response is parsed as JSON
                data = response.json()

                # ✅ Check if the response is a dictionary before calling `.get()`
                if isinstance(data, dict):
                    st.session_state["content_preview"] = data.get("parsed_lxml", "No extracted content available.")  
                else:
                    st.session_state["content_preview"] = str(data)  # ✅ Convert response to string if it's not a dictionary

                st.success("✅ Successfully extracted content!")

            except Exception as e:
                st.error(f"❌ Error while processing API response: {str(e)}")

        else:
            st.error(f"❌ Failed to process the URL. Server Response: {response.text}")

    # ✅ Show the extracted content without disappearing
    if st.session_state["content_preview"]:
        st.write("### Extracted LXML Content")
        preview_length = min(1000, len(st.session_state["content_preview"]))  
        st.text_area("Content Preview", st.session_state["content_preview"][:preview_length] + "...", height=300)

    # ✅ Extract filename (from URL) for S3 folder retrieval
    file_name = os.path.splitext(os.path.basename(url))[0]

    st.write(f"📂 **Processing Folder in S3:** `{S3_BUCKET_NAME}/Webpages/{file_name}/`")  

    # ✅ Ensure the download button is persistent and does not refresh UI
    if st.button("Download Full Processed Folder", key="download_folder"):
        folder_prefix = f"Webpages/{file_name}/"

        try:
            # ✅ List all objects inside the correct folder
            objects = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=folder_prefix)

            if "Contents" not in objects:
                st.error("❌ No files found in S3. Check if the folder exists.")
            else:
                zip_file_name = f"{file_name}.zip"
                local_zip_path = f"./{zip_file_name}"

                # ✅ Download all files and zip them locally
                import zipfile
                with zipfile.ZipFile(local_zip_path, "w") as zipf:
                    for obj in objects["Contents"]:
                        key = obj["Key"]
                        file_name_in_s3 = key.split("/")[-1]
                        local_file_path = f"./{file_name_in_s3}"

                        # ✅ Fixed `s3_client.download_file()` syntax
                        s3_client.download_file(S3_BUCKET_NAME, key, local_file_path)  # ✅ Corrected syntax

                        zipf.write(local_file_path, arcname=file_name_in_s3)
                        os.remove(local_file_path)  # ✅ Cleanup downloaded files

                st.success(f"✅ Folder '{file_name}' downloaded successfully!")

                # ✅ Store ZIP file path in session state to prevent UI refresh
                st.session_state["zip_file_path"] = local_zip_path  

        except Exception as e:
            st.error(f"❌ Failed to download from S3: {str(e)}")

    # ✅ Keep the download button visible and ensure it works without refreshing the UI
    if "zip_file_path" in st.session_state and st.session_state["zip_file_path"]:
        with open(st.session_state["zip_file_path"], "rb") as f:
            st.download_button(
                label="Download Folder as ZIP",
                data=f,
                file_name=os.path.basename(st.session_state["zip_file_path"])
            )



elif dropdown == "MS Docs":
    uploaded_file = st.sidebar.file_uploader("Upload a Document", type=["pdf", "docx"], key="msdocs_uploader")

    # ✅ Ensure session state is initialized
    if "zip_file_path" not in st.session_state:
        st.session_state.zip_file_path = None  

    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}  
        response = requests.post(f"{BASE_API_URL}/process-doc-intelligence/", files=files)

        if response.status_code == 200:
            try:
                data = response.json()  

                if isinstance(data, dict):
                    content = data.get("processed_content", "No extracted content available.")  
                else:
                    content = response.text  

                st.write("### Document Processed Successfully")
                preview_length = min(1000, len(content))  
                st.text_area("Processed Data", content[:preview_length] + "...", height=300)

                # ✅ Extract filename (without extension) for S3 folder retrieval
                file_name = os.path.splitext(uploaded_file.name)[0]  

                st.write(f"📂 **Processing Folder in S3:** `document-parsed-files-1/PDF_Files/{file_name}/`")  

                # ✅ Correct folder path
                folder_prefix = f"PDF_Files/{file_name}/"

                if st.button("Download Full Processed Folder"):
                    try:
                        # ✅ List all objects inside the correct folder
                        objects = s3_client.list_objects_v2(Bucket="document-parsed-files-1", Prefix=folder_prefix)

                        if "Contents" not in objects:
                            st.error("❌ No files found in S3. Check if the folder exists.")
                        else:
                            zip_file_name = f"{file_name}.zip"
                            local_zip_path = f"./{zip_file_name}"

                            # ✅ Download all files from S3 and zip them locally
                            import zipfile
                            with zipfile.ZipFile(local_zip_path, "w") as zipf:
                                for obj in objects["Contents"]:
                                    key = obj["Key"]
                                    file_name_in_s3 = key.split("/")[-1]
                                    local_file_path = f"./{file_name_in_s3}"

                                    # ✅ Corrected `download_file()` syntax
                                    s3_client.download_file(
                                        "document-parsed-files-1",  # ✅ S3 Bucket Name
                                        key,  # ✅ File Key in S3
                                        local_file_path  # ✅ Local save path
                                    )

                                    zipf.write(local_file_path, arcname=file_name_in_s3)
                                    os.remove(local_file_path)  

                            st.success(f"✅ Folder '{file_name}' downloaded successfully!")

                            # ✅ Store ZIP file path in session state for download
                            st.session_state.zip_file_path = local_zip_path  

                    except Exception as e:
                        st.error(f"❌ Failed to download from S3: {str(e)}")

            except Exception as e:
                st.error(f"❌ Error while processing API response: {str(e)}")

        else:
            st.error(f"❌ Failed to process the document. Server Response: {response.text}")

    # ✅ Ensure the download button remains visible
    if st.session_state.zip_file_path and os.path.exists(st.session_state.zip_file_path):
        with open(st.session_state.zip_file_path, "rb") as f:
            st.download_button(
                label="Download Folder as ZIP",
                data=f,
                file_name=os.path.basename(st.session_state.zip_file_path)
            )




# ---------------------- Fixing PyTesseract Section ----------------------

elif dropdown == "PyTesseract":
    uploaded_file = st.sidebar.file_uploader("Upload an Image (JPG, PNG, TIFF, PDF)", type=["jpg", "png", "tiff", "pdf"], key="pytesseract_uploader")

    if uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}  
        response = requests.post(f"{BASE_API_URL}/extract-text-pytesseract/", files=files)

        if response.status_code == 200:
            try:
                data = response.json()  # Ensure response is JSON

                if isinstance(data, dict):
                    content = data.get("ocr_text", "No extracted text available.")  
                else:
                    content = response.text  # If response is not JSON, fallback to plain text

                st.write("### Extracted OCR Text")
                preview_length = min(1000, len(content))  
                st.text_area("OCR Result", content[:preview_length] + "...", height=300)

                # Extract filename (without extension) for S3 folder retrieval
                file_name = os.path.splitext(uploaded_file.name)[0]  

                st.write(f"📂 **Processing Folder in S3:** `{S3_BUCKET_NAME}/{S3_FOLDER_PATH}/{file_name}/`")  

                # Ensure session state exists
                if "zip_file_path" not in st.session_state:
                    st.session_state.zip_file_path = None  

                # Generate S3 Download URL for the folder
                if st.button("Download Full Processed Folder"):
                    folder_prefix = f"{S3_FOLDER_PATH}/{file_name}/"
                    
                    try:
                        # List all objects inside the folder
                        objects = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=folder_prefix)

                        if "Contents" not in objects:
                            st.error("❌ No files found in S3. Check if the folder exists.")
                        else:
                            zip_file_name = f"{file_name}.zip"
                            local_zip_path = f"./{zip_file_name}"

                            # Download all files and zip them locally
                            import zipfile
                            with zipfile.ZipFile(local_zip_path, "w") as zipf:
                                for obj in objects["Contents"]:
                                    key = obj["Key"]
                                    file_name_in_s3 = key.split("/")[-1]
                                    local_file_path = f"./{file_name_in_s3}"

                                    # Download each file
                                    s3_client.download_file(S3_BUCKET_NAME, key, local_file_path)
                                    zipf.write(local_file_path, arcname=file_name_in_s3)
                                    os.remove(local_file_path)  # Cleanup downloaded files

                            st.success(f"✅ Folder '{file_name}' downloaded successfully!")

                            with open(local_zip_path, "rb") as f:
                             st.download_button(label="Download Folder as ZIP", data=f, file_name=zip_file_name)

                        os.remove(local_zip_path)  # Cleanup ZIP after download

                    except Exception as e:
                     st.error(f"❌ Failed to download from S3: {str(e)}")

                            # Store ZIP file path in session state
                     st.session_state.zip_file_path = local_zip_path  

            except Exception as e:
                        st.error(f"❌ Failed to download from S3: {str(e)}")

            except Exception as e:
                st.error(f"❌ Error while processing API response: {str(e)}")

        else:
            st.error("❌ Failed to extract text from the image.")



elif dropdown == "MarkItDown":
    st.sidebar.write("Upload a document:")
    uploaded_file = st.sidebar.file_uploader("Choose a document", type=["pdf", "docx", "txt"], key="markitdown_uploader")

    if uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}  
        response = requests.post(f"{BASE_API_URL}/convert_to_markdown/", files=files)

        if response.status_code == 200:
            data = response.json()
            st.write("### Extracted Markdown Content")
            markdown_file_path = data.get("s3_markdown_file", "")

            if markdown_file_path:
                st.write(f"**Markdown File Path:** {markdown_file_path}")
                st.success("Document converted to Markdown successfully!")

                # Extract filename (without extension) for S3 folder retrieval
                file_name = os.path.splitext(uploaded_file.name)[0]  

                st.write(f"📂 **Processing Folder in S3:** `{S3_BUCKET_NAME}/{S3_PDF_OBJECT}/{file_name}/`")  

                # Generate S3 Download URL for the folder
                if st.button("Download Full Processed Folder"):
                    folder_prefix = f"{S3_PDF_OBJECT}/{file_name}/"
                    
                    try:
                        # List all objects inside the folder
                        objects = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=folder_prefix)

                        if "Contents" not in objects:
                            st.error("❌ No files found in S3. Check if the folder exists.")
                        else:
                            zip_file_name = f"{file_name}.zip"
                            local_zip_path = f"./{zip_file_name}"

                            # Download all files and zip them locally
                            import zipfile
                            with zipfile.ZipFile(local_zip_path, "w") as zipf:
                                for obj in objects["Contents"]:
                                    key = obj["Key"]
                                    file_name_in_s3 = key.split("/")[-1]
                                    local_file_path = f"./{file_name_in_s3}"

                                    # Download each file
                                    s3_client.download_file(S3_BUCKET_NAME, key, local_file_path)
                                    zipf.write(local_file_path, arcname=file_name_in_s3)
                                    os.remove(local_file_path)  # Cleanup downloaded files

                            st.success(f"✅ Folder '{file_name}' downloaded successfully!")

                            # Offer the ZIP file for download
                            with open(local_zip_path, "rb") as f:
                                st.download_button(label="Download Folder as ZIP", data=f, file_name=zip_file_name)

                            os.remove(local_zip_path)  # Cleanup ZIP after download

                    except Exception as e:
                        st.error(f"❌ Failed to download from S3: {str(e)}")

        else:
            st.error("❌ Failed to process the document. Please try again.")

elif dropdown == "APIFY":
    st.sidebar.write("Enter the URL to scrape:")
    url = st.sidebar.text_input("Enter the webpage URL", key="apify_scraper_url")

    if url:
        response = requests.post(f"{BASE_API_URL}/apify-scrape/",data={"url": url})  # ✅ Fix: Send JSON instead of params

        if response.status_code == 200:
            try:
                # ✅ Ensure response is parsed as JSON
                data = response.json()

                # ✅ Check if the response is a dictionary before calling `.get()`
                if isinstance(data, dict):
                    scrape_status = data.get("message", "Scraping completed!")
                else:
                    scrape_status = str(data)  # ✅ Convert response to string if it's not a dictionary

                st.write("### Scrape Status")
                preview_length = min(1000, len(scrape_status))
                st.text_area("Scrape Log", scrape_status[:preview_length] + "...", height=150)

                st.success("✅ Webpage successfully scraped and uploaded to S3!")

            except Exception as e:
                st.error(f"❌ Error while processing API response: {str(e)}")

        else:
            st.error(f"❌ Failed to scrape the webpage. Server Response: {response.text}")

    # ✅ Extract filename (from URL) for S3 folder retrieval
    file_name = os.path.splitext(os.path.basename(url))[0]

    st.write(f"📂 **Processing Folder in S3:** `{S3_BUCKET_NAME}/Webpages/{file_name}/`")  

    # ✅ Ensure the download button is properly structured
    if st.button("Download Scraped Data"):
        folder_prefix = f"Webpages/{file_name}/"

        try:
            # ✅ List all objects inside the correct folder
            objects = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=folder_prefix)

            if "Contents" not in objects:
                st.error("❌ No files found in S3. Check if the folder exists.")
            else:
                zip_file_name = f"{file_name}.zip"
                local_zip_path = f"./{zip_file_name}"

                # ✅ Download all files and zip them locally
                import zipfile
                with zipfile.ZipFile(local_zip_path, "w") as zipf:
                    for obj in objects["Contents"]:
                        key = obj["Key"]
                        file_name_in_s3 = key.split("/")[-1]
                        local_file_path = f"./{file_name_in_s3}"

                        # ✅ Download each file from S3
                        s3_client.download_file(S3_BUCKET_NAME, key, local_file_path)
                        zipf.write(local_file_path, arcname=file_name_in_s3)
                        os.remove(local_file_path)  # ✅ Cleanup downloaded files

                st.success(f"✅ Scraped data for '{file_name}' downloaded successfully!")

                # ✅ Offer the ZIP file for download
                with open(local_zip_path, "rb") as f:
                    st.download_button(label="Download Scraped Data as ZIP", data=f, file_name=zip_file_name)

                os.remove(local_zip_path)  # ✅ Cleanup ZIP after download

        except Exception as e:
            st.error(f"❌ Failed to download from S3: {str(e)}")
