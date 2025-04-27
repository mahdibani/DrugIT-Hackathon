import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { AnalysisResult } from "../types";
import "../App.css";

type DiseaseType = 'brain_tumor' | 'pneumonia' | 'malaria';

const UploadPage: React.FC<{ setResultData: (data: AnalysisResult | null) => void }> = ({ setResultData }) => {
  const navigate = useNavigate();
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [diseaseType, setDiseaseType] = useState<DiseaseType>("brain_tumor");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!imageFile || !pdfFile) {
      setError("Please upload both required files");
      return;
    }

    setIsLoading(true);
    setError("");
    setResultData(null);

    try {
      const formData = new FormData();
      formData.append("image_file", imageFile);
      formData.append("pdf_file", pdfFile);
      formData.append("disease_type", diseaseType);

      const response = await api.post<AnalysisResult>("/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 45000
      });

      setResultData(response.data);
      navigate("/results");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Analysis failed. Please check files and try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="upload-page">
        <header className="header">
          <h1>Medical Insight Platform</h1>
          <p className="subtitle">Integrated Imaging and Clinical Document Analysis</p>
        </header>

        <div className="protocol-selector">
          <label>Select Analysis Protocol:</label>
          <select
            className="select-disease"
            value={diseaseType}
            onChange={(e) => {
              setDiseaseType(e.target.value as DiseaseType);
              setImageFile(null);
              setError("");
            }}
          >
            <option value="brain_tumor">Neuroimaging Analysis</option>
            <option value="pneumonia">Pulmonary Assessment</option>
            <option value="malaria">Hematological Screening</option>
          </select>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="file-upload-section">
            {/* Medical Imaging Upload */}
            <div className="upload-group">
              <div className="upload-title">Medical Imaging File</div>
              <div className="upload-box">
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setImageFile(e.target.files?.[0] || null)}
                />
                {imageFile && (
                  <div className="file-preview">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                      <circle cx="8.5" cy="8.5" r="1.5"></circle>
                      <polyline points="21 15 16 10 5 21"></polyline>
                    </svg>
                    <span>{imageFile.name}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Clinical Document Upload */}
            <div className="upload-group">
              <div className="upload-title">Clinical Document (PDF)</div>
              <div className="upload-box">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                />
                {pdfFile && (
                  <div className="file-preview">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <path d="M10 9H8"></path>
                      <path d="M16 13H8"></path>
                      <path d="M16 17H8"></path>
                    </svg>
                    <span>{pdfFile.name}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button 
            type="submit" 
            className={`button ${isLoading ? "loading" : ""}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Analyzing...
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                Start Analysis
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default UploadPage;
