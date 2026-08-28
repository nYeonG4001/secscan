import { AxiosError } from "axios";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/auth";
import { createAnalysis } from "../api/analyses";
import { useAuth } from "../auth/useAuth";
import { ActionDrawer } from "../components/ActionDrawer";
import { FORBIDDEN_MESSAGE, SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";
import { Project } from "./ProjectsPage";
import { SourceUploadDrawer } from "./SourceUploadDrawer";

interface ProjectAccess {
  id: number;
  user_id: number;
  user_email: string;
}

interface Analysis {
  id: number;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
}

interface ConflictBody {
  code?: string;
  analysis_id?: number;
}

const NOT_FOUND_MESSAGE = "요청한 정보를 찾을 수 없습니다.";

function errorStatus(error: unknown) {
  return (error as AxiosError).response?.status;
}

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { user, clearUser } = useAuth();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [accesses, setAccesses] = useState<ProjectAccess[]>([]);
  const [showAccessPanel, setShowAccessPanel] = useState(false);
  const [showSourceUploadPanel, setShowSourceUploadPanel] = useState(false);
  const [hasActiveAnalysis, setHasActiveAnalysis] = useState(false);
  const [email, setEmail] = useState("");
  const [accessError, setAccessError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarting, setAnalysisStarting] = useState(false);
  const [loading, setLoading] = useState(true);

  const handleRequestError = useCallback((requestError: unknown) => {
    const status = errorStatus(requestError);
    if (status === 401) {
      clearUser();
      navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } });
      return;
    }
    if (status === 403) setError(FORBIDDEN_MESSAGE);
    else if (status === 404) setError(NOT_FOUND_MESSAGE);
    else setError("요청을 처리하지 못했습니다. 다시 시도해 주세요.");
  }, [clearUser, navigate]);

  async function loadAccesses() {
    if (!projectId) return;
    try {
      const response = await api.get<ProjectAccess[]>(`/projects/${projectId}/access`);
      setAccesses(response.data);
    } catch (requestError) {
      const status = errorStatus(requestError);
      if (status === 401) handleRequestError(requestError);
      else if (status === 403) setAccessError(FORBIDDEN_MESSAGE);
      else if (status === 404) setAccessError(NOT_FOUND_MESSAGE);
      else setAccessError("접근권한을 불러오지 못했습니다. 다시 시도해 주세요.");
    }
  }

  const loadProject = useCallback(async () => {
    if (!projectId) return;
    try {
      const response = await api.get<Project>(`/projects/${projectId}`);
      setProject(response.data);
    } catch (requestError) {
      handleRequestError(requestError);
      throw requestError;
    }
  }, [handleRequestError, projectId]);

  const loadAnalysisStatus = useCallback(async () => {
    if (!projectId) return;
    try {
      const response = await api.get<Analysis[]>("/analyses/", { params: { project_id: projectId } });
      const analyses = Array.isArray(response.data) ? response.data : [];
      setHasActiveAnalysis(analyses.some((analysis) => analysis.status === "PENDING" || analysis.status === "RUNNING"));
    } catch (requestError) {
      const status = errorStatus(requestError);
      if (status === 401 || status === 403 || status === 404) handleRequestError(requestError);
    }
  }, [handleRequestError, projectId]);

  useEffect(() => {
    let active = true;
    void Promise.all([loadProject(), loadAnalysisStatus()])
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [loadAnalysisStatus, loadProject]);

  async function openAccessPanel() {
    setAccessError(null);
    setShowAccessPanel(true);
    await loadAccesses();
  }

  function closeAccessPanel() {
    setShowAccessPanel(false);
    setEmail("");
    setAccessError(null);
  }

  function closeSourceUploadPanel() {
    setShowSourceUploadPanel(false);
  }

  async function refreshProjectAfterUpload() {
    await Promise.all([loadProject(), loadAnalysisStatus()]);
  }

  async function startAnalysis() {
    if (!projectId) return;
    setError(null);
    setAnalysisStarting(true);
    try {
      const analysis = await createAnalysis(projectId);
      navigate(`/projects/${projectId}/analyses/${analysis.id}`);
    } catch (requestError) {
      const status = errorStatus(requestError);
      const body = (requestError as AxiosError<ConflictBody>).response?.data;
      if (status === 401) handleRequestError(requestError);
      else if (status === 409 && body?.code === "ANALYSIS_ACTIVE" && body.analysis_id) {
        navigate(`/projects/${projectId}/analyses/${body.analysis_id}`);
      } else if (status === 409 && body?.code === "SOURCE_UPLOAD_IN_PROGRESS") {
        setError("소스 업로드가 진행 중입니다. 완료 후 다시 시도해 주세요.");
      } else if (status === 403) setError(FORBIDDEN_MESSAGE);
      else if (status === 404) setError(NOT_FOUND_MESSAGE);
      else setError("분석 실행을 시작하지 못했습니다. 다시 시도해 주세요.");
    } finally {
      setAnalysisStarting(false);
    }
  }

  async function grantAccess(event: FormEvent) {
    event.preventDefault();
    if (!projectId) return;
    setAccessError(null);
    try {
      await api.post(`/projects/${projectId}/access`, { email });
      setEmail("");
      await loadAccesses();
    } catch (requestError) {
      const status = errorStatus(requestError);
      if (status === 409) setAccessError("이미 접근권한이 있는 사용자입니다.");
      else if (status === 422) setAccessError("일반 사용자 이메일을 입력해 주세요.");
      else if (status === 401) handleRequestError(requestError);
      else if (status === 404) setAccessError(NOT_FOUND_MESSAGE);
      else setAccessError("접근권한을 부여하지 못했습니다. 다시 시도해 주세요.");
    }
  }

  async function revokeAccess(userId: number) {
    if (!projectId) return;
    setAccessError(null);
    try {
      await api.delete(`/projects/${projectId}/access/${userId}`);
      await loadAccesses();
    } catch (requestError) {
      const status = errorStatus(requestError);
      if (status === 401) handleRequestError(requestError);
      else if (status === 404) setAccessError(NOT_FOUND_MESSAGE);
      else if (status === 403) setAccessError(FORBIDDEN_MESSAGE);
      else setAccessError("접근권한을 해제하지 못했습니다. 다시 시도해 주세요.");
    }
  }

  if (loading) return <p>프로젝트를 불러오는 중...</p>;
  if (error && !project) return <p role="alert">{error}</p>;
  if (!project) return <p role="alert">{NOT_FOUND_MESSAGE}</p>;

  return (
    <section>
      <Link to="/projects" className="text-sm">프로젝트 목록</Link>
      <div className="mt-4 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          {project.description && <p className="mt-2 text-gray-600">{project.description}</p>}
        </div>
        {user?.role === "ADMIN" && (
          <div className="flex gap-2">
            <div>
              <button
                type="button"
                onClick={() => setShowSourceUploadPanel(true)}
                disabled={hasActiveAnalysis}
                className="rounded border px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
              >
                소스 등록
              </button>
              {hasActiveAnalysis && <p className="mt-1 text-xs text-gray-600">분석이 끝난 뒤 업로드할 수 있습니다.</p>}
            </div>
            <div>
              <button
                type="button"
                onClick={() => void startAnalysis()}
                disabled={project.source_status !== "REGISTERED" || hasActiveAnalysis || analysisStarting}
                className="rounded border px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
              >
                {analysisStarting ? "분석 요청 중..." : "분석 실행"}
              </button>
              {project.source_status !== "REGISTERED" && <p className="mt-1 text-xs text-gray-600">소스를 등록한 뒤 분석할 수 있습니다.</p>}
              {hasActiveAnalysis && <p className="mt-1 text-xs text-gray-600">진행 중인 분석이 있습니다.</p>}
            </div>
            <button type="button" onClick={openAccessPanel} className="rounded border px-3 py-2 text-sm">접근권한 관리</button>
          </div>
        )}
      </div>
      <div className="mt-6 rounded border p-4">
        <h2 className="text-sm font-semibold">소스 정보</h2>
        <p className="mt-2 text-sm">상태: {project.source_status === "REGISTERED" ? "등록됨" : "등록 필요"}</p>
        <p className="mt-1 text-sm text-gray-600">감지된 언어: {project.target_languages?.join(", ") || "없음"}</p>
      </div>
      {error && <p role="alert" className="mt-4 text-sm text-red-600">{error}</p>}
      {showSourceUploadPanel && user?.role === "ADMIN" && (
        <SourceUploadDrawer
          projectId={projectId ?? ""}
          onClose={closeSourceUploadPanel}
          onProjectRefresh={refreshProjectAfterUpload}
          onRequestError={handleRequestError}
        />
      )}
      {showAccessPanel && user?.role === "ADMIN" && (
        <ActionDrawer
          title="접근권한 관리"
          onClose={closeAccessPanel}
          footer={<button type="submit" form="grant-access-form" className="w-full rounded bg-black px-3 py-2 text-sm text-white">접근권한 부여</button>}
        >
          {accessError && <p role="alert" className="mb-4 text-sm text-red-600">{accessError}</p>}
          <form id="grant-access-form" onSubmit={grantAccess}>
            <label htmlFor="access-email" className="text-sm font-medium">사용자 이메일</label>
            <input id="access-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required className="mt-2 w-full rounded border px-3 py-2" />
          </form>
          <ul className="mt-6 space-y-2">
            {accesses.map((access) => (
              <li key={access.id} className="flex items-center justify-between gap-3 border-b pb-2 text-sm">
                <span>{access.user_email}</span>
                <button type="button" onClick={() => revokeAccess(access.user_id)} className="rounded border px-2 py-1">해제</button>
              </li>
            ))}
          </ul>
        </ActionDrawer>
      )}
    </section>
  );
}
