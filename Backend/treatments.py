from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import logging
import requests

from database import load_treatments_database

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

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

@router.post("/review_treatments")
async def review_treatments(request: Request):
    """Review and modify treatment recommendations"""
    try:
        # Get request body
        request_data = await request.json()
        
        # Extract data from request
        disease_type = request_data.get("disease_type", "")
        is_positive = request_data.get("diagnosis_status", "").lower() == "positive"
        doctor_modifications = request_data.get("doctor_modifications", {})
        use_external_api = request_data.get("use_external_api", True)
        
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

@router.get("/health")
async def health_check():
    """Health check endpoint for API status"""
    return {"status": "ok", "module": "treatments"}