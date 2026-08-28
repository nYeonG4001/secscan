import { ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./auth/AuthProvider";
import { ProtectedRoute, PublicOnlyRoute } from "./auth/RouteGuards";
import { AppShell } from "./components/AppShell";
import LoginPage from "./pages/LoginPage";
import CatalogPage from "./pages/CatalogPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import ProjectsPage from "./pages/ProjectsPage";
import AnalysisStatusPage from "./pages/AnalysisStatusPage";

function ProtectedPage({ children }: { children: ReactNode }) {
  return <ProtectedRoute><AppShell>{children}</AppShell></ProtectedRoute>;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<PublicOnlyRoute><LoginPage /></PublicOnlyRoute>} />
          <Route path="/projects" element={<ProtectedPage><ProjectsPage /></ProtectedPage>} />
          <Route path="/projects/:projectId" element={<ProtectedPage><ProjectDetailPage /></ProtectedPage>} />
          <Route path="/projects/:projectId/analyses/:analysisId" element={<ProtectedPage><AnalysisStatusPage /></ProtectedPage>} />
          <Route path="/catalog" element={<ProtectedPage><CatalogPage /></ProtectedPage>} />
          <Route path="/admin/projects" element={<Navigate to="/projects" replace />} />
          <Route path="/admin/upload" element={<Navigate to="/projects" replace />} />
          <Route path="*" element={<Navigate to="/projects" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
