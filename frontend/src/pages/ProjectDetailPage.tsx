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
import { updateProject } from "../api/projects";

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

function sourceStatusLabel(status: Project["source_status"]) {
  return status === "REGISTERED" ? "등록됨" : "등록 필요";
}

function analysisStatusPresentation(status: Analysis["status"]) {
  if (status === "RUNNING") return { label: "분석 진행 중", className: "secscan-status-active" };
  if (status === "PENDING") return { label: "분석 대기", className: "secscan-status-neutral" };
  if (status === "COMPLETED") return { label: "분석 완료", className: "secscan-status-success" };
  return { label: "분석 실패", className: "secscan-status-failed" };
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
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [email, setEmail] = useState("");
  const [accessError, setAccessError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarting, setAnalysisStarting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showEditPanel, setShowEditPanel] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

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
      setAnalyses(analyses);
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

  async function updateProjectDetails(event: FormEvent) {
    event.preventDefault();
    if (!project) return;
    try {
      const updated = await updateProject(project.id, { name: editName, description: editDescription || null });
      setProject(updated);
      setShowEditPanel(false);
    } catch (requestError) { handleRequestError(requestError); }
  }

  if (loading) return <section className="secscan-loading-state" aria-busy="true">프로젝트를 불러오는 중...</section>;
  if (error && !project) return <section role="alert" className="secscan-error-state">{error}</section>;
  if (!project) return <section role="alert" className="secscan-error-state">{NOT_FOUND_MESSAGE}</section>;

  const currentAnalysis = analyses.find((analysis) => analysis.status === "RUNNING" || analysis.status === "PENDING") ?? analyses[0];
  const currentStatus = currentAnalysis ? analysisStatusPresentation(currentAnalysis.status) : null;
  const sourceRegistered = project.source_status === "REGISTERED";

  return (
    <section className="min-w-0">
      <nav aria-label="경로" className="flex min-w-0 items-center gap-2 text-sm text-secscan-muted">
        <Link to="/projects" className="shrink-0 underline decoration-secscan-border underline-offset-4 hover:text-secscan-foreground">프로젝트</Link>
        <span aria-hidden="true">&gt;</span>
        <span className="min-w-0 truncate text-secscan-foreground" title={project.name}>{project.name}</span>
      </nav>
      <div className="mt-5 flex min-w-0 flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <h1 className="break-words text-3xl font-bold tracking-tight">{project.name}</h1>
          {project.description && <p className="mt-3 max-w-2xl break-words text-sm text-secscan-muted">{project.description}</p>}
          <div className="mt-4 flex min-w-0 flex-wrap gap-2">
            {project.target_languages?.map((language) => <span key={language} className="secscan-status-badge secscan-status-neutral">{language}</span>)}
          </div>
        </div>
        {user?.role === "ADMIN" && (
          <div className="flex min-w-0 flex-col items-stretch gap-3 xl:items-end">
            <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-end">
              <div className="min-w-0">
                <button
                  type="button"
                  onClick={() => setShowSourceUploadPanel(true)}
                  disabled={hasActiveAnalysis}
                  className={`${sourceRegistered ? "secscan-secondary-button" : "secscan-primary-button"} w-full disabled:cursor-not-allowed disabled:opacity-50`}
                >
                  {sourceRegistered ? "소스 교체" : "소스 등록"}
                </button>
                {hasActiveAnalysis && <p className="mt-2 max-w-xs break-words text-xs text-red-300">분석이 끝난 뒤 업로드할 수 있습니다.</p>}
                {!sourceRegistered && !hasActiveAnalysis && <p className="mt-2 max-w-xs break-words text-xs text-secscan-muted">소스를 등록한 뒤 분석할 수 있습니다.</p>}
              </div>
              {sourceRegistered && !hasActiveAnalysis && (
                <button
                  type="button"
                  onClick={() => void startAnalysis()}
                  disabled={analysisStarting}
                  className="secscan-primary-button disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {analysisStarting ? "분석 요청 중..." : "분석 실행"}
                </button>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2 border-t border-secscan-border pt-3 text-sm xl:justify-end">
              <span className="mr-1 text-xs font-semibold text-secscan-muted">관리</span>
              <button type="button" onClick={() => { setEditName(project.name); setEditDescription(project.description ?? ""); setShowEditPanel(true); }} className="secscan-secondary-button px-3 py-1.5">프로젝트 수정</button>
              <button type="button" onClick={openAccessPanel} className="secscan-secondary-button px-3 py-1.5">접근권한 관리</button>
            </div>
          </div>
        )}
      </div>
      <div className="secscan-panel mt-7 flex min-w-0 flex-col gap-5 p-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="min-w-0">
          <p className="text-sm font-semibold">소스 등록 상태</p>
          <p className="mt-2 text-sm text-secscan-muted">소스 등록 후 분석을 실행할 수 있습니다.</p>
        </div>
        <div className="min-w-0 shrink-0">
          <span className={`secscan-status-badge ${project.source_status === "REGISTERED" ? "secscan-status-success" : "secscan-status-neutral"}`}>
            {sourceStatusLabel(project.source_status)}
          </span>
        </div>
      </div>
      {analyses.length === 0 ? (
        <div className="secscan-empty-state mt-5 text-sm">아직 분석 이력이 없습니다.</div>
      ) : (
        <>
          <div className="secscan-panel mt-5 flex min-w-0 flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div className="min-w-0">
              <p className="text-sm font-semibold">{hasActiveAnalysis ? "진행 중인 분석" : "최근 분석 상태"}</p>
              {hasActiveAnalysis && <p className="mt-2 text-sm text-secscan-muted">분석이 끝나면 결과를 확인할 수 있습니다.</p>}
            </div>
            <div className="flex min-w-0 flex-wrap items-center gap-3">
              {currentStatus && <span className={`secscan-status-badge ${currentStatus.className}`}>{currentStatus.label}</span>}
              {currentAnalysis && <Link to={`/projects/${project.id}/analyses/${currentAnalysis.id}`} className="secscan-secondary-button shrink-0 px-3 py-1.5 text-xs">{hasActiveAnalysis ? "분석 상태 보기" : "최근 분석 보기"}</Link>}
            </div>
          </div>
          <div className="mt-8">
            <h2 className="text-xl font-bold">분석 이력</h2>
          <ul className="secscan-panel mt-4 overflow-hidden divide-y divide-secscan-border">
            {analyses.map((analysis) => {
              const presentation = analysisStatusPresentation(analysis.status);
              return (
                <li key={analysis.id} className="min-w-0">
                  <Link to={`/projects/${project.id}/analyses/${analysis.id}`} className="secscan-panel-interactive flex min-w-0 flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between focus-visible:relative">
                    <span className="min-w-0 break-words text-sm font-medium">분석 #{analysis.id} · {analysis.status}</span>
                    <span className={`secscan-status-badge shrink-0 ${presentation.className}`}>{presentation.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
          </div>
        </>
      )}
      {error && <p role="alert" className="secscan-error-state mt-5 text-sm">{error}</p>}
      {showSourceUploadPanel && user?.role === "ADMIN" && (
        <SourceUploadDrawer
          projectId={projectId ?? ""}
          onClose={closeSourceUploadPanel}
          onProjectRefresh={refreshProjectAfterUpload}
          onRequestError={handleRequestError}
        />
      )}
      {showEditPanel && user?.role === "ADMIN" && <ActionDrawer title="프로젝트 수정" onClose={() => setShowEditPanel(false)} footer={<button type="submit" form="edit-project" className="secscan-primary-button w-full">저장</button>}><form id="edit-project" onSubmit={updateProjectDetails} className="space-y-4"><label className="block text-sm font-medium">프로젝트 이름<input required value={editName} onChange={(event) => setEditName(event.target.value)} className="mt-2" /></label><label className="block text-sm font-medium">설명<textarea value={editDescription} onChange={(event) => setEditDescription(event.target.value)} className="mt-2" /></label></form></ActionDrawer>}
      {showAccessPanel && user?.role === "ADMIN" && (
        <ActionDrawer
          title="접근권한 관리"
          onClose={closeAccessPanel}
          footer={<button type="submit" form="grant-access-form" className="secscan-primary-button w-full">접근권한 부여</button>}
        >
          {accessError && <p role="alert" className="secscan-error-state mb-4 text-sm">{accessError}</p>}
          <form id="grant-access-form" onSubmit={grantAccess}>
            <label htmlFor="access-email" className="text-sm font-medium">사용자 이메일</label>
            <input id="access-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required className="mt-2 w-full rounded border px-3 py-2" />
          </form>
          <ul className="mt-6 space-y-2">
            {accesses.map((access) => (
              <li key={access.id} className="flex min-w-0 items-center justify-between gap-3 border-b border-secscan-border pb-3 text-sm">
                <span className="min-w-0 break-all">{access.user_email}</span>
                <button type="button" onClick={() => revokeAccess(access.user_id)} className="secscan-destructive-button shrink-0 px-2 py-1">해제</button>
              </li>
            ))}
          </ul>
        </ActionDrawer>
      )}
    </section>
  );
}
