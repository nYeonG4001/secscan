import { AxiosError } from "axios";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api } from "../api/auth";
import { useAuth } from "../auth/useAuth";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";

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

export default function ProjectsPage() {
  const { clearUser } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) return <p>프로젝트를 불러오는 중...</p>;
  if (error) return <p role="alert">{error}</p>;

  return (
    <section>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">프로젝트</h1>
          <p className="mt-1 text-sm text-gray-500">접근 권한이 있는 프로젝트를 확인합니다.</p>
        </div>
      </div>
      {projects.length === 0 ? (
        <p className="text-sm text-gray-500">표시할 프로젝트가 없습니다.</p>
      ) : (
        <ul className="space-y-3">
          {projects.map((project) => (
            <li key={project.id} className="rounded border bg-white p-4">
              <Link to={`/projects/${project.id}`} className="font-semibold">{project.name}</Link>
              {project.description && <p className="mt-1 text-sm text-gray-600">{project.description}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
