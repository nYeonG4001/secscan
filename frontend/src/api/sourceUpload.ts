import type { AxiosProgressEvent } from "axios";

import { api } from "./auth";

export interface SourceUploadResponse {
  project_id: number;
  source_status: "REGISTERED";
  target_languages: string[];
}

export interface SourcePreflightResponse {
  safe: true;
}

export interface SourceUploadOptions {
  signal: AbortSignal;
  onUploadProgress: (event: AxiosProgressEvent) => void;
}

export interface SourcePreflightOptions {
  signal: AbortSignal;
}

export async function preflightProjectSource(
  projectId: string,
  file: File,
  options: SourcePreflightOptions,
): Promise<SourcePreflightResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<SourcePreflightResponse>(
    `/projects/${projectId}/source/preflight`,
    formData,
    options,
  );
  return response.data;
}

export async function uploadProjectSource(
  projectId: string,
  file: File,
  options: SourceUploadOptions,
): Promise<SourceUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.put<SourceUploadResponse>(`/projects/${projectId}/source`, formData, options);
  return response.data;
}
