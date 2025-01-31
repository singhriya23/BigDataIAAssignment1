from PyPDF2 import PdfReader

#reading the file
file_path="/Users/riyasingh/Desktop/PDF_PARSER/Text_file(1).pdf"
read_file=PdfReader(file_path)

#extracting basic text from the file
extracted_text=""
for selected_page in read_file.pages:
    extracted_text +=selected_page.extract_text()

#get the metadata of the pdf_file
meta_data=read_file.metadata

#extract text from a specific page
total_pages = len(read_file.pages)
print(f"Total number of pages:{total_pages}")
input_page=int(input("Enter the page number for extracted text:"))
extrated_page=read_file.pages[input_page-1]
extracted_page_text=extrated_page.extract_text()

#saving pdf to txt file
with open("pypdf_extracted_file.txt","w") as output_text:
    for page_num in range(len(read_file.pages)):
        page = read_file.pages[page_num]
        text = page.extract_text()

        output_text.write(f"--- Page {page_num + 1} ---\n")
        output_text.write(text if text else "No text extracted from this page.\n")
        output_text.write("\n" + "-"*50 + "\n")  # Separator between pages




#output
print("Extracted text")
print(extracted_text)
print("--------------------------------------------------------")
print("Below is the extracted metadata")
print(f"Title: {meta_data.title}")
print(f"Author:{meta_data.author}")
print(f"Subject:{meta_data.subject}")
print(f"Creator: {meta_data.creator}")
#print(f"Creation Date: {meta_data['/CreationDate']}")
print("--------------------------------------------------------")
print(f"Text from Page {input_page}:")
print(extracted_page_text)



