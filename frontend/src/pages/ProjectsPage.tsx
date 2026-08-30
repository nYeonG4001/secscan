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
}

function errorStatus(error: unknown) {
  return (error as AxiosError).response?.status;
}

function sourceStatusLabel(status: Project["source_status"]) {
  return status === "REGISTERED" ? "등록됨" : "등록 필요";
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
          <p className="mt-2 max-w-2xl text-sm text-secscan-muted">등록된 프로젝트를 선택해 소스 등록, 분석 실행, 결과 조회를 진행합니다.</p>
        </div>
        {user?.role === "ADMIN" && <button type="button" onClick={() => setShowCreate(true)} className="secscan-primary-button shrink-0">새 프로젝트</button>}
      </div>
      {projects.length === 0 ? (
        <div className="secscan-empty-state">
          <p className="font-medium text-secscan-foreground">표시할 프로젝트가 없습니다.</p>
          {user?.role === "ADMIN" && <p className="mt-2 text-sm">새 프로젝트를 등록해 소스 분석을 시작할 수 있습니다.</p>}
        </div>
      ) : (
        <ul className="secscan-panel overflow-hidden divide-y divide-secscan-border">
          {projects.map((project) => (
            <li key={project.id} className="min-w-0">
              <Link to={`/projects/${project.id}`} className="secscan-panel-interactive block min-w-0 px-5 py-4 focus-visible:relative">
                <div className="flex min-w-0 flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0 lg:max-w-xl">
                    <p className="break-words font-semibold text-secscan-foreground">{project.name}</p>
                    {project.description && <p className="mt-1 break-words text-sm text-secscan-muted">{project.description}</p>}
                  </div>
                  <div className="flex min-w-0 flex-wrap items-center gap-2 text-xs">
                    {project.target_languages?.map((language) => (
                      <span key={language} className="secscan-status-badge secscan-status-neutral">{language}</span>
                    ))}
                    <span className={`secscan-status-badge ${project.source_status === "REGISTERED" ? "secscan-status-success" : "secscan-status-neutral"}`}>
                      {sourceStatusLabel(project.source_status)}
                    </span>
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
      {showCreate && user?.role === "ADMIN" && <ActionDrawer title="새 프로젝트" onClose={() => setShowCreate(false)} footer={<button type="submit" form="create-project" className="secscan-primary-button w-full">등록</button>}><form id="create-project" onSubmit={submitCreate} className="space-y-4"><label className="block text-sm font-medium">프로젝트 이름<input required value={name} onChange={(event) => setName(event.target.value)} className="mt-2" /></label><label className="block text-sm font-medium">설명<textarea value={description} onChange={(event) => setDescription(event.target.value)} className="mt-2" /></label></form></ActionDrawer>}
    </section>
  );
}
