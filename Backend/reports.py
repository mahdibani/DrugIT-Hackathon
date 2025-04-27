from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
import random
from datetime import datetime
from openai import OpenAI

from diagnoses import get_severity_level
from treatments import select_treatments

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

router = APIRouter()

@router.post("/suggest_assessment")
async def suggest_assessment(request: Request):
    """Generate a clinical assessment suggestion based on diagnostic data"""
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

@router.post("/generate_final_report")
async def generate_final_report(request: Request):
    """Generate final medical report based on all available data"""
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
        else:  # normal
            additional_instructions = "Routine follow-up as needed. Continue with preventive care and monitoring."
        
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
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint for API status"""
    return {"status": "ok", "module": "analyze"}