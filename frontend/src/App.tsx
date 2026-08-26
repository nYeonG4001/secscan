import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import AdminProjectsPage from "./pages/AdminProjectsPage";
import AdminUploadPage from "./pages/AdminUploadPage";
import AnalysisStatusPage from "./pages/AnalysisStatusPage";
import FindingsPage from "./pages/FindingsPage";
import CatalogPage from "./pages/CatalogPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/admin/projects" element={<AdminProjectsPage />} />
        <Route path="/admin/upload" element={<AdminUploadPage />} />
        <Route path="/analyses/:analysisId/status" element={<AnalysisStatusPage />} />
        <Route path="/analyses/:analysisId/findings" element={<FindingsPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
