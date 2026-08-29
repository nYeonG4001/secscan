import { api } from "./auth";

export type MappingStatus = "KISA_MAPPED" | "UNMAPPED";

export interface FindingListItem {
  id: number;
  severity: string | null;
  rule_name: string | null;
  kisa_code: string | null;
  file_path: string;
  line: number | null;
  end_line: number | null;
  language: string | null;
  confidence: string | null;
  mapping_status: MappingStatus;
}

export interface FindingDetail extends FindingListItem {
  analysis_id: number;
  engine_rule_id: string;
  criterion_id: string | null;
  message: string | null;
  evidence: string | null;
  code_snippet: string | null;
  recommendation: string | null;
  raw_result?: Record<string, unknown> | null;
}

export interface FindingListResponse {
  items: FindingListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface FindingFilters {
  severity?: string;
  mapping_status?: MappingStatus;
  language?: string;
  limit?: number;
  offset?: number;
}

export async function getFindings(analysisId: string, filters: FindingFilters): Promise<FindingListResponse> {
  const response = await api.get<FindingListResponse>("/findings/", { params: { analysis_id: analysisId, ...filters } });
  return response.data;
}

export async function getFinding(findingId: number): Promise<FindingDetail> {
  const response = await api.get<FindingDetail>(`/findings/${findingId}`);
  return response.data;
}
