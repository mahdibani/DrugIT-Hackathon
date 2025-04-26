import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { AnalysisResult } from "../types";
type DiseaseType = 'brain_tumor' | 'breast_cancer' | 'pneumonia' | 'skin_cancer' | 'malaria';

interface UploadPageProps {
  setResultData: (data: AnalysisResult | null) => void;
}

const diseaseRequirements: Record<DiseaseType, string> = {
  brain_tumor: "MRI/CT scan images (PNG/JPG)",
  breast_cancer: "Mammography images (PNG/JPG)",
  pneumonia: "Chest X-ray images (PNG/JPG)",
  skin_cancer: "Dermatoscopy images (PNG/JPG)",
  malaria: "Blood smear microscopy images (PNG/JPG)"
};

const UploadPage: React.FC<UploadPageProps> = ({ setResultData }) => {
  
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [diseaseType, setDiseaseType] = useState("brain_tumor");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file");
      return;
    }

    setIsLoading(true);
    setError("");
    setResultData(null); // Clear previous results

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("disease_type", diseaseType);

      const response = await api.post<AnalysisResult>("/predict/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 30000
      });

      if (response.data.error) {
        throw new Error(response.data.error);
      }

      setResultData(response.data);
      navigate("/results");
    } catch (err: any) {
      setResultData(null);
      setError(err.response?.data?.detail || 
              err.message || 
              "Analysis failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-page">
      <h1>Medical Image Analysis</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Select Condition:</label>
          <select
            value={diseaseType}
            onChange={(e) => {
              setDiseaseType(e.target.value);
              setFile(null);
              setError("");
            }}
          >
            <option value="brain_tumor">Brain Tumor</option>
            <option value="breast_cancer">Breast Cancer</option>
            <option value="pneumonia">Pneumonia</option>
            <option value="skin_cancer">Skin Cancer</option>
            <option value="malaria">Malaria</option>
          </select>
        </div>

        <div className="form-group">
          <label>Upload Image:</label>
          <input
            type="file"
            onChange={(e) => {
              setFile(e.target.files?.[0] || null);
              setError("");
            }}
            accept="image/png, image/jpeg"
          />
          <p className="file-requirements">
           
          </p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <button 
          type="submit" 
          disabled={isLoading}
          className={isLoading ? "loading" : ""}
        >
          {isLoading ? (
            <>
              <span className="spinner"></span>
              Analyzing...
            </>
          ) : (
            "Analyze Image"
          )}
        </button>
      </form>
    </div>
  );
};

export default UploadPage;