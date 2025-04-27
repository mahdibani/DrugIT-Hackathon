import React from "react";
import { useNavigate } from "react-router-dom";
import { AnalysisResult } from "../types";
import "../App.css";

const ResultsPage: React.FC<{ resultData: AnalysisResult | null }> = ({ resultData }) => {
  const navigate = useNavigate();
  
  if (!resultData) {
    return (
      <div className="container">
        <div className="results-page">
          <h2>No results available</h2>
          <button className="button" onClick={() => navigate("/")}>
            Back to Upload
          </button>
        </div>
      </div>
    );
  }
  
  const { medical_imaging, document_analysis, generated_diagnosis } = resultData;
  const isCritical = medical_imaging.diagnosis === "Infected";
  const confidenceValue = parseFloat(medical_imaging.confidence.replace('%', ''));
  const isLowConfidence = confidenceValue < 85;
  
  // Handle both string and object formats for generated_diagnosis
  const diagnosisText = typeof generated_diagnosis === 'string' 
    ? generated_diagnosis 
    : generated_diagnosis?.text || "No diagnosis available";

  return (
    <div className="container">
      <div className={`results-page ${isCritical ? "critical" : "normal"}`}>
        <h1>Integrated Medical Analysis Report</h1>
        <div className="result-sections">
          <div className={`result-card ${isCritical ? "critical" : "normal"}`}>
            <h2>Imaging Analysis</h2>
            <div className="result-item">
              <span>Clinical Finding:</span>
              <span className={isCritical ? "critical-text" : ""}>
                {medical_imaging.diagnosis}
              </span>
            </div>
            <div className="result-item">
              <span>Confidence Level:</span>
              <span>{medical_imaging.confidence}</span>
            </div>
            <div className="result-item">
              <span>Analysis Method:</span>
              <span>{medical_imaging.model_type.toUpperCase()} Model</span>
            </div>
           
            {isLowConfidence && (
              <div className="confidence-warning">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12" y2="16"></line>
                </svg>
                Moderate Confidence - Consider additional verification
              </div>
            )}
          </div>
          
          <div className="result-card">
            <h2>Clinical Document Summary</h2>
            <div className="result-item">
              <span>Document:</span>
              <span>{document_analysis.file_name}</span>
            </div>
            <div className="result-item">
              <span>Pages Analyzed:</span>
              <span>{document_analysis.page_count}</span>
            </div>
            <div className="summary-content">
              <h3>Key Insights</h3>
              {document_analysis.summary.split('\n').map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          </div>
         
          <div className="result-card">
            <h2>Generated Diagnosis</h2>
            <div className="diagnosis-content">
              {diagnosisText.split('\n').map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          </div>
        </div>
        
        <div className="action-bar">
          <button className="button" onClick={() => navigate("/")}>
            Start New Analysis
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;