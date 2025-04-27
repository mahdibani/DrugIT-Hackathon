export interface MedicalImaging {
    diagnosis: string;
    confidence: string;
    model_type: string;
    }
    export interface DocumentAnalysis {
    summary: string;
    page_count: number;
    file_name: string;
    }
    export interface AnalysisResult {
    medical_imaging: MedicalImaging;
    document_analysis: DocumentAnalysis;
    }
    export interface Diagnosis {
    name: string;
    probability: string;
    description?: string;
    symptoms?: string[];
    treatments?: string[];
    is_primary: boolean;
    }
    export interface DiagnosisResponse {
    disease_type: string;
    diagnosis_status: string;
    confidence: string;
    possible_diagnoses: Diagnosis[];
    }