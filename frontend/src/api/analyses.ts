import { api } from "./auth";

export type AnalysisStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface Analysis {
  id: number;
  project_id: number;
  executed_by: number;
  status: AnalysisStatus;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  summary?: { total_findings?: number } | null;
  error_code?: string | null;
  error_message?: string | null;
  execution_log?: string | null;
}

export async function createAnalysis(projectId: string | number): Promise<Analysis> {
  const response = await api.post<Analysis>("/analyses/", { project_id: Number(projectId) });
  return response.data;
}

export async function getAnalysis(analysisId: string): Promise<Analysis> {
  const response = await api.get<Analysis>(`/analyses/${analysisId}`);
  return response.data;
}
