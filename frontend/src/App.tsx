import { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import UploadPage from "./components/UploadPage.tsx";
import ResultsPage from "./components/ResultsPage.tsx";

function App() {
  const [resultData, setResultData] = useState<any>(null);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<UploadPage setResultData={setResultData} />} />
        <Route path="/results" element={<ResultsPage resultData={resultData} />} />
      </Routes>
    </Router>
  );
}

export default App;
