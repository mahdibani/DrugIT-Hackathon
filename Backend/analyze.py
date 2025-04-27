from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
import io
import os
import shutil
import PyPDF2
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import loaded_models, MODELS
from utils import save_temp_image, process_image

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client for PDF summarization
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

router = APIRouter()

def extract_text_from_pdf(pdf_file: bytes) -> str:
    """Extract text content from a PDF file"""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
        return "\n".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        raise HTTPException(400, "Invalid PDF file")

@router.post("/analyze")
async def analyze(
    image_file: UploadFile = File(...),
    pdf_file: UploadFile = File(...),
    disease_type: str = Form(...)
):
    """Analyze medical image and PDF document for disease detection"""
    image_path = None
    try:
        if disease_type not in MODELS:
            raise HTTPException(400, f"Invalid disease type: {disease_type}")
        
        if not image_file.content_type.startswith("image/"):
            raise HTTPException(400, f"Invalid image file type: {image_file.content_type}")
        
        if pdf_file.content_type != "application/pdf":
            raise HTTPException(400, f"Invalid PDF file type: {pdf_file.content_type}")

        # Process image
        image_path = save_temp_image(image_file)
        img = process_image(image_path, MODELS[disease_type].get("target_size", (224, 224)))

        # Process different model types
        if MODELS[disease_type]["type"] == "huggingface":
            results = loaded_models[disease_type](img)
            top_result = results[0]
            label = str(top_result["label"])
            confidence = round(top_result["score"] * 100, 2)
            diagnosis = "Normal" if any(kw in label.lower() for kw in ["no", "normal", "negative"]) else "Infected"
        elif MODELS[disease_type]["type"] in ["yolo_local", "yolo"]:
            results = loaded_models[disease_type].predict(image_path)
            detections = results[0].boxes
            confidence = round(detections.conf.max().item() * 100, 2) if len(detections) > 0 else 0
            diagnosis = "Infected" if len(detections) > 0 else "Normal"
        else:
            raise HTTPException(400, f"Unsupported model type for {disease_type}")

        # Process PDF
        pdf_content = await pdf_file.read()
        pdf_text = extract_text_from_pdf(pdf_content)

        # Generate PDF summary using LLM
        summary_prompt = f"""Analyze this medical document and provide a structured summary:
        {pdf_text[:15000]}
        
        Provide the summary in this format:
        - Patient Overview
        - Key Clinical Findings
        - Treatment History
        - Recommended Actions"""

        llm_response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=[
                {"role": "system", "content": "Expert medical document analyst"},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.2
        )
        pdf_summary = llm_response.choices[0].message.content.strip()

        # Return analysis results
        return JSONResponse(content={
            "medical_imaging": {
                "diagnosis": diagnosis,
                "confidence": f"{confidence}%",
                "model_type": disease_type
            },
            "document_analysis": {
                "summary": pdf_summary,
                "page_count": len(PyPDF2.PdfReader(io.BytesIO(pdf_content)).pages),
                "file_name": pdf_file.filename
            }
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

@router.get("/health")
async def health_check():
    """Health check endpoint for API status"""
    return {"status": "ok", "module": "analyze"}