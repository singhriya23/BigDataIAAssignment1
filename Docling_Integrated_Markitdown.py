from fastapi import FastAPI, UploadFile, File
import subprocess
import shutil
from pathlib import Path

app = FastAPI()

UPLOAD_DIR = Path("/Users/kaushikj/Documents/DSA-PYTHON/")

@app.post("/convert/")
async def convert_pdf_to_html(file: UploadFile = File(...)):
    # Save uploaded PDF
    local_pdf_path = UPLOAD_DIR / file.filename
    with local_pdf_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Define output path for Markdown conversion (directly from PDF)
    markdown_output_path = UPLOAD_DIR / f"{local_pdf_path.stem}.md"
    html_output_path = UPLOAD_DIR / f"{local_pdf_path.stem}.html"  # Output path for HTML file

    try:
        # Run Docling to convert PDF to Markdown
        subprocess.run(
            ["docling", str(local_pdf_path), "--to", "md", "--output", str(UPLOAD_DIR)],
            check=True
        )

        # Now the Markdown file is ready, use MarkItDown to convert it to HTML
        with open(html_output_path, "w") as html_file:
            subprocess.run(
                ["markitdown", str(markdown_output_path)],
                stdout=html_file,
                check=True
            )

        return {"message": "Conversion successful", "html_file": str(html_output_path)}

    except subprocess.CalledProcessError as e:
        return {"error": f"Conversion failed: {e.stderr}"}
