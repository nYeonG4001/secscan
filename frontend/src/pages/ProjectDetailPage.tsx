import { AxiosError } from "axios";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/auth";
import { createAnalysis } from "../api/analyses";
import type { Analysis } from "../api/analyses";
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

interface AccessUserSearch {
  user_id: number;
  user_email: string;
  already_granted: boolean;
}

interface ConflictBody {
  code?: string;
  analysis_id?: number;
}

const NOT_FOUND_MESSAGE = "요청한 정보를 찾을 수 없습니다.";

function errorStatus(error: unknown) {
  return (error as AxiosError).response?.status;
}

function analysisStatusPresentation(status: Analysis["status"]) {
  if (status === "RUNNING") return { label: "분석 진행 중", className: "secscan-status-active" };
  if (status === "PENDING") return { label: "분석 대기", className: "secscan-status-neutral" };
  if (status === "COMPLETED") return { label: "분석 완료", className: "secscan-status-success" };
  return { label: "분석 실패", className: "secscan-status-failed" };
}

function formatAnalysisTime(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const pad = (number: number) => String(number).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function ManageIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
      <path d="M12 15.25A3.25 3.25 0 1 0 12 8.75a3.25 3.25 0 0 0 0 6.5Z" />
      <path d="m19.2 13.5 1.1.85-1.8 3.12-1.32-.55a7.1 7.1 0 0 1-1.45.84L15.55 19h-3.6l-.18-1.24a7.1 7.1 0 0 1-1.45-.84L9 17.47l-1.8-3.12 1.1-.85a7.3 7.3 0 0 1 0-1.68l-1.1-.85L9 7.85l1.32.55a7.1 7.1 0 0 1 1.45-.84L11.95 6h3.6l.18 1.24a7.1 7.1 0 0 1 1.45.84l1.32-.55 1.8 3.12-1.1.85a7.3 7.3 0 0 1 0 1.68Z" />
    </svg>
  );
}

function SourceIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
      <path d="M12 15V3" />
      <path d="m8.5 6.5 3.5-3.5 3.5 3.5" />
      <path d="M5 13.5v4.25A2.25 2.25 0 0 0 7.25 20h9.5A2.25 2.25 0 0 0 19 17.75V13.5" />
    </svg>
  );
}

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { user, clearUser } = useAuth();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [accesses, setAccesses] = useState<ProjectAccess[]>([]);
  const [showManagePanel, setShowManagePanel] = useState(false);
  const [showSourceUploadPanel, setShowSourceUploadPanel] = useState(false);
  const [hasActiveAnalysis, setHasActiveAnalysis] = useState(false);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [email, setEmail] = useState("");
  const [searchedUser, setSearchedUser] = useState<AccessUserSearch | null>(null);
  const [accessError, setAccessError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarting, setAnalysisStarting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [projectSaving, setProjectSaving] = useState(false);

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

  async function openManagePanel() {
    setAccessError(null);
    setSearchError(null);
    setEditName(project?.name ?? "");
    setEditDescription(project?.description ?? "");
    setShowManagePanel(true);
    await loadAccesses();
  }

  function closeManagePanel() {
    if (hasProjectChanges && !window.confirm("저장하지 않은 변경사항이 있습니다. 닫을까요?")) return;
    setShowManagePanel(false);
    setEmail("");
    setAccessError(null);
    setSearchError(null);
    setSearchedUser(null);
  }

  function closeSourceUploadPanel() {
    setShowSourceUploadPanel(false);
  }

  function openSourceAction() {
    setShowSourceUploadPanel(true);
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

  async function grantAccess(userToGrant = searchedUser) {
    if (!projectId || !userToGrant || userToGrant.already_granted) return;
    setAccessError(null);
    try {
      await api.post(`/projects/${projectId}/access`, { email });
      setEmail("");
      setSearchedUser(null);
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
    if (!window.confirm("이 사용자의 프로젝트 접근권한을 해제할까요?")) return;
    setAccessError(null);
    setSearchError(null);
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

  async function searchAccessUser() {
    if (!projectId || !email) return;
    setAccessError(null);
    setSearchError(null);
    setSearchedUser(null);
    try {
      const response = await api.get<AccessUserSearch>(`/projects/${projectId}/access/user`, { params: { email } });
      setSearchedUser(response.data);
      if (response.data.already_granted) setAccessError("이미 접근권한이 부여된 사용자입니다.");
      else if (window.confirm(`${response.data.user_email} 사용자에게 프로젝트 접근권한을 부여하시겠습니까?`)) await grantAccess(response.data);
    } catch (requestError) {
      const status = errorStatus(requestError);
      if (status === 401) handleRequestError(requestError);
      else if (status === 403) setAccessError(FORBIDDEN_MESSAGE);
      else if (status === 404) setSearchError("해당 사용자를 찾을 수 없습니다.");
      else if (status === 422) setSearchError("일반 사용자 이메일을 입력해 주세요.");
      else setSearchError("사용자를 검색하지 못했습니다. 다시 시도해 주세요.");
    }
  }

  async function updateProjectDetails(event: FormEvent) {
    event.preventDefault();
    if (!project || !hasProjectChanges || projectSaving) return;
    setProjectSaving(true);
    const startedAt = Date.now();
    try {
      const updated = await updateProject(project.id, { name: editName, description: editDescription || null });
      const remainingDelay = Math.max(0, 300 - (Date.now() - startedAt));
      if (remainingDelay > 0) await new Promise((resolve) => setTimeout(resolve, remainingDelay));
      setProject(updated);
      setShowManagePanel(false);
    } catch (requestError) {
      handleRequestError(requestError);
    } finally {
      setProjectSaving(false);
    }
  }

  if (loading) return <section className="secscan-loading-state" aria-busy="true">프로젝트를 불러오는 중...</section>;
  if (error && !project) return <section role="alert" className="secscan-error-state">{error}</section>;
  if (!project) return <section role="alert" className="secscan-error-state">{NOT_FOUND_MESSAGE}</section>;

  const hasProjectChanges = project !== null && (editName !== project.name || editDescription !== (project.description ?? ""));

  return (
    <section className="min-w-0">
      <nav aria-label="경로" className="flex min-w-0 items-center gap-2 text-sm text-secscan-muted">
        <Link to="/projects" className="shrink-0 underline decoration-secscan-border underline-offset-4 hover:text-secscan-foreground">프로젝트</Link>
        <span aria-hidden="true">&gt;</span>
        <span className="min-w-0 truncate text-secscan-foreground" title={project.name}>{project.name}</span>
      </nav>
      <div className="mt-5 flex min-w-0 flex-col gap-2 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <h1 className="break-words text-3xl font-bold tracking-tight">{project.name}</h1>
          {project.description && <p className="mt-3 max-w-2xl break-words text-sm text-secscan-muted">{project.description}</p>}
          <div className="mt-4 flex min-w-0 flex-wrap gap-2">
            {project.target_languages?.map((language) => <span key={language} className="secscan-status-badge secscan-status-neutral">{language}</span>)}
          </div>
        </div>
        {user?.role === "ADMIN" && (
          <div className="flex min-w-0 flex-col items-stretch xl:items-end">
          <div className="-mt-2 flex min-w-0 flex-col gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={openManagePanel}
                className="secscan-secondary-button w-full sm:w-auto"
              >
                <span className="inline-flex items-center gap-2"><ManageIcon />관리</span>
              </button>
              <button
                type="button"
                onClick={openSourceAction}
                disabled={hasActiveAnalysis || analysisStarting}
                className="secscan-primary-button w-full disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
              >
                <span className="inline-flex items-center gap-2"><SourceIcon />{analysisStarting ? "요청 중..." : "분석"}</span>
              </button>
            </div>
          </div>
        )}
      </div>
      {analyses.length === 0 ? (
        <div className="secscan-empty-state mt-7 text-sm">아직 분석 이력이 없습니다.</div>
      ) : (
        <div className="mt-2">
          <h2 className="text-xl font-bold">분석 이력</h2>
          <div className="secscan-panel mt-4 overflow-x-auto">
              <table className="min-w-[780px] w-full border-collapse text-left text-sm" aria-label="분석 이력">
                <thead className="border-b border-secscan-border bg-secscan-surface-2 text-xs font-semibold text-secscan-muted">
                  <tr>
                    <th scope="col" className="px-5 py-3">분석 요청 시각</th>
                    <th scope="col" className="px-5 py-3">상태</th>
                    <th scope="col" className="px-5 py-3">시작 시각</th>
                    <th scope="col" className="px-5 py-3">완료 시각</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-secscan-border">
                  {analyses.map((analysis) => {
                    const presentation = analysisStatusPresentation(analysis.status);
                    return (
                      <tr
                        key={analysis.id}
                        tabIndex={0}
                        onClick={() => navigate(`/projects/${project.id}/analyses/${analysis.id}`)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            navigate(`/projects/${project.id}/analyses/${analysis.id}`);
                          }
                        }}
                        className="cursor-pointer transition-colors hover:bg-secscan-surface-2 focus-visible:bg-secscan-surface-2"
                      >
                        <td className="whitespace-nowrap px-5 py-4 text-secscan-foreground">{formatAnalysisTime(analysis.created_at)}</td>
                        <td className="px-5 py-4"><span className={`secscan-status-badge ${presentation.className}`}>{presentation.label}</span></td>
                        <td className="whitespace-nowrap px-5 py-4 text-secscan-muted">{formatAnalysisTime(analysis.started_at)}</td>
                        <td className="whitespace-nowrap px-5 py-4 text-secscan-muted">{formatAnalysisTime(analysis.completed_at)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
          </div>
        </div>
      )}
      {error && <p role="alert" className="secscan-error-state mt-5 text-sm">{error}</p>}
      {showSourceUploadPanel && user?.role === "ADMIN" && (
        <SourceUploadDrawer
          projectId={projectId ?? ""}
          hasExistingSource={project.source_status === "REGISTERED"}
          onClose={closeSourceUploadPanel}
          onProjectRefresh={refreshProjectAfterUpload}
          onRequestError={handleRequestError}
          onAnalysis={() => { setShowSourceUploadPanel(false); void startAnalysis(); }}
        />
      )}
      {showManagePanel && user?.role === "ADMIN" && (
        <ActionDrawer
          title="프로젝트 관리"
          onClose={closeManagePanel}
          hideDividers
        >
          {accessError && <p role="alert" className="secscan-error-state mb-4 text-sm">{accessError}</p>}
          <form id="edit-project" onSubmit={updateProjectDetails} className="-mt-2 space-y-4">
            <label className="block text-sm font-medium">프로젝트 이름<input required value={editName} onChange={(event) => setEditName(event.target.value)} className="mt-2" /></label>
            <label className="block text-sm font-medium">설명<textarea value={editDescription} onChange={(event) => setEditDescription(event.target.value)} className="mt-2" /></label>
            <button type="submit" disabled={!hasProjectChanges || projectSaving} className="secscan-primary-button w-full disabled:cursor-not-allowed disabled:opacity-45">{projectSaving ? "저장 중..." : "저장"}</button>
          </form>
          <section className="mt-12 border-t border-secscan-border pt-8">
            <h2 className="text-xl font-bold">사용자 접근권한</h2>
            <h3 className="mt-4 text-sm font-semibold">권한 부여</h3>
            <div className="mt-3 flex gap-2">
              <input id="access-email" type="email" value={email} onChange={(event) => { setEmail(event.target.value); setSearchedUser(null); setAccessError(null); setSearchError(null); }} placeholder="사용자 이메일" required />
              <button type="button" onClick={() => void searchAccessUser()} className="secscan-secondary-button shrink-0">검색</button>
            </div>
            {searchError && <p role="alert" className="mt-2 text-sm text-red-400">{searchError}</p>}
            <div className="mt-6" />
          </section>
          <section className="mt-8">
            <h3 className="text-sm font-semibold">접근 권한이 있는 사용자</h3>
            {accesses.length === 0 ? (
              <p className="mt-4 text-sm text-secscan-muted">권한이 부여된 사용자가 없습니다.</p>
            ) : (
              <ul className="mt-4 space-y-2">
                {accesses.map((access) => (
              <li key={access.id} className="flex min-w-0 items-center justify-between gap-3 border-b border-secscan-border pb-3 text-sm">
                <span className="min-w-0 break-all">{access.user_email}</span>
                <button type="button" onClick={() => revokeAccess(access.user_id)} className="secscan-destructive-button shrink-0 px-2 py-1">해제</button>
              </li>
                ))}
              </ul>
            )}
          </section>
        </ActionDrawer>
      )}
    </section>
  );
}
