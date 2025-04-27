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
  const [currentDate] = useState(new Date().toLocaleDateString());
  const [currentTime] = useState(new Date().toLocaleTimeString());

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
  
  // Determine severity level for visual indicators
  const getSeverityLevel = () => {
    if (isCritical) {
      return confidenceValue > 90 ? "severe" : "moderate";
    }
    return "normal";
  };
  
  const severityLevel = getSeverityLevel();
  
  // Format disease type for display
  const formatDiseaseType = (modelType: string) => {
    if (modelType.includes("brain")) return "Brain MRI Analysis";
    if (modelType.includes("pneumonia")) return "Chest X-Ray Analysis";
    if (modelType.includes("malaria")) return "Blood Smear Analysis";
    return modelType.toUpperCase() + " Analysis";
  };

  // Get recommendations based on results
  const getRecommendations = () => {
    if (isCritical) {
      if (confidenceValue > 90) {
        return "Immediate specialist consultation recommended";
      } else {
        return "Follow-up examination recommended within 7-14 days";
      }
    }
    return "Routine follow-up recommended";
  };

  return (
    <div className="container">
      <div className={`results-page ${severityLevel}`}>
        <div className="report-header">
          <h1>Integrated Medical Analysis Report</h1>
          <div className="report-meta">
            <div className="report-timestamp">
              <span>Report Generated: {currentDate} at {currentTime}</span>
              <span>Report ID: MIP-{Math.floor(Math.random() * 1000000)}</span>
            </div>
            <div className={`severity-indicator ${severityLevel}`}>
              <span className="severity-dot"></span>
              {severityLevel === "severe" ? "High Priority" : 
               severityLevel === "moderate" ? "Medium Priority" : "Normal"}
            </div>
          </div>
        </div>

        <div className="result-sections">
          {/* Imaging Analysis Section */}
          <div className={`result-card ${severityLevel}`}>
            <div className="card-header">
              <h2>Imaging Analysis</h2>
              <span className="analysis-type">{formatDiseaseType(medical_imaging.model_type)}</span>
            </div>
            
            <div className="result-metrics">
              <div className="metric">
                <span className="metric-label">Clinical Finding:</span>
                <span className={`metric-value ${isCritical ? "critical-text" : "normal-text"}`}>
                  {medical_imaging.diagnosis}
                  {isCritical && (
                    <svg className="alert-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="12" y1="8" x2="12" y2="12"></line>
                      <line x1="12" y1="16" x2="12" y2="16"></line>
                    </svg>
                  )}
                </span>
              </div>
              
              <div className="metric">
                <span className="metric-label">Confidence Level:</span>
                <div className="confidence-display">
                  <div className="confidence-bar-container">
                    <div 
                      className={`confidence-bar ${confidenceValue > 85 ? "high" : "moderate"}`}
                      style={{ width: `${confidenceValue}%` }}
                    ></div>
                  </div>
                  <span className="confidence-value">{medical_imaging.confidence}</span>
                </div>
              </div>
              
              <div className="metric">
                <span className="metric-label">Analysis Method:</span>
                <span className="metric-value">{medical_imaging.model_type.toUpperCase()} Model</span>
              </div>
              
              <div className="metric">
                <span className="metric-label">Recommendation:</span>
                <span className={`metric-value recommendation ${severityLevel}`}>
                  {getRecommendations()}
                </span>
              </div>
            </div>

            {isLowConfidence && (
              <div className="confidence-warning">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12" y2="16"></line>
                </svg>
                <span>Moderate Confidence - Additional verification recommended</span>
              </div>
            )}
          </div>

          {/* Document Analysis Section */}
          <div className="result-card document-analysis">
            <div className="card-header">
              <h2>Clinical Document Summary</h2>
              <span className="document-info">
                {document_analysis.file_name} ({document_analysis.page_count} pages)
              </span>
            </div>
            
            <div className="summary-content">
              <h3>Key Clinical Insights</h3>
              <div className="structured-summary">
                {document_analysis.summary.split('\n').map((line, index) => {
                  // Format each line with proper styling based on content
                  if (line.startsWith('-')) {
                    const [title, ...content] = line.substring(1).trim().split(':');
                    if (content.length > 0) {
                      return (
                        <div key={index} className="summary-item">
                          <h4>{title}</h4>
                          <p>{content.join(':')}</p>
                        </div>
                      );
                    }
                  }
                  return <p key={index} className="summary-text">{line}</p>;
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Possible Diagnoses Section */}
        <div className="diagnoses-section">
          <h2>
            Diagnostic Assessment
            <span className="section-subtitle">
              Based on imaging analysis and clinical document review
            </span>
          </h2>

          {isLoadingDiagnoses && (
            <div className="loading-diagnoses">
              <div className="spinner"></div>
              <p>Analyzing clinical data and generating diagnostic assessments...</p>
            </div>
          )}

          {diagnosisError && (
            <div className="error-message">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12" y2="16"></line>
              </svg>
              {diagnosisError}
            </div>
          )}

          {diagnoses && !isLoadingDiagnoses && !diagnosisError && (
            <>
              <div className="diagnosis-overview">
                <div className="overview-item">
                  <span className="overview-label">Primary Assessment:</span>
                  <span className={`overview-value ${diagnoses.diagnosis_status.toLowerCase() === 'positive' ? 'positive' : 'negative'}`}>
                    {diagnoses.diagnosis_status}
                  </span>
                </div>
                <div className="overview-item">
                  <span className="overview-label">Analysis Protocol:</span>
                  <span className="overview-value">{diagnoses.disease_type.replace('_', ' ').toUpperCase()}</span>
                </div>
                <div className="overview-item">
                  <span className="overview-label">Confidence:</span>
                  <span className="overview-value">{diagnoses.confidence}</span>
                </div>
              </div>
              
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

                    <div className="diagnosis-content">
                      {diagnosis.symptoms && diagnosis.symptoms.length > 0 && (
                        <div className="diagnosis-details">
                          <h4>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <circle cx="12" cy="12" r="10"></circle>
                              <line x1="12" y1="8" x2="12" y2="12"></line>
                              <line x1="12" y1="16" x2="12" y2="16"></line>
                            </svg>
                            Common Symptoms
                          </h4>
                          <ul className="symptom-list">
                            {diagnosis.symptoms.map((symptom: string, idx: number) => (
                              <li key={idx}>{symptom}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {diagnosis.treatments && diagnosis.treatments.length > 0 && (
                        <div className="diagnosis-details">
                          <h4>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                            </svg>
                            Recommended Treatments
                          </h4>
                          <ul className="treatment-list">
                            {diagnosis.treatments.map((treatment: string, idx: number) => (
                              <li key={idx}>{treatment}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    
                    {diagnosis.is_primary && (
                      <div className="clinical-recommendations">
                        <h4>Clinical Recommendations</h4>
                        <ul>
                          {diagnosis.probability.toLowerCase() === 'high' ? (
                            <>
                              <li>Specialist consultation within 24-48 hours</li>
                              <li>Complete diagnostic workup</li>
                              <li>Consider additional {diagnoses.disease_type.includes('brain') ? 'contrast MRI' : 
                                diagnoses.disease_type.includes('pneumonia') ? 'CT scan' : 'blood work'}</li>
                            </>
                          ) : (
                            <>
                              <li>Follow-up examination in 1-2 weeks</li>
                              <li>Monitor for symptom progression</li>
                              <li>Consider additional diagnostic tests if symptoms persist</li>
                            </>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Disclaimer Section */}
        <div className="report-disclaimer">
          <p><strong>Disclaimer:</strong> This report is generated using AI-assisted analysis and is intended to support clinical decision-making, not replace professional medical judgment. Results should be verified by qualified healthcare professionals.</p>
        </div>

        {/* Action Bar */}
        <div className="action-bar">
          <button className="button print-button" onClick={() => window.print()}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 6 2 18 2 18 9"></polyline>
              <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
              <rect x="6" y="14" width="12" height="8"></rect>
            </svg>
            Print Report
          </button>
          <button className="button" onClick={() => navigate("/")}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>
            Start New Analysis
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;