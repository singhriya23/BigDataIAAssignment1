# Introduction

In this Codelab, you will learn how to build a Streamlit-based frontend for interacting with a document-processing API. This API can process documents using different techniques such as PyMuPDF, BeautifulSoup, LXML, Microsoft Document Intelligence, and PyTesseract.

By the end of this tutorial, you will be able to:

Upload PDFs, images, and DOCX files

Process documents using an API

Display extracted content in Streamlit

Download processed files from S3 storage

# Prerequisites

Before you start, make sure you have the following:

Python (>=3.8)

Installed dependencies:

streamlit boto3

fastapi

# Running the Application

For the backend create an Endpoint for each of the services using Fastapi. For ex PyMuPdf, Doc Intelligence etc.

Once the Backend Endpoints are created, make sure that you route the endpoints in a main.py file.

run the fastapi endpoints..

uvicorn main:app --reload

Then run the Streamlit Application using

Make sure the respective credentials are in env file and do call them wherever required

### Note Do not Commit the env file as it will cause issues.

Streamlit run Frontendnew.py


# Running the application

Select the respective Dropdowns (e.x PymuPdf,Tesseract etc). 

Upload the Respective files and see the output in S3.



