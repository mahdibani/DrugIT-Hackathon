export interface AnalysisResult {
    medical_imaging: {
      diagnosis: string;
      confidence: string;
      model_type: string;
    };
    document_analysis: {
      summary: string;
      page_count: number;
      file_name: string;
    };
  }