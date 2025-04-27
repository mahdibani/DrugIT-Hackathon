from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from ultralytics import YOLO
from PIL import Image
import shutil
import os
import uvicorn
import logging
import PyPDF2
import io
from typing import Dict, Any
from openai import OpenAI

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

def load_diagnosis_database() -> Dict[str, Dict[str, Any]]:
    # Dummy database (You can replace this with your real database or load from file)
    return {
        "brain_tumor": {
            "description": "A tumor in the brain.",
            "symptoms": ["Headaches", "Seizures", "Nausea", "Vision problems", "Cognitive difficulties"],
            "treatment": ["Surgery", "Radiation therapy", "Chemotherapy"],
            "subtypes": ["Glioblastoma", "Meningioma", "Pituitary tumor"]
        },
        "pneumonia": {
            "description": "An infection that inflames the air sacs in one or both lungs.",
            "symptoms": ["Cough", "Fever", "Shortness of breath", "Chest pain"],
            "treatment": ["Antibiotics", "Rest", "Fluids"],
            "subtypes": ["Bacterial pneumonia", "Viral pneumonia"]
        },
        "malaria": {
            "description": "A mosquito-borne infectious disease affecting humans and animals.",
            "symptoms": ["Fever", "Chills", "Headache", "Nausea", "Vomiting"],
            "treatment": ["Antimalarial medications"],
            "subtypes": ["Plasmodium falciparum", "Plasmodium vivax"]
        }
    }

# Routes
@app.post("/analyze")
async def analyze(
    image_file: UploadFile = File(...),
    pdf_file: UploadFile = File(...),
    disease_type: str = Form(...)
):
    image_path = None
    try:
        if disease_type not in MODELS:
            raise HTTPException(400, "Invalid disease type")
        
        if not image_file.content_type.startswith("image/"):
            raise HTTPException(400, "Invalid image file type")
        
        if pdf_file.content_type != "application/pdf":
            raise HTTPException(400, "Invalid PDF file type")

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

        pdf_content = await pdf_file.read()
        pdf_text = extract_text_from_pdf(pdf_content)

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

        return JSONResponse(content={
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
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(500, "Analysis failed")
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

@app.get("/diagnoses/{disease_type}")
async def get_diagnoses(disease_type: str):
    try:
        diagnosis_db = load_diagnosis_database()
        if disease_type not in diagnosis_db:
            raise HTTPException(status_code=404, detail=f"No diagnosis information found for {disease_type}")
        
        return JSONResponse(content=diagnosis_db[disease_type])
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving diagnoses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve diagnosis information")

@app.post("/possible_diagnoses")
async def get_possible_diagnoses(analysis_results: Dict[str, Any]):
    try:
        diagnosis_db = load_diagnosis_database()

        disease_type = None
        for model_type in MODELS:
            if model_type in analysis_results.get("medical_imaging", {}).get("model_type", "").lower():
                disease_type = model_type
                break
        
        if not disease_type:
            if "brain" in str(analysis_results).lower():
                disease_type = "brain_tumor"
            elif "lung" in str(analysis_results).lower() or "pneumonia" in str(analysis_results).lower():
                disease_type = "pneumonia"
            elif "malaria" in str(analysis_results).lower() or "blood" in str(analysis_results).lower():
                disease_type = "malaria"
            else:
                disease_type = list(diagnosis_db.keys())[0]

        is_positive = analysis_results.get("medical_imaging", {}).get("diagnosis", "") == "Infected"
        confidence = float(analysis_results.get("medical_imaging", {}).get("confidence", "0%").replace("%", ""))

        document_text = analysis_results.get("document_analysis", {}).get("summary", "")

        response = {
            "disease_type": disease_type,
            "diagnosis_status": "Positive" if is_positive else "Negative",
            "confidence": f"{confidence}%",
            "possible_diagnoses": []
        }

        if disease_type in diagnosis_db:
            disease_info = diagnosis_db[disease_type]

            if is_positive:
                response["possible_diagnoses"].append({
                    "name": disease_type.replace("_", " ").title(),
                    "probability": "High" if confidence > 85 else "Moderate",
                    "description": disease_info.get("description", ""),
                    "symptoms": disease_info.get("symptoms", [])[:5],
                    "treatments": disease_info.get("treatment", [])[:5] if isinstance(disease_info.get("treatment", []), list) else list(disease_info.get("treatment", {}).values())[0][:5],
                    "is_primary": True
                })

                subtypes = []
                if isinstance(disease_info.get("subtypes", []), list):
                    subtypes = disease_info.get("subtypes", [])[:3]
                elif isinstance(disease_info.get("subtypes", {}), dict):
                    for subtype_group in disease_info.get("subtypes", {}).values():
                        if isinstance(subtype_group, list):
                            subtypes.extend(subtype_group[:2])

                for i, subtype in enumerate(subtypes[:3]):
                    if isinstance(subtype, str):
                        response["possible_diagnoses"].append({
                            "name": subtype,
                            "probability": "Moderate" if i == 0 else "Low",
                            "description": f"Subtype of {disease_type.replace('_', ' ').title()}",
                            "is_primary": False
                        })
            else:
                response["possible_diagnoses"].append({
                    "name": "Negative for " + disease_type.replace("_", " ").title(),
                    "probability": "High" if confidence > 85 else "Moderate",
                    "description": f"No evidence of {disease_type.replace('_', ' ')} detected",
                    "is_primary": True
                })

                if disease_type == "brain_tumor":
                    response["possible_diagnoses"].extend([
                        {"name": "Migraine", "probability": "Moderate", "is_primary": False},
                        {"name": "Intracranial Hemorrhage", "probability": "Low", "is_primary": False}
                    ])
                elif disease_type == "pneumonia":
                    response["possible_diagnoses"].extend([
                        {"name": "Bronchitis", "probability": "Moderate", "is_primary": False},
                        {"name": "Pulmonary Embolism", "probability": "Low", "is_primary": False}
                    ])
                elif disease_type == "malaria":
                    response["possible_diagnoses"].extend([
                        {"name": "Dengue Fever", "probability": "Moderate", "is_primary": False},
                        {"name": "Viral Infection", "probability": "Moderate", "is_primary": False}
                    ])

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error generating possible diagnoses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate possible diagnoses")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8123)
