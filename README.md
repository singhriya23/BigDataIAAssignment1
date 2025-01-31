The Repository Contains the Following Files.

Backend -- Contains the Respective Code for FastAPI Endpoints and Respective S3 Functions.

Frontend -- Contains the Streamlit code used for Frontend.

Python Parsers -- Contains the POCs we have developed for the same.

Codelabs Link: https://codelabs-preview.appspot.com/?file_id=1i3SX7f9MV_4QOnY8MV32oV3I9o9Yk8MtxNx7H6rayNk#2


ATTESTATION
WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENT'S WORK IN OUR
ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK

CONTRIBUTION
KAUSHIK - BACKEND DIAGRAMS 33%
RIYA - DEPLOYMENT POCS 33%
ARVIND - FRONTEND(STREAMLIT) AND FRONTEND BACKEND INTEGRATION, DOCUMENTATION.

We have used Pymupdf and Pytesseract to extract data from PDF as text, images, and tables which can be seen in the diagram below.
![Diagrams_Pymupdf_Pytesseract](https://github.com/user-attachments/assets/c8b0f916-eddf-47c0-bcdc-9fa3170189e1)

We have integrated Docling and Markitdown, where we used docling to generate a Markdown file and gave it as input to Markitdown to convert it to HTML format.
![Docling_Markitdown](https://github.com/user-attachments/assets/7e9f33d7-8afe-46d2-a7ce-5737658cb306)

Next, we used Beautiful Soap and Lxml to parse webpages to extract text, tables, and images.
![WebPage_BS4_lxml](https://github.com/user-attachments/assets/c3756502-8db2-4053-8eb3-20446469d125)

All of the above parsing techniques we have used we have made sure that all the files are uploaded to the Amazon S3 bucket after processing, which contains all the extracted data in a folder.

In the frontend part, we have integrated all the parsing techniques as a dropdown so that the user can select his/her preferred choice of document based on the requirement. Integration from frontend and backend is done by using the main.py file which has the addresses of the parsing techniques in the backend. 

We have also included a Download button to save a copy of the parsed files on the User's Computer/System




