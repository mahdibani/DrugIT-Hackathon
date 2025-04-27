from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import logging

from database import load_diagnosis_database

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

def get_severity_level(diagnosis_status: str, confidence: float) -> str:
    """Determine severity level based on diagnosis and confidence"""
    if diagnosis_status.lower() == "positive":
        if confidence > 90:
            return "severe"
        return "moderate"
    return "normal"

@router.get("/diagnoses/{disease_type}")
async def get_diagnoses(disease_type: str):
    """Get detailed information about a specific disease type"""
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

@router.post("/possible_diagnoses")
async def get_possible_diagnoses(analysis_results: Dict[str, Any]):
    """Generate possible diagnoses based on analysis results"""
    try:
        diagnosis_db = load_diagnosis_database()

        # Determine disease type from analysis results
        disease_type = None
        model_type = analysis_results.get("medical_imaging", {}).get("model_type", "")
        
        # Try to get disease type from model type first
        for model in ["brain_tumor", "breast_tumor", "pneumonia", "malaria"]:
            if model in str(model_type).lower():
                disease_type = model
                break
        
        # If not found, try to infer from analysis results text
        if not disease_type:
            results_str = str(analysis_results).lower()
            if "brain" in results_str:
                disease_type = "brain_tumor"
            elif "breast" in results_str:
                disease_type = "breast_tumor"
            elif "lung" in results_str or "pneumonia" in results_str:
                disease_type = "pneumonia"
            elif "malaria" in results_str or "blood" in results_str:
                disease_type = "malaria"
            else:
                # Default to first available disease type
                disease_type = list(diagnosis_db.keys())[0]

        # Extract diagnosis information
        is_positive = analysis_results.get("medical_imaging", {}).get("diagnosis", "") == "Infected"
        confidence_str = analysis_results.get("medical_imaging", {}).get("confidence", "0%")
        confidence = float(confidence_str.replace("%", ""))
        document_text = analysis_results.get("document_analysis", {}).get("summary", "")

        # Prepare response
        response = {
            "disease_type": disease_type,
            "diagnosis_status": "Positive" if is_positive else "Negative",
            "confidence": f"{confidence}%",
            "possible_diagnoses": []
        }

        # Generate possible diagnoses based on disease type
        if disease_type in diagnosis_db:
            disease_info = diagnosis_db[disease_type]

            if is_positive:
                # Primary diagnosis for positive case
                response["possible_diagnoses"].append({
                    "name": disease_type.replace("_", " ").title(),
                    "probability": "High" if confidence > 85 else "Moderate",
                    "description": disease_info.get("description", ""),
                    "symptoms": disease_info.get("symptoms", [])[:5],
                    "treatments": disease_info.get("treatment", [])[:5] if isinstance(disease_info.get("treatment", []), list) else list(disease_info.get("treatment", {}).values())[0][:5],
                    "is_primary": True
                })

                # Add subtypes as differential diagnoses
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
                # Primary diagnosis for negative case
                response["possible_diagnoses"].append({
                    "name": "Negative for " + disease_type.replace("_", " ").title(),
                    "probability": "High" if confidence > 85 else "Moderate",
                    "description": f"No evidence of {disease_type.replace('_', ' ')} detected",
                    "is_primary": True
                })

                # Add differential diagnoses based on disease type
                if disease_type == "brain_tumor":
                    response["possible_diagnoses"].extend([
                        {"name": "Migraine", "probability": "Moderate", "is_primary": False},
                        {"name": "Intracranial Hemorrhage", "probability": "Low", "is_primary": False}
                    ])
                elif disease_type == "breast_tumor":
                    response["possible_diagnoses"].extend([
                        {"name": "Fibrocystic Breast Changes", "probability": "Moderate", "is_primary": False},
                        {"name": "Mastitis", "probability": "Low", "is_primary": False}
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

@router.get("/health")
async def health_check():
    """Health check endpoint for API status"""
    return {"status": "ok", "module": "diagnoses"}