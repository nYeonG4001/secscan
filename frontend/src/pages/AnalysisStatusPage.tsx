import { AxiosError } from "axios";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Analysis, createAnalysis, getAnalysis } from "../api/analyses";
import { useAuth } from "../auth/useAuth";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";

const POLL_INTERVAL_MS = 3_000;
const USER_FAILURE_MESSAGE = "분석을 완료하지 못했습니다. 관리자에게 문의하세요.";

export default function AnalysisStatusPage() {
  const { analysisId, projectId } = useParams<{ analysisId: string; projectId: string }>();
  const { user, clearUser } = useAuth();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [transportError, setTransportError] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [rerunning, setRerunning] = useState(false);

  const loadAnalysis = useCallback(async () => {
    if (!analysisId) return;
    try {
      const next = await getAnalysis(analysisId);
      setAnalysis(next);
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
  }, [analysisId, clearUser, navigate]);

  useEffect(() => {
    void loadAnalysis();
  }, [loadAnalysis]);

  useEffect(() => {
    if (analysis?.status !== "PENDING" && analysis?.status !== "RUNNING") return;
    const intervalId = window.setInterval(() => void loadAnalysis(), POLL_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [analysis?.status, loadAnalysis]);

  async function rerun() {
    if (!projectId) return;
    setRerunning(true);
    try {
      const next = await createAnalysis(projectId);
      navigate(`/projects/${projectId}/analyses/${next.id}`);
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

  if (loading) return <p>분석 상태를 불러오는 중...</p>;
  if (pageError) return <p role="alert">{pageError}</p>;
  if (!analysis) {
    if (transportError) {
      return (
        <div role="alert">
          <p>상태를 갱신하지 못했습니다. 분석은 계속 진행 중일 수 있습니다.</p>
          <button type="button" onClick={() => void loadAnalysis()} className="mt-2 rounded border px-3 py-2">새로고침</button>
        </div>
      );
    }
    return <p role="alert">분석 상태를 불러오지 못했습니다.</p>;
  }

  return (
    <section>
      <Link to={`/projects/${projectId}`} className="text-sm">프로젝트로 돌아가기</Link>
      <h1 className="mt-4 text-2xl font-bold">분석 상태</h1>
      <p className="mt-2 text-sm">상태: {analysis.status}</p>
      {transportError && (
        <div role="alert" className="mt-4 text-sm text-red-600">
          <p>상태를 갱신하지 못했습니다. 분석은 계속 진행 중일 수 있습니다.</p>
          <button type="button" onClick={() => void loadAnalysis()} className="mt-2 rounded border px-3 py-2">새로고침</button>
        </div>
      )}
      {(analysis.status === "PENDING" || analysis.status === "RUNNING") && <p className="mt-4">분석이 진행 중입니다. 상태를 자동으로 갱신합니다.</p>}
      {analysis.status === "COMPLETED" && <p className="mt-4">분석이 완료되었습니다. 탐지 결과 목록은 다음 단계에서 제공합니다.</p>}
      {analysis.status === "FAILED" && (
        <div role="alert" className="mt-4">
          <p>{user?.role === "ADMIN" ? analysis.error_message || USER_FAILURE_MESSAGE : USER_FAILURE_MESSAGE}</p>
          {user?.role === "ADMIN" && analysis.error_code && <p className="mt-2 text-sm">오류 코드: {analysis.error_code}</p>}
          {user?.role === "ADMIN" && analysis.execution_log && <pre className="mt-2 overflow-auto rounded border p-3 text-xs">{analysis.execution_log}</pre>}
          {user?.role === "ADMIN" && <button type="button" disabled={rerunning} onClick={() => void rerun()} className="mt-4 rounded border px-3 py-2">{rerunning ? "재실행 요청 중..." : "현재 소스로 다시 분석"}</button>}
        </div>
      )}
    </section>
  );
}
