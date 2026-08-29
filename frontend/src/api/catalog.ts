import { api } from "./auth";

export type ImplementationStatus = "지원" | "부분 지원" | "미지원";

export interface CatalogItem {
  kisa_code: string;
  criterion_id: string | null;
  item_number: number | null;
  category: string;
  name: string;
  description: string | null;
  reference_info: string | null;
  default_severity: string;
  active: boolean;
  implementation_status: ImplementationStatus;
  recommendation: string | null;
}

export type CatalogCreate = Omit<CatalogItem, "criterion_id" | "item_number" | "description" | "reference_info" | "recommendation"> & {
  criterion_id?: string;
  item_number?: number;
  description?: string;
  reference_info?: string;
};

export type CatalogUpdate = Pick<CatalogItem, "description" | "reference_info" | "active" | "default_severity" | "implementation_status" | "recommendation">;

export async function getCatalog(): Promise<CatalogItem[]> {
  return (await api.get<CatalogItem[]>("/catalog/")).data;
}

export async function createCatalog(item: CatalogCreate): Promise<CatalogItem> {
  return (await api.post<CatalogItem>("/catalog/", item)).data;
}

export async function updateCatalog(kisaCode: string, item: CatalogUpdate): Promise<CatalogItem> {
  return (await api.patch<CatalogItem>(`/catalog/${kisaCode}`, item)).data;
}
