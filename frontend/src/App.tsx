// src/App.tsx
import { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import UploadPage from "./components/UploadPage";
import ResultsPage from "./components/ResultsPage";
import { AnalysisResult } from "./types";

function App() {
  const [resultData, setResultData] = useState<AnalysisResult | null>(null);

  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route 
            path="/" 
            element={<UploadPage setResultData={setResultData} />} 
          />
          <Route 
            path="/results" 
            element={<ResultsPage resultData={resultData} />} 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;