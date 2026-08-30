import { AxiosError } from "axios";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { FindingDetail, FindingFilters, FindingListItem, getFinding, getFindings } from "../api/findings";
import { useAuth } from "../auth/useAuth";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";

const LIMIT = 50;

function location(item: FindingListItem) {
  if (item.line == null) return item.file_path;
  return `${item.file_path}:${item.line}${item.end_line && item.end_line !== item.line ? `-${item.end_line}` : ""}`;
}

function severityClass(severity: string | null) {
  if (severity === "CRITICAL" || severity === "HIGH") return "secscan-status-failed";
  if (severity === "MEDIUM") return "secscan-status-active";
  return "secscan-status-neutral";
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
  const [filterOpen, setFilterOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await getFindings(analysisId, filters);
      setItems(result.items);
      setTotal(result.total);
      setError(null);
    } catch (requestError) {
      const status = (requestError as AxiosError).response?.status;
      if (status === 401) {
        clearUser();
        navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } });
      } else {
        setError(status === 403 ? "이 기능은 관리자만 사용할 수 있습니다." : status === 404 ? "요청한 정보를 찾을 수 없습니다." : "결과를 불러오지 못했습니다. 다시 시도해 주세요.");
      }
    } finally {
      setLoading(false);
    }
  }, [analysisId, clearUser, filters, navigate]);

  useEffect(() => {
    void load();
  }, [load]);

  async function select(item: FindingListItem) {
    try {
      setSelected(await getFinding(item.id));
    } catch (requestError) {
      const status = (requestError as AxiosError).response?.status;
      if (status === 401) {
        clearUser();
        navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } });
      } else if (status === 403) {
        setError("이 기능은 관리자만 사용할 수 있습니다.");
      } else if (status === 404) {
        setError("요청한 정보를 찾을 수 없습니다.");
      } else {
        setError("결과 상세를 불러오지 못했습니다. 다시 시도해 주세요.");
      }
    }
  }

  function changeFilter(name: "severity" | "mapping_status" | "language", value: string) {
    setSelected(null);
    setFilters((current) => ({ ...current, [name]: value || undefined, offset: 0 }));
  }

  function resetFilters() {
    setSelected(null);
    setFilters({ limit: LIMIT, offset: 0 });
  }

  const activeFilterCount = [filters.severity, filters.mapping_status, filters.language].filter(Boolean).length;
  const hasFilters = activeFilterCount > 0;

  if (loading) return <section className="secscan-loading-state" aria-busy="true">탐지 결과를 불러오는 중...</section>;

  return (
    <section className="min-h-[560px] min-w-0">
      <div className="mb-5 flex min-w-0 flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-3xl font-bold tracking-tight">탐지 결과</h1>
          <p className="mt-2 text-sm text-secscan-muted">총 {total}건</p>
        </div>
        <div className="relative">
          <button type="button" aria-expanded={filterOpen} aria-controls="finding-filter-panel" onClick={() => setFilterOpen((open) => !open)} className="secscan-secondary-button">
            필터{activeFilterCount > 0 ? ` ${activeFilterCount}` : ""}
          </button>
          {filterOpen && (
            <div id="finding-filter-panel" className="secscan-panel absolute right-0 z-10 mt-2 w-[min(22rem,calc(100vw-3rem))] p-4 shadow-2xl shadow-black/40" aria-label="결과 필터">
              <div className="grid gap-3">
                <label className="block text-sm font-medium">심각도
                  <select aria-label="심각도 필터" className="mt-2" value={filters.severity ?? ""} onChange={(event) => changeFilter("severity", event.target.value)}>
                    <option value="">모든 심각도</option>
                    {["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => <option key={value}>{value}</option>)}
                  </select>
                </label>
                <label className="block text-sm font-medium">KISA 매핑
                  <select aria-label="KISA 매핑 필터" className="mt-2" value={filters.mapping_status ?? ""} onChange={(event) => changeFilter("mapping_status", event.target.value)}>
                    <option value="">모든 매핑</option>
                    <option value="KISA_MAPPED">KISA 매핑됨</option>
                    <option value="UNMAPPED">미매핑</option>
                  </select>
                </label>
                <label className="block text-sm font-medium">언어
                  <select aria-label="언어 필터" className="mt-2" value={filters.language ?? ""} onChange={(event) => changeFilter("language", event.target.value)}>
                    <option value="">모든 언어</option>
                    {["JAVA", "JAVASCRIPT", "PYTHON"].map((value) => <option key={value}>{value}</option>)}
                  </select>
                </label>
                {hasFilters && <button type="button" onClick={resetFilters} className="secscan-secondary-button justify-self-start px-3 py-1.5 text-xs">필터 초기화</button>}
              </div>
            </div>
          )}
        </div>
      </div>

      {error && <div role="alert" className="secscan-error-state mb-4 text-sm"><p>{error}</p><button type="button" onClick={() => void load()} className="secscan-secondary-button mt-4">다시 시도</button></div>}

      {total === 0 ? (
        <div className="secscan-empty-state">
          <p className="font-medium text-secscan-foreground">{hasFilters ? "현재 필터에 맞는 결과가 없습니다." : "이 분석에서 탐지된 결과가 없습니다."}</p>
          {hasFilters && <button type="button" onClick={resetFilters} className="secscan-secondary-button mt-4">필터 초기화</button>}
        </div>
      ) : (
        <div className={`secscan-panel grid min-w-0 overflow-hidden ${selected ? "lg:grid-cols-2" : "grid-cols-1"} lg:h-[600px]`}>
          <div className="min-w-0 overflow-y-auto" data-testid="finding-list">
            {items.map((item) => (
              <button key={item.id} type="button" onClick={() => void select(item)} aria-pressed={selected?.id === item.id} className={`block w-full min-w-0 border-b border-secscan-border px-5 py-5 text-left last:border-b-0 ${selected?.id === item.id ? "bg-violet-500/10" : "hover:bg-secscan-surface-2"}`}>
                <div className="flex min-w-0 flex-wrap items-center justify-between gap-3">
                  <span className={`secscan-status-badge ${severityClass(item.severity)}`}>{item.severity ?? "UNKNOWN"}</span>
                  <span className={`secscan-status-badge ${item.mapping_status === "KISA_MAPPED" ? "secscan-status-success" : "secscan-status-neutral"}`}>{item.mapping_status === "KISA_MAPPED" ? item.kisa_code : "미매핑"}</span>
                </div>
                <p className="mt-3 break-words font-semibold">{item.rule_name ?? "이름 없는 진단"}</p>
                <div className="mt-3 flex min-w-0 flex-wrap gap-x-2 gap-y-1 text-sm text-secscan-muted"><span className="break-all">{location(item)}</span><span aria-hidden="true">·</span><span>{item.language ?? "언어 미상"}</span><span aria-hidden="true">·</span><span>{item.confidence ?? "신뢰도 미상"}</span></div>
              </button>
            ))}
          </div>

          {selected && (
            <aside className="min-w-0 overflow-y-auto border-t border-secscan-border bg-secscan-surface p-5 lg:border-l lg:border-t-0 lg:p-6" aria-label="탐지 결과 상세" data-testid="finding-detail">
              <div className="flex min-w-0 items-start justify-between gap-4">
                <div className="min-w-0"><span className={`secscan-status-badge ${severityClass(selected.severity)}`}>{selected.severity ?? "UNKNOWN"}</span><h2 className="mt-3 break-words text-2xl font-bold tracking-tight">{selected.rule_name ?? "이름 없는 진단"}</h2></div>
                <button type="button" onClick={() => setSelected(null)} aria-label="결과 상세 닫기" className="secscan-secondary-button shrink-0 px-3 py-1.5 text-xs">닫기</button>
              </div>
              <dl className="mt-6 grid min-w-0 gap-4 text-sm">
                <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">매핑 상태</dt><dd className="mt-1 break-words">{selected.mapping_status}</dd></div>
                <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">위치</dt><dd className="mt-1 break-all">{location(selected)}</dd></div>
                <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">언어 / 신뢰도</dt><dd className="mt-1 break-words">{selected.language ?? "-"} / {selected.confidence ?? "-"}</dd></div>
              </dl>
              {([ ["메시지", selected.message], ["탐지 근거", selected.evidence], ["코드 조각", selected.code_snippet], ["조치 권고", selected.recommendation] ] as const).map(([label, value]) => value && <div key={label} className="mt-6 min-w-0"><h3 className="font-semibold">{label}</h3><pre className="mt-3 max-w-full overflow-x-auto whitespace-pre-wrap break-words rounded-lg border border-secscan-border bg-secscan-canvas p-4 text-sm text-secscan-foreground">{value}</pre></div>)}
              {user?.role === "ADMIN" && selected.raw_result != null && <div className="mt-6 min-w-0"><h3 className="font-semibold">원본 분석 결과</h3><pre className="mt-3 max-w-full overflow-x-auto whitespace-pre-wrap break-words rounded-lg border border-secscan-border bg-secscan-canvas p-4 text-xs text-secscan-foreground">{JSON.stringify(selected.raw_result, null, 2)}</pre></div>}
            </aside>
          )}
        </div>
      )}

      {total > LIMIT && <div className="mt-5 flex gap-2"><button type="button" disabled={!filters.offset} onClick={() => setFilters((value) => ({ ...value, offset: Math.max(0, (value.offset ?? 0) - LIMIT) }))} className="secscan-secondary-button disabled:opacity-50">이전</button><button type="button" disabled={(filters.offset ?? 0) + LIMIT >= total} onClick={() => setFilters((value) => ({ ...value, offset: (value.offset ?? 0) + LIMIT }))} className="secscan-secondary-button disabled:opacity-50">다음</button></div>}
    </section>
  );
}
