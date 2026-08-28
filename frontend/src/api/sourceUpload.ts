import type { AxiosProgressEvent } from "axios";

import { api } from "./auth";

export interface SourceUploadResponse {
  project_id: number;
  source_status: "REGISTERED";
  target_languages: string[];
}

export interface SourceUploadOptions {
  signal: AbortSignal;
  onUploadProgress: (event: AxiosProgressEvent) => void;
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
