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
  
  // Doctor's input states
  const [doctorInput, setDoctorInput] = useState("");
  const [showDoctorInput, setShowDoctorInput] = useState(false);
  const [finalReport, setFinalReport] = useState<any>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState("");
  
  // New states for suggestion feature
  const [suggestedAssessment, setSuggestedAssessment] = useState("");
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState("");
  const [showSuggestion, setShowSuggestion] = useState(false);
  const [isEditingSuggestion, setIsEditingSuggestion] = useState(false);

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
  
  // New function to fetch suggested assessment
  const fetchSuggestedAssessment = async () => {
    if (!diagnoses || !resultData) {
      setSuggestionError("Diagnostic data not available for generating suggestions");
      return;
    }
    
    try {
      setIsLoadingSuggestion(true);
      setSuggestionError("");
      
      const response = await api.post("/suggest_assessment", {
        diagnostic_data: diagnoses,
        analysis_results: resultData
      });
      
      setSuggestedAssessment(response.data.suggested_assessment);
      setShowSuggestion(true);
    } catch (err) {
      console.error("Failed to fetch suggested assessment:", err);
      setSuggestionError("Failed to generate assessment suggestion");
    } finally {
      setIsLoadingSuggestion(false);
    }
  };
  
  // Modified function to show doctor input with suggestion
  const handleShowDoctorInput = async () => {
    setShowDoctorInput(true);
    await fetchSuggestedAssessment();
  };
  
  // Function to accept the suggestion
  const handleAcceptSuggestion = () => {
    setDoctorInput(suggestedAssessment);
    setIsEditingSuggestion(false);
  };
  
  // Function to edit the suggestion
  const handleEditSuggestion = () => {
    setDoctorInput(suggestedAssessment);
    setIsEditingSuggestion(true);
  };
  
  // Function to request a new suggestion
  const handleNewSuggestion = async () => {
    await fetchSuggestedAssessment();
  };

  const handleDoctorInputSubmit = async () => {
    if (!doctorInput.trim() || !diagnoses || !resultData) {
      setReportError("Please provide your medical assessment");
      return;
    }

    try {
      setIsGeneratingReport(true);
      setReportError("");

      const response = await api.post("/generate_final_report", {
        doctor_assessment: doctorInput,
        diagnostic_data: diagnoses,
        analysis_results: resultData
      });

      setFinalReport(response.data);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error("Failed to generate final report:", err);
      setReportError("Failed to generate final report. Please try again.");
    } finally {
      setIsGeneratingReport(false);
    }
  };

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

  // If final report is available, show that instead of the analysis results
  if (finalReport) {
    return (
      <div className="container">
        <div className="results-page">
          <div className="report-header">
            <h1>Final Medical Report</h1>
            <div className="report-meta">
              <div className="report-timestamp">
                <span>Report Generated: {currentDate} at {currentTime}</span>
                <span>Report ID: MIP-FINAL-{Math.floor(Math.random() * 1000000)}</span>
              </div>
              <div className={`severity-indicator ${finalReport.severity_level}`}>
                <span className="severity-dot"></span>
                {finalReport.severity_level === "severe" ? "High Priority" : 
                 finalReport.severity_level === "moderate" ? "Medium Priority" : "Normal"}
              </div>
            </div>
          </div>

          {/* Patient Information */}
          <div className="result-card">
            <div className="card-header">
              <h2>Patient Information</h2>
            </div>
            <div className="patient-info">
              <p><strong>Case ID:</strong> {finalReport.case_id}</p>
              <p><strong>Analysis Date:</strong> {finalReport.analysis_date}</p>
            </div>
          </div>

          {/* Diagnostic Summary */}
          <div className={`result-card ${finalReport.severity_level}`}>
            <div className="card-header">
              <h2>Diagnostic Summary</h2>
            </div>
            <div className="diagnostic-summary">
              <p>{finalReport.diagnostic_summary}</p>
            </div>
          </div>

          {/* Doctor's Assessment */}
          <div className="result-card doctor-assessment">
            <div className="card-header">
              <h2>Physician's Assessment</h2>
            </div>
            <div className="doctor-assessment-content">
              <p>{finalReport.doctor_assessment}</p>
            </div>
          </div>

          {/* Treatment Recommendations */}
          <div className="result-card treatment-recommendations">
            <div className="card-header">
              <h2>Treatment Recommendations</h2>
            </div>
            <div className="treatments-list">
              {finalReport.recommended_treatments.map((treatment: any, index: number) => (
                <div key={index} className="treatment-item">
                  <h3>{treatment.name}</h3>
                  <p className="treatment-description">{treatment.description}</p>
                  
                  {treatment.dosage && (
                    <div className="treatment-detail">
                      <strong>Dosage:</strong> {treatment.dosage}
                    </div>
                  )}
                  
                  {treatment.duration && (
                    <div className="treatment-detail">
                      <strong>Duration:</strong> {treatment.duration}
                    </div>
                  )}
                  
                  {treatment.contraindications && (
                    <div className="treatment-detail">
                      <strong>Contraindications:</strong> {treatment.contraindications}
                    </div>
                  )}
                  
                  {treatment.side_effects && treatment.side_effects.length > 0 && (
                    <div className="treatment-detail">
                      <strong>Possible Side Effects:</strong>
                      <ul className="side-effects-list">
                        {treatment.side_effects.map((effect: string, idx: number) => (
                          <li key={idx}>{effect}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Additional Instructions */}
          {finalReport.additional_instructions && (
            <div className="result-card">
              <div className="card-header">
                <h2>Additional Instructions</h2>
              </div>
              <div className="additional-instructions">
                <p>{finalReport.additional_instructions}</p>
              </div>
            </div>
          )}

          {/* Disclaimer Section */}
          <div className="report-disclaimer">
            <p><strong>Disclaimer:</strong> This report is generated using AI-assisted analysis and clinical assessment. It is intended to support clinical decision-making, not replace professional medical judgment. Treatment recommendations should be verified by qualified healthcare professionals before implementation.</p>
          </div>

          {/* Action Bar */}
          <div className="action-bar">
            <button className="button print-button" onClick={() => window.print()}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 6 2 18 2 18 9"></polyline>
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                <rect x="6" y="14" width="12" height="8"></rect>
              </svg>
              Print Final Report
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
  }

  // Original results page code
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

        {/* Doctor's Input Section with Suggestion Feature */}
        {!showDoctorInput && diagnoses && !isLoadingDiagnoses && (
          <div className="doctor-action">
            <button 
              className="button primary-button"
              onClick={handleShowDoctorInput}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
              Add Physician's Assessment
            </button>
          </div>
        )}

        {showDoctorInput && (
          <div className="doctor-input-section">
            <h2>Physician's Assessment</h2>
            
            {/* Suggestion feature */}
            {isLoadingSuggestion && (
              <div className="loading-suggestion">
                <div className="spinner"></div>
                <p>Generating assessment suggestion...</p>
              </div>
            )}
            
            {suggestionError && (
              <div className="error-message">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12" y2="16"></line>
                </svg>
                {suggestionError}
              </div>
            )}
            
            {showSuggestion && suggestedAssessment && (
              <div className="suggestion-panel">
                <div className="suggestion-header">
                  <h3>Suggested Assessment</h3>
                  <div className="suggestion-actions">
                    <button className="suggestion-button accept" onClick={handleAcceptSuggestion}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                      Use This
                    </button>
                    <button className="suggestion-button edit" onClick={handleEditSuggestion}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                      Edit
                    </button>
                    <button className="suggestion-button refresh" onClick={handleNewSuggestion}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"></path>
                      </svg>
                      New Suggestion
                    </button>
                  </div>
                </div>
                <div className="suggestion-content">
                  <p>{suggestedAssessment}</p>
                </div>
              </div>
            )}
            
            <div className="input-group">
              <label htmlFor="doctorAssessment">
                Enter your clinical assessment:
                {isEditingSuggestion && (
                  <span className="editing-label">(Editing suggestion)</span>
                )}
              </label>
              <textarea
                id="doctorAssessment"
                rows={6}
                placeholder="Enter your professional assessment based on the medical imaging results and clinical document analysis..."
                value={doctorInput}
                onChange={(e) => setDoctorInput(e.target.value)}
                className="doctor-assessment-input"
              ></textarea>
            </div>
            
            {reportError && (
              <div className="error-message">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12" y2="16"></line>
                </svg>
                {reportError}
              </div>
            )}
            
            {/* Treatment Review Section */}
            {doctorInput.trim().length > 0 && (
              <div className="treatment-review-section">
                <h3>Treatment Review</h3>
                <p className="review-instruction">Review the automated treatment recommendations and make any necessary adjustments before finalizing the report.</p>
                
                {/* This would be populated with treatments from diagnoses that the doctor can modify */}
                <div className="treatments-review-list">
                  {diagnoses && diagnoses.disease_type && (
                    <>
                      {/* Treatment modification UI would go here */}
                      <div className="treatment-actions">
                        <button className="button secondary-button" onClick={() => setShowDoctorInput(false)}>
                          Back to Diagnosis
                        </button>
                        <button className="button primary-button" onClick={handleDoctorInputSubmit}>
                          {isGeneratingReport ? (
                            <>
                              <div className="spinner small"></div>
                              Finalizing Report...
                            </>
                          ) : (
                            <>
                              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                                <polyline points="22 4 12 14.01 9 11.01"></polyline>
                              </svg>
                              Validate and Generate Final Report
                            </>
                          )}
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultsPage;