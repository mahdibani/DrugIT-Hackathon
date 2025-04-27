import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AnalysisResult } from "../types";
import api from "../services/api";
import "../App.css";

interface ResultsPageProps {
  resultData: AnalysisResult | null;
}

const ResultsPage: React.FC<ResultsPageProps> = ({ resultData }) => {
  const navigate = useNavigate();
  const [diagnoses, setDiagnoses] = useState<any>(null);
  const [isLoadingDiagnoses, setIsLoadingDiagnoses] = useState(false);
  const [diagnosisError, setDiagnosisError] = useState("");

  useEffect(() => {
    const fetchPossibleDiagnoses = async () => {
      if (!resultData) return;
      try {
        setIsLoadingDiagnoses(true);
        setDiagnosisError("");

        const response = await api.post("/possible_diagnoses", resultData);
        setDiagnoses(response.data);
      } catch (err) {
        console.error("Failed to fetch diagnoses:", err);
        setDiagnosisError("Failed to load diagnostic information");
      } finally {
        setIsLoadingDiagnoses(false);
      }
    };

    fetchPossibleDiagnoses();
  }, [resultData]);

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

  const { medical_imaging, document_analysis } = resultData;
  const isCritical = medical_imaging.diagnosis === "Infected";
  const confidenceValue = parseFloat(medical_imaging.confidence.replace('%', ''));
  const isLowConfidence = confidenceValue < 85;

  return (
    <div className="container">
      <div className={`results-page ${isCritical ? "critical" : "normal"}`}>
        <h1>Integrated Medical Analysis Report</h1>

        <div className="result-sections">
          {/* Imaging Analysis Section */}
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

          {/* Document Analysis Section */}
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
        </div>

        {/* Possible Diagnoses Section */}
        <div className="diagnoses-section">
          <h2>Possible Diagnoses</h2>

          {isLoadingDiagnoses && (
            <div className="loading-diagnoses">
              <div className="spinner"></div>
              <p>Generating diagnostic information...</p>
            </div>
          )}

          {diagnosisError && (
            <div className="error-message">
              {diagnosisError}
            </div>
          )}

          {diagnoses && !isLoadingDiagnoses && !diagnosisError && (
            <div className="diagnoses-list">
              {diagnoses.possible_diagnoses.map((diagnosis: any, index: number) => (
                <div
                  key={index}
                  className={`diagnosis-card ${diagnosis.is_primary ? 'primary-diagnosis' : 'secondary-diagnosis'}`}
                >
                  <div className="diagnosis-header">
                    <h3>{diagnosis.name}</h3>
                    <span className={`probability-badge ${diagnosis.probability.toLowerCase()}`}>
                      {diagnosis.probability} Probability
                    </span>
                  </div>

                  {diagnosis.description && (
                    <p className="diagnosis-description">{diagnosis.description}</p>
                  )}

                  {diagnosis.symptoms && diagnosis.symptoms.length > 0 && (
                    <div className="diagnosis-details">
                      <h4>Common Symptoms</h4>
                      <ul className="symptom-list">
                        {diagnosis.symptoms.map((symptom: string, idx: number) => (
                          <li key={idx}>{symptom}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {diagnosis.treatments && diagnosis.treatments.length > 0 && (
                    <div className="diagnosis-details">
                      <h4>Possible Treatments</h4>
                      <ul className="treatment-list">
                        {diagnosis.treatments.map((treatment: string, idx: number) => (
                          <li key={idx}>{treatment}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action Bar */}
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
