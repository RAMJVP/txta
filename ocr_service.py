import pytesseract
from PIL import Image
from fastapi import UploadFile

import pytesseract
import shutil

tesseract_path = shutil.which("tesseract")
print(f"Tesseract Path: {tesseract_path}")




def extract_text_from_image(uploaded_file: UploadFile) -> str:
    try:
        # Read the uploaded file as an image
        image = Image.open(uploaded_file.file)
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Error during OCR processing: {e}")
