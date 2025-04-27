from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
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
import json
from typing import Dict, Any, List
from openai import OpenAI
from datetime import datetime
import random

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

# Load treatments database
TREATMENTS_DB_PATH = "treatments_database.json"  # Updated path to be relative

def load_treatments_database() -> Dict[str, List[Dict[str, Any]]]:
    try:
        with open(TREATMENTS_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load treatments database: {e}")
        # Fallback mock data if database file is not accessible
        return {
            "brain_tumor": [
                {
                    "name": "Dexamethasone",
                    "description": "Corticosteroid to reduce inflammation and swelling around brain tumors",
                    "dosage": "4-16 mg daily, divided into 2-4 doses",
                    "duration": "As needed to control symptoms",
                    "contraindications": "Systemic fungal infections, hypersensitivity",
                    "side_effects": ["Mood changes", "Increased appetite", "Fluid retention", "Insomnia"]
                },
                {
                    "name": "Temozolomide",
                    "description": "Alkylating agent used in chemotherapy for malignant brain tumors",
                    "dosage": "150-200 mg/m² daily for 5 consecutive days per 28-day cycle",
                    "duration": "6-12 cycles depending on response and tolerance",
                    "contraindications": "Severe myelosuppression, pregnancy",
                    "side_effects": ["Nausea", "Fatigue", "Headache", "Constipation", "Myelosuppression"]
                }
            ],
            "pneumonia": [
                {
                    "name": "Azithromycin",
                    "description": "Macrolide antibiotic effective against common pneumonia pathogens",
                    "dosage": "500 mg on day 1, then 250 mg daily on days 2-5",
                    "duration": "5 days",
                    "contraindications": "Known hypersensitivity, history of QT prolongation",
                    "side_effects": ["Diarrhea", "Nausea", "Abdominal pain", "Headache"]
                },
                {
                    "name": "Amoxicillin-Clavulanate",
                    "description": "Broad-spectrum antibiotic combination for bacterial pneumonia",
                    "dosage": "875 mg/125 mg twice daily",
                    "duration": "7-10 days",
                    "contraindications": "Penicillin allergy, severe hepatic impairment",
                    "side_effects": ["Diarrhea", "Rash", "Nausea", "Vomiting"]
                }
            ],
            "malaria": [
                {
                    "name": "Artemether-Lumefantrine",
                    "description": "Combination therapy for uncomplicated malaria",
                    "dosage": "4 tablets twice daily for 3 days (total of 24 tablets)",
                    "duration": "3 days",
                    "contraindications": "First trimester of pregnancy, severe malaria",
                    "side_effects": ["Headache", "Dizziness", "Loss of appetite", "Muscle and joint pain"]
                },
                {
                    "name": "Atovaquone-Proguanil",
                    "description": "Fixed-dose combination used for treatment and prevention of malaria",
                    "dosage": "4 tablets once daily for 3 days",
                    "duration": "3 days",
                    "contraindications": "Severe renal impairment, pregnancy",
                    "side_effects": ["Abdominal pain", "Nausea", "Vomiting", "Headache"]
                }
            ]
        }

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

def get_severity_level(diagnosis_status: str, confidence: float) -> str:
    """Determine severity level based on diagnosis and confidence"""
    if diagnosis_status.lower() == "positive":
        if confidence > 90:
            return "severe"
        return "moderate"
    return "normal"

def select_treatments(disease_type: str, is_positive: bool) -> List[Dict[str, Any]]:
    """Select appropriate treatments based on disease type and diagnosis"""
    treatments_db = load_treatments_database()
    
    # If the disease type exists in treatments database and diagnosis is positive
    if disease_type in treatments_db and is_positive:
        # Return all available treatments for this disease type
        available_treatments = treatments_db.get(disease_type, [])
        # Limit to 3 treatments max
        return available_treatments[:3]
    
    # For negative diagnoses or unavailable disease types, return supportive care recommendations
    if disease_type == "brain_tumor":
        return [{
            "name": "Supportive Care - Headache Management",
            "description": "Non-opioid pain relievers for headache management",
            "dosage": "As directed on package or by physician",
            "duration": "As needed for symptom relief",
            "side_effects": ["Stomach upset", "Nausea"]
        }]
    elif disease_type == "pneumonia":
        return [{
            "name": "Supportive Care - Respiratory Support",
            "description": "Mucolytic agents and expectorants to manage respiratory symptoms",
            "dosage": "As directed on package or by physician",
            "duration": "7-10 days or as needed",
            "side_effects": ["Nausea", "Drowsiness"]
        }]
    else:  # malaria or others
        return [{
            "name": "Supportive Care - Symptomatic Relief",
            "description": "Antipyretics and analgesics for fever and discomfort",
            "dosage": "As directed on package or by physician",
            "duration": "As needed for symptom relief",
            "side_effects": ["Stomach upset", "Drowsiness"]
        }]

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
                "model_type": disease_type  # Fixed to return proper disease_type
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
            if model_type in str(analysis_results.get("medical_imaging", {}).get("model_type", "")).lower():
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

# Fix: Updated endpoint to correctly parse request body
@app.post("/suggest_assessment")
async def suggest_assessment(request: Request):
    try:
        # Get request body
        request_data = await request.json()
        
        # Extract relevant data from request
        diagnostic_data = request_data.get("diagnostic_data", {})
        analysis_results = request_data.get("analysis_results", {})
        
        if not diagnostic_data or not analysis_results:
            raise HTTPException(400, "Missing required diagnostic data")
        
        # Extract key information for the prompt
        disease_type = diagnostic_data.get("disease_type", "").replace("_", " ").title()
        diagnosis_status = diagnostic_data.get("diagnosis_status", "")
        confidence = diagnostic_data.get("confidence", "0%")
        
        # Get primary diagnosis details
        primary_diagnosis = next((d for d in diagnostic_data.get("possible_diagnoses", []) if d.get("is_primary", False)), {})
        
        # Extract medical imaging and document analysis results
        medical_imaging = analysis_results.get("medical_imaging", {})
        document_analysis = analysis_results.get("document_analysis", {})
        document_summary = document_analysis.get("summary", "")
        
        # Create prompt for LLM
        assessment_prompt = f"""
        As an experienced physician reviewing this case, provide a professional clinical assessment based on:
        
        Disease Type: {disease_type}
        Primary Diagnosis: {primary_diagnosis.get("name", diagnosis_status)}
        Confidence Level: {confidence}
        
        Diagnostic Imaging Findings: 
        - {medical_imaging.get("diagnosis")} with {medical_imaging.get("confidence")} confidence
        
        Patient Document Summary:
        {document_summary}
        
        Key clinical features:
        {', '.join(primary_diagnosis.get("symptoms", []))}
        
        Write a concise, professional physician's assessment in 3-5 sentences that a doctor might enter to document their clinical impression and reasoning for this case. Include relevant findings, differential diagnoses if appropriate, and brief justification for your assessment.
        """
        
        # Generate assessment using LLM
        llm_response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=[
                {"role": "system", "content": "You are an experienced physician providing clinical assessments."},
                {"role": "user", "content": assessment_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        suggested_assessment = llm_response.choices[0].message.content.strip()
        
        return JSONResponse(content={"suggested_assessment": suggested_assessment})
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating assessment suggestion: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate assessment suggestion")

# Fix: Updated endpoint to correctly parse request body
@app.post("/review_treatments")
async def review_treatments(request: Request):
    try:
        # Get request body
        request_data = await request.json()
        
        # Extract data from request
        disease_type = request_data.get("disease_type", "")
        is_positive = request_data.get("diagnosis_status", "").lower() == "positive"
        doctor_modifications = request_data.get("doctor_modifications", {})
        
        if not disease_type:
            raise HTTPException(400, "Missing disease type information")
        
        # Get initial treatment recommendations from database
        initial_treatments = select_treatments(disease_type, is_positive)
        
        # Apply doctor's modifications if provided
        final_treatments = []
        
        # Process each treatment with doctor's modifications
        for treatment in initial_treatments:
            treatment_id = treatment.get("name", "").replace(" ", "_").lower()
            
            # Check if doctor modified this treatment
            if treatment_id in doctor_modifications:
                modification = doctor_modifications[treatment_id]
                
                # Handle removal
                if modification.get("action") == "remove":
                    continue
                
                # Handle modification
                if modification.get("action") == "modify":
                    modified_treatment = treatment.copy()
                    
                    # Update fields that doctor modified
                    for field, value in modification.get("changes", {}).items():
                        if field in modified_treatment and value:
                            modified_treatment[field] = value
                    
                    final_treatments.append(modified_treatment)
                else:
                    # Keep original if no modifications
                    final_treatments.append(treatment)
            else:
                # Keep original if not in modifications
                final_treatments.append(treatment)
        
        # Add new treatments if doctor added any
        new_treatments = doctor_modifications.get("new_treatments", [])
        for new_treatment in new_treatments:
            if all(key in new_treatment for key in ["name", "description", "dosage", "duration"]):
                # Ensure side_effects is a list
                if "side_effects" in new_treatment and isinstance(new_treatment["side_effects"], str):
                    new_treatment["side_effects"] = [item.strip() for item in new_treatment["side_effects"].split(",")]
                final_treatments.append(new_treatment)
        
        return JSONResponse(content={"treatments": final_treatments})
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reviewing treatments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process treatment review")

# Fix: Updated endpoint to correctly parse request body
@app.post("/generate_final_report")
async def generate_final_report(request: Request):
    try:
        # Get request body
        request_data = await request.json()
        
        # Extract data from request
        doctor_assessment = request_data.get("doctor_assessment", "")
        diagnostic_data = request_data.get("diagnostic_data", {})
        analysis_results = request_data.get("analysis_results", {})
        
        if not doctor_assessment or not diagnostic_data or not analysis_results:
            raise HTTPException(400, "Missing required data for final report generation")
        
        # Extract key information
        disease_type = diagnostic_data.get("disease_type", "")
        diagnosis_status = diagnostic_data.get("diagnosis_status", "")
        confidence = diagnostic_data.get("confidence", "0%")
        confidence_value = float(confidence.replace("%", ""))
        
        # Extract medical imaging and document analysis results
        medical_imaging = analysis_results.get("medical_imaging", {})
        document_analysis = analysis_results.get("document_analysis", {})
        
        # Determine severity level
        is_positive = diagnosis_status.lower() == "positive"
        severity_level = get_severity_level(diagnosis_status, confidence_value)
        
        # Get appropriate treatment recommendations
        recommended_treatments = select_treatments(disease_type, is_positive)
        
        # Generate a summary based on all available information
        summary_prompt = f"""
        Generate a concise diagnostic summary based on the following medical information:
        
        Disease Type: {disease_type.replace('_', ' ').title()}
        Diagnosis: {diagnosis_status} with {confidence} confidence
        
        Medical Imaging Findings: {medical_imaging.get('diagnosis')} with {medical_imaging.get('confidence')} confidence
        
        Patient Document Summary: 
        {document_analysis.get('summary', '')}
        
        Doctor's Assessment:
        {doctor_assessment}
        
        Please provide a focused, clinical diagnostic summary in 3-5 sentences that integrates this information.
        """
        
        try:
            # Use LLM to generate diagnostic summary
            llm_response = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct",
                messages=[
                    {"role": "system", "content": "Expert medical consultant providing precise diagnostic summaries"},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=250
            )
            diagnostic_summary = llm_response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM summary generation failed: {str(e)}")
            diagnostic_summary = f"Based on medical imaging analysis, the patient's diagnosis is {diagnosis_status} for {disease_type.replace('_', ' ').title()} with {confidence} confidence level. The clinical document review indicates further evaluation is needed."
        
        # Generate additional instructions based on severity
        additional_instructions = None
        if severity_level == "severe":
            additional_instructions = "Schedule immediate follow-up within 48 hours. Monitor for changes in symptoms, especially headache intensity, neurological deficits, or signs of increased intracranial pressure. Contact emergency services if condition deteriorates."
        elif severity_level == "moderate":
            additional_instructions = "Schedule follow-up within 7-14 days. Monitor symptoms and report any significant changes. Maintain adequate hydration and rest."
        
        # Create case ID and date for the report
        case_id = f"MIP-{disease_type.upper()[:3]}-{random.randint(10000, 99999)}"
        analysis_date = datetime.now().strftime("%Y-%m-%d")
        
        # Construct final report
        final_report = {
            "case_id": case_id,
            "analysis_date": analysis_date,
            "severity_level": severity_level,
            "diagnostic_summary": diagnostic_summary,
            "doctor_assessment": doctor_assessment,
            "recommended_treatments": recommended_treatments,
            "additional_instructions": additional_instructions
        }
        
        return JSONResponse(content=final_report)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating final report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate final report")

# Add debug route for testing API connectivity
@app.get("/health")
async def health_check():
    return {"status": "ok", "endpoints": ["/analyze", "/possible_diagnoses", "/suggest_assessment", "/generate_final_report"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8123)