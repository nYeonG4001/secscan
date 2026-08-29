import { api } from "./auth";

export interface ProjectPayload { name: string; description?: string | null; }

export async function createProject(body: ProjectPayload) {
  return (await api.post("/projects/", body)).data;
}

export async function updateProject(id: number, body: ProjectPayload) {
  return (await api.patch(`/projects/${id}`, body)).data;
}
