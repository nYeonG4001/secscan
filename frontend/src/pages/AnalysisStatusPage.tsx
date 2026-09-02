import { AxiosError } from "axios";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Analysis, createAnalysis, getAnalysis } from "../api/analyses";
import { api } from "../api/auth";
import { useAuth } from "../auth/useAuth";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";
import FindingsPage from "./FindingsPage";

const POLL_INTERVAL_MS = 3_000;
const MIN_ANALYSIS_DISPLAY_MS = 6_000;
const USER_FAILURE_MESSAGE = "분석을 완료하지 못했습니다. 관리자에게 문의하세요.";

function formatAnalysisTime(value?: string | null) {
  if (!value) return "-";
  return value.replace("T", " ").slice(0, 19);
}

function formatDuration(start?: string | null, end?: string | null) {
  if (!start) return "-";
  const elapsed = Math.max(0, Math.floor((new Date(end ?? Date.now()).getTime() - new Date(start).getTime()) / 1000));
  const hours = Math.floor(elapsed / 3600);
  const minutes = Math.floor((elapsed % 3600) / 60);
  const seconds = elapsed % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function analysisStatusPresentation(status: Analysis["status"]) {
  if (status === "RUNNING") return { label: "분석 진행 중", className: "secscan-status-active" };
  if (status === "PENDING") return { label: "분석 대기", className: "secscan-status-neutral" };
  if (status === "COMPLETED") return { label: "분석 완료", className: "secscan-status-success" };
  return { label: "분석 실패", className: "secscan-status-failed" };
}

export default function AnalysisStatusPage() {
  const { analysisId, projectId } = useParams<{ analysisId: string; projectId: string }>();
  const { user, clearUser } = useAuth();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [transportError, setTransportError] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [rerunning, setRerunning] = useState(false);
  const [projectName, setProjectName] = useState<string | null>(null);
  const [showCompletion, setShowCompletion] = useState(false);
  const previousStatusRef = useRef<Analysis["status"] | null>(null);
  const analysisDisplayStartedAtRef = useRef<number | null>(null);
  const analysisProjectId = analysis?.project_id;

  const loadAnalysis = useCallback(async () => {
    if (!analysisId) return;
    try {
      const next = await getAnalysis(analysisId);
      if ((next.status === "PENDING" || next.status === "RUNNING") && analysisDisplayStartedAtRef.current === null) {
        analysisDisplayStartedAtRef.current = Date.now();
      }
      if (next.status === "COMPLETED" && analysisDisplayStartedAtRef.current !== null) {
        const remaining = MIN_ANALYSIS_DISPLAY_MS - (Date.now() - analysisDisplayStartedAtRef.current);
        if (remaining > 0) {
          window.setTimeout(() => void loadAnalysis(), remaining);
          return;
        }
      }
      if (previousStatusRef.current && previousStatusRef.current !== "COMPLETED" && next.status === "COMPLETED") {
        setShowCompletion(true);
      }
      previousStatusRef.current = next.status;
      setAnalysis(next);
      if (projectId && String(next.project_id) !== projectId) {
        navigate(`/projects/${next.project_id}/analyses/${next.id}`, { replace: true });
      }
      setTransportError(false);
      setPageError(null);
    } catch (error) {
      const status = (error as AxiosError).response?.status;
      if (status === 401) {
        clearUser();
        navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } });
      } else if (status === 403) setPageError("이 기능은 관리자만 사용할 수 있습니다.");
      else if (status === 404) setPageError("요청한 정보를 찾을 수 없습니다.");
      else setTransportError(true);
    } finally {
      setLoading(false);
    }
  }, [analysisId, clearUser, navigate, projectId]);

  useEffect(() => {
    void loadAnalysis();
  }, [loadAnalysis]);

  useEffect(() => {
    if (analysis?.status !== "PENDING" && analysis?.status !== "RUNNING") return;
    const intervalId = window.setInterval(() => void loadAnalysis(), POLL_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [analysis?.status, loadAnalysis]);

  useEffect(() => {
    if (!analysisProjectId) return;
    let active = true;

    api.get<{ name: string }>(`/projects/${analysisProjectId}`)
      .then((response) => {
        if (active) setProjectName(response.data.name);
      })
      .catch(() => {
        if (active) setProjectName(null);
      });

    return () => {
      active = false;
    };
  }, [analysisProjectId]);

  async function rerun() {
    if (!analysis) return;
    setRerunning(true);
    try {
      const next = await createAnalysis(analysis.project_id);
      navigate(`/projects/${next.project_id}/analyses/${next.id}`);
    } catch (error) {
      const status = (error as AxiosError).response?.status;
      if (status === 401) {
        clearUser();
        navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } });
      } else {
        setTransportError(true);
      }
    } finally {
      setRerunning(false);
    }
  }

  if (loading) return <section className="secscan-loading-state" aria-busy="true">분석 상태를 불러오는 중...</section>;
  if (pageError) return <section role="alert" className="secscan-error-state">{pageError}</section>;
  if (!analysis) {
    if (transportError) {
      return (
        <div role="alert" className="secscan-error-state">
          <p>상태를 갱신하지 못했습니다. 분석은 계속 진행 중일 수 있습니다.</p>
          <button type="button" onClick={() => void loadAnalysis()} className="secscan-secondary-button mt-4">새로고침</button>
        </div>
      );
    }
    return <section role="alert" className="secscan-error-state">분석 상태를 불러오지 못했습니다.</section>;
  }

  const presentation = analysisStatusPresentation(analysis.status);
  const breadcrumbProjectName = projectName ?? `프로젝트 #${analysis.project_id}`;
  const breadcrumbEnd = analysis.status === "COMPLETED" ? "분석 결과" : "분석 상태";

  return (
    <section className="min-w-0">
      <nav aria-label="경로" className="flex min-w-0 items-center gap-2 text-sm text-secscan-muted">
        <Link to="/projects" className="shrink-0 underline decoration-secscan-border underline-offset-4 hover:text-secscan-foreground">프로젝트</Link>
        <span aria-hidden="true">&gt;</span>
        <Link to={`/projects/${analysis.project_id}`} className="min-w-0 truncate underline decoration-secscan-border underline-offset-4 hover:text-secscan-foreground" title={breadcrumbProjectName}>{breadcrumbProjectName}</Link>
        <span aria-hidden="true">&gt;</span>
        <span className="shrink-0 text-secscan-foreground">{breadcrumbEnd}</span>
      </nav>
      {analysis.status !== "COMPLETED" && (
        <div className="secscan-panel mt-5 flex min-w-0 flex-col gap-5 p-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="min-w-0">
            <h1 className="text-3xl font-bold tracking-tight">분석 상태</h1>
            <p className="mt-2 text-sm text-secscan-muted">상태: {analysis.status}</p>
          </div>
          <span className={`secscan-status-badge shrink-0 ${presentation.className}`}>{presentation.label}</span>
        </div>
      )}
      {transportError && (
        <div role="alert" className="secscan-error-state mt-5 text-sm">
          <p>상태를 갱신하지 못했습니다. 분석은 계속 진행 중일 수 있습니다.</p>
          <button type="button" onClick={() => void loadAnalysis()} className="secscan-secondary-button mt-4">새로고침</button>
        </div>
      )}
      {(analysis.status === "PENDING" || analysis.status === "RUNNING") && (
        <div className="fixed inset-x-0 top-[72px] bottom-0 z-40 flex items-center justify-center bg-black/70 px-5" role="dialog" aria-modal="true" aria-labelledby="analysis-progress-title">
          <div className="w-full max-w-xl min-h-[330px] rounded-xl border border-secscan-border bg-secscan-surface p-8 shadow-2xl shadow-black/60">
            <div className="flex justify-center">
              <span className={`secscan-status-badge ${presentation.className}`}>{presentation.label}</span>
            </div>
            <h2 id="analysis-progress-title" className="mt-5 text-center text-xl font-bold">분석이 진행 중입니다.</h2>
            <div aria-label="분석 진행 중" aria-busy="true" className="secscan-preflight-progress mt-6">
              <span />
            </div>
          </div>
        </div>
      )}
      {analysis.status === "COMPLETED" && <div className="mt-5"><FindingsPage analysisId={analysis.id.toString()} /></div>}
      {analysis.status === "COMPLETED" && showCompletion && (
        <div className="fixed inset-x-0 top-[72px] bottom-0 z-40 flex items-center justify-center bg-black/70 px-5" role="dialog" aria-modal="true" aria-labelledby="analysis-complete-title">
          <div className="w-full max-w-xl min-h-[330px] rounded-xl border border-secscan-border bg-secscan-surface p-8 shadow-2xl shadow-black/60">
            <div className="flex justify-center"><span className={`secscan-status-badge ${presentation.className}`}>{presentation.label}</span></div>
            <h2 id="analysis-complete-title" className="mt-5 text-center text-xl font-bold">분석이 완료되었습니다.</h2>
            <div className="mt-7 pt-6">
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div><dt className="text-xs text-secscan-muted">시작 시각</dt><dd className="mt-2 font-medium">{formatAnalysisTime(analysis.started_at)}</dd></div>
                <div><dt className="text-xs text-secscan-muted">분석 소요 시간</dt><dd className="mt-2 font-medium">{formatDuration(analysis.started_at, analysis.completed_at)}</dd></div>
              </dl>
            </div>
            <button type="button" onClick={() => setShowCompletion(false)} className="secscan-primary-button mt-7 w-full">결과 보기</button>
          </div>
        </div>
      )}
      {analysis.status === "FAILED" && (
        <div role="alert" className="secscan-error-state mt-5 min-w-0 p-5">
          <p>{user?.role === "ADMIN" ? analysis.error_message || USER_FAILURE_MESSAGE : USER_FAILURE_MESSAGE}</p>
          {user?.role === "ADMIN" && analysis.error_code && <p className="mt-3 break-all text-sm text-secscan-muted">오류 코드: {analysis.error_code}</p>}
          {user?.role === "ADMIN" && analysis.execution_log && <pre className="mt-3 max-w-full overflow-x-auto whitespace-pre-wrap break-words rounded-lg border border-secscan-border bg-secscan-canvas p-3 text-xs text-secscan-foreground">{analysis.execution_log}</pre>}
          {user?.role === "ADMIN" && <button type="button" disabled={rerunning} onClick={() => void rerun()} className="secscan-secondary-button mt-5 disabled:cursor-not-allowed disabled:opacity-50">{rerunning ? "재실행 요청 중..." : "현재 소스로 다시 분석"}</button>}
        </div>
      )}
    </section>
  );
}
