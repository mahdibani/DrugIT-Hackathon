import React from "react";
import { useNavigate } from "react-router-dom";
import { AnalysisResult } from "../types";

interface ResultsPageProps {
  resultData: AnalysisResult | null;
}

const ResultsPage: React.FC<ResultsPageProps> = ({ resultData }) => {
  const navigate = useNavigate();

  if (!resultData) {
    return (
      <div className="results-page">
        <h2>No results available</h2>
        <button onClick={() => navigate("/")}>Back to Upload</button>
      </div>
    );
  }

  // Safely handle diagnosis with type checking
  const diagnosis = typeof resultData.diagnosis === 'string' 
    ? resultData.diagnosis 
    : "No diagnosis available";

  const isCritical = diagnosis.toLowerCase().includes("tumor") || 
                     diagnosis.toLowerCase().includes("cancer");

  return (
    <div className={`results-page ${isCritical ? "critical" : "normal"}`}>
      <h1>Analysis Results</h1>
      
      <div className="result-card">
        <div className="diagnosis">
          <h2>Diagnosis:</h2>
          <p className={isCritical ? "critical-text" : "normal-text"}>
            {diagnosis}
          </p>
          <p>Confidence: {resultData.confidence || "N/A"}</p>
        </div>

        <div className="care-pathway">
          <h3>Recommended Care Pathway:</h3>
          <p>{resultData.care_pathway || "Consult medical specialist"}</p>
        </div>

        <div className="advice">
          <h3>Medical Advice:</h3>
          <p>{resultData.advice || "Please consult a healthcare professional"}</p>
        </div>
      </div>

      <button 
        onClick={() => navigate("/")}
        className="upload-another"
      >
        Upload Another Image
      </button>
    </div>
  );
};

export default ResultsPage;