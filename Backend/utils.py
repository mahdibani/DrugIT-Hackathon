from fastapi import UploadFile, HTTPException
from PIL import Image
import PyPDF2
import os
import io
import shutil
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def save_temp_image(upload_file: UploadFile) -> str:
    """
    Save uploaded image to temporary directory
    
    Args:
        upload_file: FastAPI UploadFile object
        
    Returns:
        Path to saved temporary file
    """
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, upload_file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return temp_path

def process_image(image_path: str, target_size: Tuple[int, int] = (224, 224)) -> Image.Image:
    """
    Process image file for model inference
    
    Args:
        image_path: Path to image file
        target_size: Target dimensions for the image
        
    Returns:
        Processed PIL Image object
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            return img
    except Exception as e:
        raise ValueError(f"Image processing failed: {e}")

def extract_text_from_pdf(pdf_file: bytes) -> str:
    """
    Extract text content from PDF file
    
    Args:
        pdf_file: PDF file content as bytes
        
    Returns:
        Extracted text content
    """
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
        return "\n".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        raise HTTPException(400, "Invalid PDF file")

def get_severity_level(diagnosis_status: str, confidence: float) -> str:
    """
    Determine severity level based on diagnosis and confidence
    
    Args:
        diagnosis_status: Diagnosis status (positive/negative)
        confidence: Confidence level (0-100)
        
    Returns:
        Severity level string (severe/moderate/normal)
    """
    if diagnosis_status.lower() == "positive":
        if confidence > 90:
            return "severe"
        return "moderate"
    return "normal"