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
import requests
from typing import Dict, Any, List, Optional
import logging
logger = logging.getLogger(__name__)

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
# Update the MODELS dictionary to include breast_tumor
MODELS = {
    "brain_tumor": {
        "type": "huggingface",
        "model_name": "shimaGh/Brain-Tumor-Detection",
        "target_size": (224, 224)
    },
    "breast_tumor": {
        "type": "yolo_local",
        "model_path": "yolov8_medical_detection.pt", 
        "target_size": (640, 640), 
        "conf_threshold": 0.25
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
            logger.info(f"✅ Loaded Hugging Face model for {disease}")
        elif config["type"] == "yolo":
            loaded_models[disease] = YOLO(config["model_name"])
            logger.info(f"✅ Loaded YOLO model for {disease}")
        elif config["type"] == "yolo_local":
            # Load local YOLO model
            model_path = config["model_path"]
            if os.path.exists(model_path):
                loaded_models[disease] = YOLO(model_path)
                logger.info(f"✅ Loaded local YOLO model for {disease} from {model_path}")
            else:
                logger.error(f"❌ Local YOLO model file not found: {model_path}")
                loaded_models[disease] = None
    except Exception as e:
        logger.error(f"❌ Failed to load model for {disease}: {e}")
        loaded_models[disease] = None
logger.info("🚀 All medical models loaded!")

# Update the load_diagnosis_database function to include breast_tumor
def load_diagnosis_database() -> Dict[str, Dict[str, Any]]:
    # Enhanced database with more comprehensive information
    return {
        "brain_tumor": {
            "description": "A tumor in the brain that can be benign or malignant.",
            "symptoms": ["Headaches", "Seizures", "Nausea", "Vision problems", "Cognitive difficulties", 
                        "Balance problems", "Speech difficulties", "Personality changes"],
            "treatment": ["Surgery", "Radiation therapy", "Chemotherapy", "Targeted therapy", "Immunotherapy"],
            "severity_levels": ["Low-grade (I-II)", "High-grade (III-IV)"],
            "risk_factors": ["Radiation exposure", "Family history", "Genetic disorders", "Immune system disorders"],
            "diagnostic_criteria": ["MRI scan", "CT scan", "Biopsy", "Neurological examination"],
            "subtypes": ["Glioblastoma", "Meningioma", "Pituitary tumor", "Astrocytoma", "Oligodendroglioma", "Ependymoma"]
        },
        "breast_tumor": {
            "description": "An abnormal growth of cells in the breast tissue that can be benign or malignant.",
            "symptoms": ["Lump in the breast", "Change in breast size or shape", "Skin dimpling", 
                        "Nipple discharge", "Breast pain", "Redness or thickening of the nipple or breast skin"],
            "treatment": ["Surgery", "Radiation therapy", "Chemotherapy", "Hormone therapy", "Targeted therapy", "Immunotherapy"],
            "severity_levels": ["Stage 0", "Stage I", "Stage II", "Stage III", "Stage IV"],
            "risk_factors": ["Age", "Family history", "Genetic mutations", "Hormone therapy", "Alcohol consumption", "Obesity"],
            "diagnostic_criteria": ["Mammogram", "Ultrasound", "MRI", "Biopsy", "Blood tests"],
            "subtypes": ["Ductal carcinoma in situ", "Invasive ductal carcinoma", "Lobular carcinoma", 
                        "Inflammatory breast cancer", "Triple-negative breast cancer", "HER2-positive breast cancer"]
        },
        "pneumonia": {
            "description": "An infection that inflames the air sacs in one or both lungs, which may fill with fluid.",
            "symptoms": ["Cough with phlegm", "Fever", "Shortness of breath", "Chest pain", "Fatigue", 
                        "Confusion (especially in older adults)", "Low body temperature", "Bluish lips or nailbeds"],
            "treatment": ["Antibiotics", "Antiviral medications", "Rest", "Fluids", "Oxygen therapy", "Hospitalization for severe cases"],
            "severity_levels": ["Mild", "Moderate", "Severe", "Critical"],
            "risk_factors": ["Age (very young or very old)", "Smoking", "Chronic diseases", "Weakened immune system", "Hospitalization"],
            "diagnostic_criteria": ["Chest X-ray", "Blood tests", "Sputum test", "Pulse oximetry", "CT scan"],
            "subtypes": ["Bacterial pneumonia", "Viral pneumonia", "Mycoplasma pneumonia", "Fungal pneumonia", "Aspiration pneumonia"]
        },
        "malaria": {
            "description": "A mosquito-borne infectious disease affecting humans caused by Plasmodium parasites.",
            "symptoms": ["Fever", "Chills", "Headache", "Nausea", "Vomiting", "Muscle pain", "Fatigue", 
                        "Sweating", "Chest or abdominal pain", "Enlarged spleen"],
            "treatment": ["Antimalarial medications", "Supportive care", "Hydration", "Antipyretics"],
            "severity_levels": ["Uncomplicated", "Severe/Complicated"],
            "risk_factors": ["Travel to endemic areas", "Lack of preventive measures", "Young age", "Pregnancy", "HIV/AIDS"],
            "diagnostic_criteria": ["Blood smear examination", "Rapid diagnostic tests", "PCR tests", "Serological tests"],
            "subtypes": ["Plasmodium falciparum", "Plasmodium vivax", "Plasmodium ovale", "Plasmodium malariae", "Plasmodium knowlesi"]
        }
    }

def load_treatments_database() -> Dict[str, List[Dict[str, Any]]]:
    try:
        with open(TREATMENTS_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load treatments database: {e}")
        # Enhanced fallback mock data with more comprehensive information
        return {
            "brain_tumor": [
                {
                    "name": "Dexamethasone",
                    "description": "Corticosteroid to reduce inflammation and swelling around brain tumors",
                    "dosage": "4-16 mg daily, divided into 2-4 doses",
                    "duration": "As needed to control symptoms",
                    "contraindications": "Systemic fungal infections, hypersensitivity",
                    "side_effects": ["Mood changes", "Increased appetite", "Fluid retention", "Insomnia", "Elevated blood sugar"],
                    "efficacy_rate": "70-80% for symptom management",
                    "monitoring_requirements": ["Blood glucose levels", "Blood pressure", "Electrolytes"]
                },
                {
                    "name": "Temozolomide",
                    "description": "Alkylating agent used in chemotherapy for malignant brain tumors",
                    "dosage": "150-200 mg/m² daily for 5 consecutive days per 28-day cycle",
                    "duration": "6-12 cycles depending on response and tolerance",
                    "contraindications": "Severe myelosuppression, pregnancy",
                    "side_effects": ["Nausea", "Fatigue", "Headache", "Constipation", "Myelosuppression"],
                    "efficacy_rate": "45-60% for glioblastoma patients",
                    "monitoring_requirements": ["Complete blood count", "Liver function tests", "Kidney function tests"]
                },
                {
                    "name": "Bevacizumab",
                    "description": "Monoclonal antibody that targets vascular endothelial growth factor (VEGF)",
                    "dosage": "10 mg/kg every 2 weeks",
                    "duration": "Until disease progression or unacceptable toxicity",
                    "contraindications": "Recent surgery, uncontrolled hypertension, pregnancy",
                    "side_effects": ["Hypertension", "Proteinuria", "Delayed wound healing", "Bleeding", "Blood clots"],
                    "efficacy_rate": "30-40% response rate in recurrent glioblastoma",
                    "monitoring_requirements": ["Blood pressure", "Urinalysis", "Cardiac function"]
                }
            ],
            "breast_tumor": [
                {
                    "name": "Tamoxifen",
                    "description": "Selective estrogen receptor modulator (SERM) used in hormone therapy for estrogen receptor-positive breast cancer",
                    "dosage": "20 mg daily",
                    "duration": "5-10 years depending on cancer stage and risk factors",
                    "contraindications": "History of deep vein thrombosis, pulmonary embolism, stroke",
                    "side_effects": ["Hot flashes", "Fatigue", "Mood changes", "Increased risk of endometrial cancer", "Blood clots"],
                    "efficacy_rate": "Reduces recurrence risk by 40-50% in ER-positive breast cancer",
                    "monitoring_requirements": ["Gynecological examination", "Endometrial monitoring", "Blood counts"]
                },
                {
                    "name": "Anastrozole",
                    "description": "Aromatase inhibitor that blocks estrogen production in postmenopausal women",
                    "dosage": "1 mg daily",
                    "duration": "5-10 years",
                    "contraindications": "Premenopausal status, severe osteoporosis",
                    "side_effects": ["Joint pain", "Bone loss", "Hot flashes", "Mood changes", "Increased cholesterol"],
                    "efficacy_rate": "Reduces recurrence risk by 50-60% in postmenopausal women",
                    "monitoring_requirements": ["Bone density scans", "Cholesterol levels", "Liver function tests"]
                },
                {
                    "name": "Trastuzumab",
                    "description": "Monoclonal antibody targeting HER2 protein for HER2-positive breast cancer",
                    "dosage": "Initial dose of 8 mg/kg followed by 6 mg/kg every 3 weeks",
                    "duration": "52 weeks (1 year) for early-stage breast cancer",
                    "contraindications": "Severe heart disease, pregnancy",
                    "side_effects": ["Heart dysfunction", "Infusion reactions", "Nausea", "Fatigue", "Headache"],
                    "efficacy_rate": "Reduces recurrence risk by 40-50% in HER2-positive breast cancer",
                    "monitoring_requirements": ["Cardiac function (LVEF)", "CBC", "Liver and kidney function"]
                },
                {
                    "name": "Palbociclib",
                    "description": "CDK4/6 inhibitor used in combination with hormone therapy for HR+/HER2- advanced breast cancer",
                    "dosage": "125 mg once daily for 21 days, followed by 7 days off",
                    "duration": "Until disease progression or unacceptable toxicity",
                    "contraindications": "Severe neutropenia, liver impairment",
                    "side_effects": ["Neutropenia", "Leukopenia", "Fatigue", "Nausea", "Infections"],
                    "efficacy_rate": "Improves progression-free survival by 10-12 months",
                    "monitoring_requirements": ["Complete blood count", "Liver function tests", "ECG monitoring"]
                }
            ],
            "pneumonia": [
                {
                    "name": "Azithromycin",
                    "description": "Macrolide antibiotic effective against common pneumonia pathogens",
                    "dosage": "500 mg on day 1, then 250 mg daily on days 2-5",
                    "duration": "5 days",
                    "contraindications": "Known hypersensitivity, history of QT prolongation",
                    "side_effects": ["Diarrhea", "Nausea", "Abdominal pain", "Headache", "QT interval prolongation"],
                    "efficacy_rate": "85-90% for community-acquired pneumonia",
                    "monitoring_requirements": ["Liver function", "ECG if history of cardiac issues"]
                },
                {
                    "name": "Amoxicillin-Clavulanate",
                    "description": "Broad-spectrum antibiotic combination for bacterial pneumonia",
                    "dosage": "875 mg/125 mg twice daily",
                    "duration": "7-10 days",
                    "contraindications": "Penicillin allergy, severe hepatic impairment",
                    "side_effects": ["Diarrhea", "Rash", "Nausea", "Vomiting", "Liver enzyme elevation"],
                    "efficacy_rate": "80-85% for community-acquired pneumonia",
                    "monitoring_requirements": ["Liver function tests", "Kidney function tests"]
                },
                {
                    "name": "Levofloxacin",
                    "description": "Respiratory fluoroquinolone with excellent coverage for pneumonia pathogens",
                    "dosage": "750 mg once daily",
                    "duration": "5-7 days",
                    "contraindications": "QT prolongation, tendon disorders, myasthenia gravis",
                    "side_effects": ["Tendonitis", "QT prolongation", "GI disturbances", "Headache", "Photosensitivity"],
                    "efficacy_rate": "90-95% for community-acquired pneumonia",
                    "monitoring_requirements": ["Tendon symptoms", "QT interval if risk factors present"]
                }
            ],
            "malaria": [
                {
                    "name": "Artemether-Lumefantrine",
                    "description": "Combination therapy for uncomplicated malaria",
                    "dosage": "4 tablets twice daily for 3 days (total of 24 tablets)",
                    "duration": "3 days",
                    "contraindications": "First trimester of pregnancy, severe malaria",
                    "side_effects": ["Headache", "Dizziness", "Loss of appetite", "Muscle and joint pain", "Palpitations"],
                    "efficacy_rate": "95-98% cure rate for P. falciparum malaria",
                    "monitoring_requirements": ["Parasite count", "Hemoglobin levels", "ECG if cardiac history"]
                },
                {
                    "name": "Atovaquone-Proguanil",
                    "description": "Fixed-dose combination used for treatment and prevention of malaria",
                    "dosage": "4 tablets once daily for 3 days",
                    "duration": "3 days",
                    "contraindications": "Severe renal impairment, pregnancy",
                    "side_effects": ["Abdominal pain", "Nausea", "Vomiting", "Headache", "Elevated liver enzymes"],
                    "efficacy_rate": "90-95% cure rate for uncomplicated malaria",
                    "monitoring_requirements": ["Liver function", "Renal function", "Parasite count"]
                },
                {
                    "name": "Quinine with Doxycycline",
                    "description": "Combination therapy for chloroquine-resistant malaria",
                    "dosage": "Quinine 10 mg/kg three times daily + Doxycycline 100 mg twice daily",
                    "duration": "7 days",
                    "contraindications": "G6PD deficiency, pregnancy, children under 8 years (doxycycline)",
                    "side_effects": ["Cinchonism (tinnitus, headache, nausea)", "Photosensitivity", "GI upset"],
                    "efficacy_rate": "85-90% cure rate for resistant strains",
                    "monitoring_requirements": ["ECG monitoring", "Blood glucose", "Complete blood count"]
                }
            ]
        }
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
def fetch_fda_drugs_for_condition(condition: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch drugs from FDA API based on a specific medical condition
    """
    try:
        # Map common disease names to search terms
        search_terms = {
            "brain_tumor": "brain neoplasm OR brain tumor OR glioma",
            "breast_tumor": "breast cancer OR breast carcinoma OR breast neoplasm",
            "pneumonia": "pneumonia OR respiratory infection",
            "malaria": "malaria OR anti-malarial"
        }
        
        search_query = search_terms.get(condition, condition.replace("_", " "))
        
        # FDA API endpoint with search parameters
        url = (
            f"https://api.fda.gov/drug/label.json"
            f"?search=indications_and_usage:{search_query}"
            f"&limit={limit}"
        )
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get('results'):
            logger.warning(f"No FDA drug results found for condition: {condition}")
            return []
        
        # Process and format the results
        drugs = []
        for result in data['results']:
            try:
                # Extract brand name or generic name
                brand_names = result.get("openfda", {}).get("brand_name", [])
                generic_names = result.get("openfda", {}).get("generic_name", [])
                
                drug_name = "Unknown"
                if brand_names:
                    drug_name = brand_names[0]
                elif generic_names:
                    drug_name = generic_names[0]
                
                # Extract and clean up common fields
                indications = result.get("indications_and_usage", ["No description available."])[0]
                dosage_info = result.get("dosage_and_administration", ["Consult physician for appropriate dosage."])[0]
                contra_info = result.get("contraindications", ["No specific contraindications listed."])[0]
                side_effects_raw = result.get("adverse_reactions", ["Side effects not specified."])[0]
                
                # Process side effects into a list
                side_effects = []
                if side_effects_raw:
                    # Split by periods and cleanup
                    effects = [e.strip() for e in side_effects_raw.split(".") if e.strip()]
                    # Take first 5 effects or less
                    side_effects = effects[:5]
                    if not side_effects:
                        side_effects = ["Side effects may include headache, nausea, and other symptoms."]
                
                drug_info = {
                    "name": drug_name,
                    "description": indications[:300] if indications else "No description available.",
                    "dosage": dosage_info[:300] if dosage_info else "As directed by physician.",
                    "duration": "As directed by physician",
                    "contraindications": contra_info[:200] if contra_info else "Consult with physician.",
                    "side_effects": side_effects,
                    "source": "FDA"  # Mark the source for later reference
                }
                drugs.append(drug_info)
            except Exception as drug_error:
                logger.error(f"Error processing drug result: {drug_error}")
                continue
        
        return drugs
        
    except Exception as e:
        logger.error(f"Error fetching FDA drug data: {e}")
        return []

def select_treatments(disease_type: str, is_positive: bool, use_external_api: bool = True) -> List[Dict[str, Any]]:
    """
    Select appropriate treatments based on disease type and diagnosis,
    combining local database with external FDA API data
    
    Args:
        disease_type: Type of disease (e.g., brain_tumor, pneumonia)
        is_positive: Whether the diagnosis is positive
        use_external_api: Whether to use the external FDA API
        
    Returns:
        List of recommended treatments
    """
    # Step 1: Get treatments from local database
    treatments_db = load_treatments_database()
    local_treatments = []
    
    # If the disease type exists in treatments database and diagnosis is positive
    if disease_type in treatments_db and is_positive:
        # Get all available treatments for this disease type
        local_treatments = treatments_db.get(disease_type, [])
        # Mark the source
        for treatment in local_treatments:
            treatment["source"] = "local"
    
    # Step 2: Get supportive care for negative diagnoses
    if not is_positive:
        supportive_care = None
        if disease_type == "brain_tumor":
            supportive_care = {
                "name": "Supportive Care - Headache Management",
                "description": "Non-opioid pain relievers for headache management",
                "dosage": "As directed on package or by physician",
                "duration": "As needed for symptom relief",
                "side_effects": ["Stomach upset", "Nausea"],
                "source": "local"
            }
        elif disease_type == "breast_tumor":
            supportive_care = {
                "name": "Supportive Care - Imaging Follow-up",
                "description": "Regular imaging to monitor for any changes",
                "dosage": "N/A",
                "duration": "As recommended by physician",
                "side_effects": ["None"],
                "source": "local"
            }
        elif disease_type == "pneumonia":
            supportive_care = {
                "name": "Supportive Care - Respiratory Support",
                "description": "Mucolytic agents and expectorants to manage respiratory symptoms",
                "dosage": "As directed on package or by physician",
                "duration": "7-10 days or as needed",
                "side_effects": ["Nausea", "Drowsiness"],
                "source": "local"
            }
        else:  # malaria or others
            supportive_care = {
                "name": "Supportive Care - Symptomatic Relief",
                "description": "Antipyretics and analgesics for fever and discomfort",
                "dosage": "As directed on package or by physician",
                "duration": "As needed for symptom relief",
                "side_effects": ["Stomach upset", "Drowsiness"],
                "source": "local"
            }
        
        if supportive_care:
            local_treatments.append(supportive_care)
    
    # Step 3: If requested, fetch external treatments from FDA API
    external_treatments = []
    if use_external_api and is_positive:
        try:
            # Only fetch FDA data for positive diagnoses
            external_treatments = fetch_fda_drugs_for_condition(disease_type, limit=3)
        except Exception as e:
            logger.error(f"Failed to fetch external treatment data: {e}")
    
    # Step 4: Combine treatments, prioritizing local treatments first
    # Remove duplicates (prefer local over external if names are similar)
    combined_treatments = []
    added_names = set()
    
    # First add local treatments
    for treatment in local_treatments:
        treatment_name = treatment["name"].lower()
        if treatment_name not in added_names:
            combined_treatments.append(treatment)
            added_names.add(treatment_name)
    
    # Then add external treatments (avoiding duplicates)
    for treatment in external_treatments:
        treatment_name = treatment["name"].lower()
        # Check for similar names with fuzzy matching
        add_treatment = True
        for existing_name in added_names:
            # Simple similarity check (can be improved)
            if (treatment_name in existing_name or 
                existing_name in treatment_name or
                treatment_name.split()[0] == existing_name.split()[0]):
                add_treatment = False
                break
        
        if add_treatment:
            combined_treatments.append(treatment)
            added_names.add(treatment_name)
    
    # Step 5: Limit to a reasonable number (5 max)
    return combined_treatments[:5]
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

        # Inside the analyze endpoint when processing results
        if MODELS[disease_type]["type"] == "huggingface":
            results = loaded_models[disease_type](img)
            top_result = results[0]
            label = str(top_result["label"])
            confidence = round(top_result["score"] * 100, 2)
            diagnosis = "Normal" if any(kw in label.lower() for kw in ["no", "normal", "negative"]) else "Infected"
        elif MODELS[disease_type]["type"] == "yolo_local" or MODELS[disease_type]["type"] == "yolo":
            results = loaded_models[disease_type].predict(image_path)
            detections = results[0].boxes
            confidence = round(detections.conf.max().item() * 100, 2) if len(detections) > 0 else 0
            diagnosis = "Infected" if len(detections) > 0 else "Normal"
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
        
        # Inside get_possible_diagnoses endpoint
        if not disease_type:
            if "brain" in str(analysis_results).lower():
                disease_type = "brain_tumor"
            elif "breast" in str(analysis_results).lower():
                disease_type = "breast_tumor"
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
        use_external_api = request_data.get("use_external_api", True)  # New parameter
        
        if not disease_type:
            raise HTTPException(400, "Missing disease type information")
        
        # Get initial treatment recommendations using enhanced function
        initial_treatments = select_treatments(disease_type, is_positive, use_external_api)
        
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
                new_treatment["source"] = "doctor"  # Mark doctor-added treatments
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