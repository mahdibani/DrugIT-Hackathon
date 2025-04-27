import json
import logging
import requests
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Path to the treatments database file (if it exists)
TREATMENTS_DB_PATH = "treatments_db.json"

def load_diagnosis_database() -> Dict[str, Dict[str, Any]]:
    """
    Load diagnosis information database
    
    Returns:
        Dictionary containing diagnosis information for various diseases
    """
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
    """
    Load treatments database from file or return mock data
    
    Returns:
        Dictionary containing treatment information for various diseases
    """
    try:
        with open(TREATMENTS_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load treatments database: {e}")
        # Fallback mock data
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

def fetch_fda_drugs_for_condition(condition: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch drugs from FDA API based on a specific medical condition
    
    Args:
        condition: The medical condition to search for
        limit: Maximum number of results to return
        
    Returns:
        List of drug information dictionaries
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