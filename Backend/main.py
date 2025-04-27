from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import google.generativeai as genai
import logging
import os
import shutil
import PyPDF2
import io
import uvicorn
from PIL import Image
from openai import OpenAI
from ultralytics import YOLO
from transformers import pipeline

app = FastAPI()

# Configure logging and CORS
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client for PDF summarization
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

# Medical imaging models configuration
MODELS = {
    "brain_tumor": {
        "type": "huggingface",
        "model_name": "shimaGh/Brain-Tumor-Detection",
        "target_size": (224, 224)
    },
    "pneumonia": {
        "type": "huggingface",
        "model_name": "nickmuchi/vit-finetuned-chest-xray-pneumonia",
        "target_size": (224, 224)
    },
    "malaria": {
        "type": "yolo",
        "model_name": "ultralytics/yolov8n.pt",
        "conf_threshold": 0.5,
        "target_size": (640, 640)
    }
}

loaded_models = {}
logger.info("🔄 Loading medical imaging models...")
for disease, config in MODELS.items():
    try:
        if config["type"] == "huggingface":
            loaded_models[disease] = pipeline("image-classification", model=config["model_name"])
        elif config["type"] == "yolo":
            loaded_models[disease] = YOLO(config["model_name"])
        logger.info(f"✅ Loaded model for {disease}")
    except Exception as e:
        logger.error(f"❌ Failed to load model for {disease}: {e}")
        loaded_models[disease] = None
logger.info("🚀 All medical models loaded!")

# Helper functions
def save_temp_image(upload_file: UploadFile):
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, upload_file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return temp_path

def process_image(image_path: str, target_size=(224, 224)):
    try:
        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            return img
    except Exception as e:
        raise ValueError(f"Image processing failed: {e}")

def extract_text_from_pdf(pdf_file: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
        return "\n".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        raise HTTPException(400, "Invalid PDF file")

async def generate_diagnosis(patient_data: dict) -> str:
    prompt = f"""
    Please analyze the following patient information and predict the possible diseases the patient may have,
    along with the likelihood percentage for each condition.
    The results will be presented to a doctor,
    so please ensure that the answer is professional and medically appropriate.

    Patient Data:
    {json.dumps(patient_data, indent=2)}

    Format your answer like:
    Disease 1: XX%
    Disease 2: XX%
    Disease 3: XX%
    """

    # Initialize Google Gemini client
    genai.configure(api_key="AIzaSyCUroQyxF1h6f1ZaPZluKF8ldP-wjVf_bM")  # Replace with your actual API key

    # Create a model for generating content
    model = genai.GenerativeModel('gemini-1.5-pro')

    # Generate the content based on the prompt
    try:
        response = model.generate_content(prompt)
        print(response.text)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini generation error: {str(e)}")
        raise HTTPException(500, "Diagnosis generation failed")

# Combined analysis endpoint
@app.post("/analyze")
async def analyze(
    image_file: UploadFile = File(...),
    pdf_file: UploadFile = File(...),
    disease_type: str = Form(...)
):
    image_path = None
    try:
        # Validate inputs
        if disease_type not in MODELS:
            raise HTTPException(400, "Invalid disease type")
        
        if not image_file.content_type.startswith("image/"):
            raise HTTPException(400, "Invalid image file type")
        
        if pdf_file.content_type != "application/pdf":
            raise HTTPException(400, "Invalid PDF file type")

        # Process medical image
        image_path = save_temp_image(image_file)
        img = process_image(image_path, MODELS[disease_type].get("target_size", (224, 224)))
        
        if MODELS[disease_type]["type"] == "huggingface":
            results = loaded_models[disease_type](img)
            top_result = results[0]
            label = str(top_result["label"])
            confidence = round(top_result["score"] * 100, 2)
            diagnosis = "Normal" if any(kw in label.lower() for kw in ["no", "normal", "negative"]) else "Infected"
        else:
            results = loaded_models[disease_type].predict(image_path)
            detections = results[0].boxes
            confidence = round(detections.conf.max().item() * 100, 2) if len(detections) > 0 else 0
            diagnosis = "Infected" if len(detections) > 0 else "Normal"

        # Process PDF
        pdf_content = await pdf_file.read()
        pdf_text = extract_text_from_pdf(pdf_content)
        
        # Generate PDF summary using OpenAI
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

        # Combine the data for patient
        patient_data = {
            "medical_imaging": {
                "diagnosis": diagnosis,
                "confidence": f"{confidence}%",
                "model_type": MODELS[disease_type]["type"]
            },
            "document_analysis": {
                "summary": pdf_summary,
                "page_count": len(PyPDF2.PdfReader(io.BytesIO(pdf_content)).pages),
                "file_name": pdf_file.filename
            }
        }

        # Generate diagnosis based on the patient data
        generated_diagnosis = await generate_diagnosis(patient_data)

        return JSONResponse(content={
            "medical_imaging": patient_data["medical_imaging"],
            "document_analysis": patient_data["document_analysis"],
            "generated_diagnosis": {
                "text": generated_diagnosis  
            }
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(500, "Analysis failed")
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8123)
