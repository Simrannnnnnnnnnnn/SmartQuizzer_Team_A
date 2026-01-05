import easyocr
import numpy as np
import cv2
import pypdf
import os
from flask import current_app

# Initialize reader ONCE at module level
reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_image(file):
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    result = reader.readtext(img, detail=0)
    return " ".join(result)

    print("--- OCR EXTRACTED TEXT START---")
    print(content)
    print("---OCR EXTRACTED TEXT END---")
    return content
def extract_text_from_pdf(file):
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    pdf_reader = pypdf.PdfReader(path)
    content = " ".join([p.extract_text() for p in pdf_reader.pages if p.extract_text()])
    os.remove(path)
    return content