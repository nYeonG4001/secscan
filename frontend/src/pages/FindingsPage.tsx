import { AxiosError } from "axios";
import { useCallback, useEffect, useState } from "react";

import { FindingDetail, FindingFilters, FindingListItem, getFinding, getFindings } from "../api/findings";
import { useAuth } from "../auth/useAuth";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";
import { useNavigate } from "react-router-dom";

const LIMIT = 50;

function location(item: FindingListItem) {
  if (item.line == null) return item.file_path;
  return `${item.file_path}:${item.line}${item.end_line && item.end_line !== item.line ? `-${item.end_line}` : ""}`;
}

export default function FindingsPage({ analysisId }: { analysisId: string }) {
  const { user, clearUser } = useAuth();
  const navigate = useNavigate();
  const [filters, setFilters] = useState<FindingFilters>({ limit: LIMIT, offset: 0 });
  const [items, setItems] = useState<FindingListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<FindingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    try { const result = await getFindings(analysisId, filters); setItems(result.items); setTotal(result.total); setError(null); }
    catch (requestError) { const status = (requestError as AxiosError).response?.status; if (status === 401) { clearUser(); navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } }); } else setError(status === 403 ? "이 기능은 관리자만 사용할 수 있습니다." : status === 404 ? "요청한 정보를 찾을 수 없습니다." : "결과를 불러오지 못했습니다. 다시 시도해 주세요."); }
    finally { setLoading(false); }
  }, [analysisId, clearUser, filters, navigate]);
  useEffect(() => { void load(); }, [load]);
  async function select(item: FindingListItem) { try { setSelected(await getFinding(item.id)); } catch { setError("결과 상세를 불러오지 못했습니다. 다시 시도해 주세요."); } }
  function changeFilter(name: "severity" | "mapping_status" | "language", value: string) { setSelected(null); setFilters((current) => ({ ...current, [name]: value || undefined, offset: 0 })); }
  function resetFilters() { setSelected(null); setFilters({ limit: LIMIT, offset: 0 }); }
  const hasFilters = Boolean(filters.severity || filters.mapping_status || filters.language);
  if (loading) return <p>탐지 결과를 불러오는 중...</p>;
  return <section className="min-h-[560px]">
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><h1 className="text-2xl font-bold">탐지 결과</h1><p className="mt-1 text-sm text-gray-500">총 {total}건</p></div><div className="flex flex-wrap gap-2" aria-label="결과 필터">
      <select aria-label="심각도 필터" value={filters.severity ?? ""} onChange={(e) => changeFilter("severity", e.target.value)}><option value="">모든 심각도</option>{["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => <option key={value}>{value}</option>)}</select>
      <select aria-label="KISA 매핑 필터" value={filters.mapping_status ?? ""} onChange={(e) => changeFilter("mapping_status", e.target.value)}><option value="">모든 매핑</option><option value="KISA_MAPPED">KISA 매핑됨</option><option value="UNMAPPED">미매핑</option></select>
      <select aria-label="언어 필터" value={filters.language ?? ""} onChange={(e) => changeFilter("language", e.target.value)}><option value="">모든 언어</option>{["JAVA", "JAVASCRIPT", "PYTHON"].map((value) => <option key={value}>{value}</option>)}</select>
    </div></div>
    {error && <div role="alert" className="mb-3"><p>{error}</p><button type="button" onClick={() => void load()}>다시 시도</button></div>}
    {total === 0 ? (hasFilters ? <div><p>현재 필터에 맞는 결과가 없습니다.</p><button type="button" onClick={resetFilters}>필터 초기화</button></div> : <p>이 분석에서 탐지된 결과가 없습니다.</p>) : <div className="flex h-[560px] overflow-hidden rounded border border-gray-800 bg-[#121214]">
      <div className={`${selected ? "w-1/2 border-r" : "w-full"} min-w-0 overflow-y-auto`} data-testid="finding-list">{items.map((item) => <button key={item.id} type="button" onClick={() => void select(item)} className="block w-full border-b border-gray-800 p-4 text-left hover:bg-gray-900" aria-pressed={selected?.id === item.id}><div className="flex justify-between gap-3"><strong>{item.severity ?? "UNKNOWN"}</strong><span className="text-xs">{item.mapping_status === "KISA_MAPPED" ? item.kisa_code : "미매핑"}</span></div><p className="mt-1 font-medium">{item.rule_name ?? "이름 없는 진단"}</p><p className="mt-1 text-sm text-gray-400">{location(item)} · {item.language ?? "언어 미상"} · {item.confidence ?? "신뢰도 미상"}</p></button>)}</div>
      {selected && <aside className="w-1/2 min-w-0 overflow-y-auto p-5" aria-label="탐지 결과 상세" data-testid="finding-detail"><div className="flex justify-between gap-3"><div><p className="text-sm">{selected.severity ?? "UNKNOWN"}</p><h2 className="text-xl font-bold">{selected.rule_name ?? "이름 없는 진단"}</h2></div><button type="button" onClick={() => setSelected(null)} aria-label="결과 상세 닫기">닫기</button></div><dl className="mt-5 grid gap-2 text-sm"><div><dt>매핑 상태</dt><dd>{selected.mapping_status}</dd></div><div><dt>위치</dt><dd>{location(selected)}</dd></div><div><dt>언어 / 신뢰도</dt><dd>{selected.language ?? "-"} / {selected.confidence ?? "-"}</dd></div></dl>{([["메시지", selected.message], ["탐지 근거", selected.evidence], ["코드 조각", selected.code_snippet], ["조치 권고", selected.recommendation]] as const).map(([label, value]) => value && <div key={label} className="mt-5"><h3 className="font-semibold">{label}</h3><pre className="mt-2 whitespace-pre-wrap break-words rounded bg-black/30 p-3 text-sm">{value}</pre></div>)}{user?.role === "ADMIN" && selected.raw_result != null && <div className="mt-5"><h3 className="font-semibold">원본 분석 결과</h3><pre className="mt-2 overflow-auto rounded bg-black/30 p-3 text-xs">{JSON.stringify(selected.raw_result, null, 2)}</pre></div>}</aside>}
    </div>}
    {total > LIMIT && <div className="mt-4 flex gap-2"><button type="button" disabled={!filters.offset} onClick={() => setFilters((v) => ({ ...v, offset: Math.max(0, (v.offset ?? 0) - LIMIT) }))}>이전</button><button type="button" disabled={(filters.offset ?? 0) + LIMIT >= total} onClick={() => setFilters((v) => ({ ...v, offset: (v.offset ?? 0) + LIMIT }))}>다음</button></div>}
  </section>;
}
