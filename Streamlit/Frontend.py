import streamlit as st
import fitz  # PyMuPDF
import os

st.title("Welcome to DocGPT")
st.header("Generate Markdown from PDF or URL")
st.write("Choose a model in the sidebar to proceed.")

# Sidebar model selection
dropdown = st.sidebar.selectbox("Select the model", ["PyMupdf", "BeautifulSoup"])

if dropdown == "PyMupdf":
    st.sidebar.write("Upload your PDF file:")
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        st.write("File uploaded successfully!")
        st.write("Generating Markdown for the uploaded file...")
        
        # Save the uploaded file temporarily
        temp_pdf_path = f"temp_{uploaded_file.name}"
        with open(temp_pdf_path, "wb") as temp_file:
            temp_file.write(uploaded_file.getbuffer())
        
        # Output Markdown file path
        output_markdown_file = f"{os.path.splitext(uploaded_file.name)[0]}.md"
        
        # Open the PDF and extract text to Markdown
        pdf_document = fitz.open(temp_pdf_path)
        
        with open(output_markdown_file, "w", encoding="utf-8") as markdown_file:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text("text")
                
                markdown_file.write(f"# Page {page_num + 1}\n")
                markdown_file.write(text + "\n\n")
                markdown_file.write("---\n\n")
        
        pdf_document.close()
        
        # Provide a download link for the generated Markdown file
        with open(output_markdown_file, "r", encoding="utf-8") as file:
            markdown_content = file.read()
        
        st.write("### Generated Markdown")
        st.text_area("Markdown Preview", markdown_content, height=300)
        st.download_button("Download Markdown File", markdown_content, file_name=output_markdown_file)
        
        # Cleanup temporary files
        os.remove(temp_pdf_path)

elif dropdown == "BeautifulSoup":
    st.sidebar.write("Paste a link:")
    pasted_link = st.sidebar.text_input("Enter the URL")
    
    if pasted_link:
        st.write("URL received successfully!")
        st.write("Markdown generation from URL is not implemented yet.")
        # Implement BeautifulSoup logic for URL handling here
