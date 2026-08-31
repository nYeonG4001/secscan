import { AxiosError } from "axios";
import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api } from "../api/auth";
import { useAuth } from "../auth/useAuth";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";
import { ActionDrawer } from "../components/ActionDrawer";
import { createProject } from "../api/projects";

export interface Project {
  id: number;
  name: string;
  description: string | null;
  source_status?: "NEEDS_UPLOAD" | "REGISTERED";
  target_languages?: string[] | null;
  latest_analysis_status?: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | null;
  updated_at?: string;
}

function errorStatus(error: unknown) {
  return (error as AxiosError).response?.status;
}

function sourceStatusLabel(status: Project["source_status"]) {
  return status === "REGISTERED" ? "등록됨" : "등록 필요";
}

function analysisStatusLabel(status: Project["latest_analysis_status"]) {
  if (status === "PENDING") return "분석 대기";
  if (status === "RUNNING") return "분석 진행 중";
  if (status === "COMPLETED") return "분석 완료";
  if (status === "FAILED") return "분석 실패";
  return "분석 전";
}

function analysisStatusClass(status: Project["latest_analysis_status"]) {
  if (status === "RUNNING") return "secscan-status-active";
  if (status === "COMPLETED") return "secscan-status-success";
  if (status === "FAILED") return "secscan-status-failed";
  return "secscan-status-neutral";
}

function formatUpdatedAt(value: Project["updated_at"]) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

export default function ProjectsPage() {
  const { clearUser, user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function submitCreate(event: FormEvent) {
    event.preventDefault();
    try {
      const created = await createProject({ name, description: description || null });
      setShowCreate(false);
      navigate(`/projects/${created.id}`);
    } catch (requestError) {
      if (errorStatus(requestError) === 401) { clearUser(); navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } }); }
      else if (errorStatus(requestError) === 403) setError("이 기능은 관리자만 사용할 수 있습니다.");
      else setError("프로젝트를 등록하지 못했습니다. 다시 시도해 주세요.");
    }
  }

  useEffect(() => {
    let active = true;

    api.get<Project[]>("/projects/")
      .then((response) => {
        if (active) setProjects(response.data);
      })
      .catch((requestError) => {
        if (!active) return;
        if (errorStatus(requestError) === 401) {
          clearUser();
          navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } });
          return;
        }
        setError("프로젝트를 불러오지 못했습니다. 다시 시도해 주세요.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [clearUser, navigate]);

  if (loading) return <section className="secscan-loading-state" aria-busy="true">프로젝트를 불러오는 중...</section>;
  if (error) return <section role="alert" className="secscan-error-state">{error}</section>;

  return (
    <section className="min-w-0">
      <nav aria-label="경로" className="text-sm text-secscan-muted">
        <span className="text-secscan-foreground">프로젝트</span>
      </nav>
      <div className="mb-7 mt-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h1 className="text-3xl font-bold tracking-tight">프로젝트</h1>
        </div>
        {user?.role === "ADMIN" && <button type="button" onClick={() => setShowCreate(true)} className="secscan-primary-button shrink-0"><span aria-hidden="true" className="mr-1.5 text-base leading-none">＋</span>새 프로젝트</button>}
      </div>
      {projects.length === 0 ? (
        <div className="secscan-empty-state">
          <p className="font-medium text-secscan-foreground">표시할 프로젝트가 없습니다.</p>
          {user?.role === "ADMIN" && <p className="mt-2 text-sm">새 프로젝트를 등록해 소스 분석을 시작할 수 있습니다.</p>}
        </div>
      ) : (
        <div className="secscan-panel overflow-x-auto">
          <table className="min-w-[860px] w-full border-collapse text-left text-sm" aria-label="프로젝트 목록">
            <thead className="border-b border-secscan-border bg-secscan-surface-2 text-xs font-semibold text-secscan-muted">
              <tr>
                <th scope="col" className="px-5 py-3">프로젝트명</th>
                <th scope="col" className="px-5 py-3">분석 언어</th>
                <th scope="col" className="px-5 py-3">소스 상태</th>
                <th scope="col" className="px-5 py-3">최근 분석 상태</th>
                <th scope="col" className="px-5 py-3">수정 시각</th>
                <th scope="col" aria-label="프로젝트 열기" className="w-12 px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-secscan-border">
              {projects.map((project) => (
                <tr
                  key={project.id}
                  tabIndex={0}
                  onClick={() => navigate(`/projects/${project.id}`)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      navigate(`/projects/${project.id}`);
                    }
                  }}
                  className="cursor-pointer transition-colors hover:bg-secscan-surface-2 focus-visible:bg-secscan-surface-2"
                >
                  <td className="max-w-sm px-5 py-4 font-semibold text-secscan-foreground">
                    <Link to={`/projects/${project.id}`} className="block break-words hover:text-secscan-violet">
                      {project.name}
                    </Link>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex flex-nowrap gap-1.5 whitespace-nowrap">
                      {project.target_languages?.length
                        ? project.target_languages.map((language) => <span key={language} className="secscan-status-badge secscan-status-neutral">{language}</span>)
                        : <span className="text-secscan-muted">—</span>}
                    </div>
                  </td>
                  <td className="px-5 py-4"><span className={`secscan-status-badge ${project.source_status === "REGISTERED" ? "secscan-status-success" : "secscan-status-neutral"}`}>{sourceStatusLabel(project.source_status)}</span></td>
                  <td className="px-5 py-4"><span className={`secscan-status-badge ${analysisStatusClass(project.latest_analysis_status)}`}>{analysisStatusLabel(project.latest_analysis_status)}</span></td>
                  <td className="whitespace-nowrap px-5 py-4 text-secscan-muted">{formatUpdatedAt(project.updated_at)}</td>
                  <td className="px-4 py-4 text-right"><Link to={`/projects/${project.id}`} aria-label={`${project.name} 열기`} className="inline-flex p-1 text-xl text-secscan-muted hover:text-secscan-foreground">›</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {showCreate && user?.role === "ADMIN" && <ActionDrawer title="새 프로젝트" onClose={() => setShowCreate(false)} footer={<button type="submit" form="create-project" className="secscan-primary-button w-full">등록</button>}><form id="create-project" onSubmit={submitCreate} className="space-y-4"><label className="block text-sm font-medium">프로젝트 이름<input required value={name} onChange={(event) => setName(event.target.value)} className="mt-2" /></label><label className="block text-sm font-medium">설명<textarea value={description} onChange={(event) => setDescription(event.target.value)} className="mt-2" /></label></form></ActionDrawer>}
    </section>
  );
}
