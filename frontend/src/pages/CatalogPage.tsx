import { AxiosError } from "axios";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { CatalogItem, CatalogUpdate, createCatalog, getCatalog, updateCatalog } from "../api/catalog";
import { useAuth } from "../auth/useAuth";
import { ActionDrawer } from "../components/ActionDrawer";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";

const emptyCreate = {
  kisa_code: "",
  name: "",
  category: "",
  default_severity: "MEDIUM",
  description: "",
  criterion_id: "",
  item_number: "",
  reference_info: "",
};

interface CatalogDraft {
  description: string;
  reference_info: string;
  active: boolean;
  default_severity: string;
  implementation_status: CatalogItem["implementation_status"];
  recommendation: string;
}

function LockIcon() {
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="inline-block h-3.5 w-3.5 text-secscan-muted"><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>;
}

function toDraft(item: CatalogItem): CatalogDraft {
  return {
    description: item.description ?? "",
    reference_info: item.reference_info ?? "",
    active: item.active,
    default_severity: item.default_severity,
    implementation_status: item.implementation_status,
    recommendation: item.recommendation ?? "",
  };
}

function draftChanged(item: CatalogItem, draft: CatalogDraft | null) {
  if (!draft) return false;
  const initial = toDraft(item);
  return Object.entries(initial).some(([key, value]) => draft[key as keyof CatalogDraft] !== value);
}

function implementationStatusClass(status: CatalogItem["implementation_status"]) {
  if (status === "지원") return "secscan-status-success";
  if (status === "부분 지원") return "secscan-status-active";
  return "secscan-status-neutral";
}

function resetScrollPosition(element: HTMLElement | null) {
  if (!element) return;
  if (typeof element.scrollTo === "function") {
    element.scrollTo({ top: 0 });
    return;
  }
  element.scrollTop = 0;
}

function SearchIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
      <circle cx="10.75" cy="10.75" r="5.75" />
      <path d="m15.25 15.25 4 4" />
    </svg>
  );
}

export default function CatalogPage() {
  const { user, clearUser } = useAuth();
  const navigate = useNavigate();
  const admin = user?.role === "ADMIN";
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [draft, setDraft] = useState<CatalogDraft | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [implementationStatus, setImplementationStatus] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [create, setCreate] = useState(emptyCreate);
  const [error, setError] = useState<string | null>(null);

  const loadCatalog = useCallback(async () => {
    try {
      setItems(await getCatalog());
      setError(null);
    } catch (requestError) {
      const responseStatus = (requestError as AxiosError).response?.status;
      if (responseStatus === 401) {
        clearUser();
        navigate("/login", { replace: true, state: { message: SESSION_EXPIRED_MESSAGE } });
      } else if (responseStatus === 403) {
        setError("이 기능은 관리자만 사용할 수 있습니다.");
      } else if (responseStatus === 404) {
        setError("요청한 정보를 찾을 수 없습니다.");
      } else {
        setError("카탈로그를 불러오지 못했습니다. 다시 시도해 주세요.");
      }
    }
  }, [clearUser, navigate]);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  const categories = useMemo(
    () => Array.from(new Set(items.map((item) => item.category))).sort((first, second) => first.localeCompare(second, "ko")),
    [items],
  );
  const filtered = useMemo(() => items.filter((item) => (
    (!category || item.category === category)
    && (!implementationStatus || item.implementation_status === implementationStatus)
    && `${item.kisa_code} ${item.name} ${item.category}`.toLowerCase().includes(search.toLowerCase())
  )), [category, implementationStatus, items, search]);
  const hasChanges = selected ? draftChanged(selected, draft) : false;
  const detailRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    resetScrollPosition(detailRef.current);
  }, [selected?.kisa_code]);

  function selectItem(item: CatalogItem) {
    if (selected?.kisa_code === item.kisa_code) {
      closeDetail();
      return;
    }
    setSelected(item);
    setDraft(toDraft(item));
  }

  function closeDetail() {
    setSelected(null);
    setDraft(null);
  }

  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selected || !draft || !hasChanges) return;
    const body: CatalogUpdate = {
      description: draft.description || null,
      reference_info: draft.reference_info || null,
      active: draft.active,
      default_severity: draft.default_severity,
      implementation_status: draft.implementation_status,
      recommendation: draft.recommendation || null,
    };
    try {
      const updated = await updateCatalog(selected.kisa_code, body);
      setItems((current) => current.map((item) => item.kisa_code === updated.kisa_code ? updated : item));
      setSelected(updated);
      setDraft(toDraft(updated));
      setError(null);
    } catch {
      setError("카탈로그 항목을 저장하지 못했습니다. 다시 시도해 주세요.");
    }
  };

  const submitCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const created = await createCatalog({
        kisa_code: create.kisa_code,
        name: create.name,
        category: create.category,
        default_severity: create.default_severity,
        description: create.description || undefined,
        criterion_id: create.criterion_id || undefined,
        item_number: create.item_number ? Number(create.item_number) : undefined,
        reference_info: create.reference_info || undefined,
        active: true,
        implementation_status: "미지원",
      });
      setItems((current) => [...current, created].sort((first, second) => first.kisa_code.localeCompare(second.kisa_code)));
      selectItem(created);
      setCreateOpen(false);
      setCreate(emptyCreate);
    } catch (requestError) {
      setError((requestError as AxiosError).response?.status === 409
        ? "같은 KISA 코드가 이미 등록되어 있습니다. 코드를 확인해 주세요."
        : "카탈로그 항목을 등록하지 못했습니다. 다시 시도해 주세요.");
    }
  };

  return (
    <section className="min-w-0">
      <div className="mb-6 flex min-w-0 flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <h1 className="text-3xl font-bold tracking-tight">진단 기준</h1>
        {admin && (
          <button type="button" onClick={() => setCreateOpen(true)} className="secscan-primary-button shrink-0">
            <span aria-hidden="true" className="mr-1.5 text-base leading-none">＋</span>진단 기준 등록
          </button>
        )}
      </div>

      {error && <div role="alert" className="secscan-error-state mb-4 text-sm"><p>{error}</p><button type="button" onClick={() => void loadCatalog()} className="secscan-secondary-button mt-4">다시 시도</button></div>}

      <div className="mb-5 flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative min-w-0 sm:max-w-[340px] sm:flex-none">
          <span aria-hidden="true" className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-secscan-muted"><SearchIcon /></span>
          <input aria-label="카탈로그 검색" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="기준명 또는 식별자 검색" className="w-full" style={{ paddingLeft: "2.5rem" }} />
        </div>
        <select aria-label="분류 필터" value={category} onChange={(event) => setCategory(event.target.value)} className="sm:w-40">
          <option value="">분류: 전체</option>
          {categories.map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
        <select aria-label="구현 상태 필터" value={implementationStatus} onChange={(event) => setImplementationStatus(event.target.value)} className="sm:w-44">
          <option value="">구현 상태: 전체</option>
          {["지원", "부분 지원", "미지원"].map((value) => <option key={value}>{value}</option>)}
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="secscan-empty-state">현재 조건에 맞는 카탈로그 항목이 없습니다.</div>
      ) : (
        <div className={`grid min-w-0 border-y border-secscan-border ${selected ? "lg:grid-cols-[minmax(0,1.15fr)_minmax(400px,0.85fr)]" : "grid-cols-1"} lg:h-[650px]`}>
          <div className="min-w-0 overflow-auto" data-testid="catalog-list">
            <table className="min-w-[720px] w-full border-collapse text-left text-sm" aria-label="진단 기준 목록">
              <thead className="sticky top-0 z-10 border-b border-secscan-border bg-secscan-surface-2 text-xs font-semibold text-secscan-muted">
                <tr>
                  <th scope="col" className="whitespace-nowrap px-5 py-3">진단 항목 코드</th>
                  <th scope="col" className="px-5 py-3">기준명</th>
                  <th scope="col" className="px-5 py-3">분류</th>
                  <th scope="col" className="px-5 py-3">구현 상태</th>
                  <th scope="col" className="whitespace-nowrap px-5 py-3">활성 여부</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secscan-border">
                {filtered.map((item) => (
                  <tr
                    key={item.kisa_code}
                    tabIndex={0}
                    onClick={() => selectItem(item)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        selectItem(item);
                      }
                    }}
                    className={`cursor-pointer transition-colors hover:bg-secscan-surface-2 focus-visible:bg-secscan-surface-2 ${selected?.kisa_code === item.kisa_code ? "bg-violet-500/10" : ""}`}
                  >
                    <td className="whitespace-nowrap px-5 py-4 font-medium text-secscan-muted">{item.kisa_code}</td>
                    <td className="max-w-xs px-5 py-4 font-semibold text-secscan-foreground"><span className="block break-words">{item.name}</span></td>
                    <td className="max-w-40 px-5 py-4 text-secscan-muted"><span className="block break-words">{item.category}</span></td>
                    <td className="whitespace-nowrap px-5 py-4"><span className={`secscan-status-badge ${implementationStatusClass(item.implementation_status)}`}>{item.implementation_status}</span></td>
                    <td className="whitespace-nowrap px-5 py-4"><span className={`inline-flex items-center gap-1.5 text-xs ${item.active ? "text-secscan-foreground" : "text-secscan-muted"}`}><span className={`h-1.5 w-1.5 rounded-full ${item.active ? "bg-secscan-cyan" : "bg-secscan-muted"}`} />{item.active ? "활성" : "비활성"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selected && (
            <aside ref={detailRef} className="min-w-0 overflow-y-auto border-t border-secscan-border bg-secscan-surface p-5 lg:border-l lg:border-t-0 lg:p-6" aria-label="카탈로그 상세">
              <div className="flex min-w-0 items-start justify-between gap-4">
                <div className="min-w-0"><p className="text-sm font-semibold text-secscan-muted">{selected.kisa_code}</p><h2 className="mt-2 break-words text-2xl font-bold tracking-tight">{selected.name}</h2></div>
                <button type="button" onClick={closeDetail} aria-label="카탈로그 상세 닫기" title="닫기" className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded border border-secscan-border text-xl leading-none text-secscan-muted">×</button>
              </div>

              {admin && draft ? (
                <form className="secscan-catalog-edit-form mt-6 space-y-4" onSubmit={save} onMouseDown={(event) => { if ((event.target as HTMLElement).closest("label")?.querySelector("input[readonly]")) event.preventDefault(); }}>
                  <label className="block text-sm font-medium"><span className="inline-flex items-center gap-1.5">진단 항목 코드 <LockIcon /></span><div className="relative mt-2"><input value={selected.kisa_code} readOnly aria-readonly="true" tabIndex={-1} className="pointer-events-none text-secscan-muted" /></div></label>
                  <label className="block text-sm font-medium"><span className="inline-flex items-center gap-1.5">기준 식별자 <LockIcon /></span><input value={selected.criterion_id ?? "-"} readOnly aria-readonly="true" tabIndex={-1} className="pointer-events-none mt-2 text-secscan-muted" /></label>
                  <label className="block text-sm font-medium"><span className="inline-flex items-center gap-1.5">기준명 <LockIcon /></span><input value={selected.name} readOnly aria-readonly="true" tabIndex={-1} className="pointer-events-none mt-2 text-secscan-muted" /></label>
                  <label className="block text-sm font-medium">설명<textarea value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} className="mt-2" /></label>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="block text-sm font-medium"><span className="inline-flex items-center gap-1.5">분류 <LockIcon /></span><input value={selected.category} readOnly aria-readonly="true" tabIndex={-1} className="pointer-events-none mt-2 text-secscan-muted" /></label>
                    <label className="block text-sm font-medium"><span className="inline-flex items-center gap-1.5">항목 번호 <LockIcon /></span><input value={selected.item_number ?? "-"} readOnly aria-readonly="true" tabIndex={-1} className="pointer-events-none mt-2 text-secscan-muted" /></label>
                  </div>
                  <label className="block text-sm font-medium">참조 정보 링크<input value={draft.reference_info} onChange={(event) => setDraft({ ...draft, reference_info: event.target.value })} className="mt-2" /></label>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="block text-sm font-medium">기본 심각도<select value={draft.default_severity} onChange={(event) => setDraft({ ...draft, default_severity: event.target.value })} className="mt-2">{["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => <option key={value}>{value}</option>)}</select></label>
                    <label className="block text-sm font-medium">구현 상태<select value={draft.implementation_status} onChange={(event) => setDraft({ ...draft, implementation_status: event.target.value as CatalogItem["implementation_status"] })} className="mt-2">{["지원", "부분 지원", "미지원"].map((value) => <option key={value}>{value}</option>)}</select></label>
                  </div>
                  <label className="flex cursor-pointer items-center justify-between rounded border border-secscan-border px-3 py-2.5 text-sm font-medium">활성 여부<input aria-label="활성 여부" type="checkbox" checked={draft.active} onChange={(event) => setDraft({ ...draft, active: event.target.checked })} className="peer sr-only" /><span className="ml-auto mr-3 text-xs text-secscan-muted">{draft.active ? "활성" : "비활성"}</span><span aria-hidden="true" className="relative h-5 w-9 rounded-full bg-secscan-border transition-colors peer-checked:bg-secscan-violet after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-4 peer-focus-visible:ring-2 peer-focus-visible:ring-secscan-violet" /></label>
                  <label className="block text-sm font-medium">조치 권고<textarea value={draft.recommendation} onChange={(event) => setDraft({ ...draft, recommendation: event.target.value })} className="mt-2" /></label>
                  <button type="submit" disabled={!hasChanges} className="secscan-primary-button w-full disabled:cursor-not-allowed disabled:opacity-45">변경 사항 저장</button>
                </form>
              ) : (
                <dl className="mt-6 grid min-w-0 gap-4 text-sm">
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">기준 식별자</dt><dd className="mt-1 break-words">{selected.criterion_id ?? "-"}</dd></div>
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">분류 / 항목 번호</dt><dd className="mt-1 break-words">{selected.category} / {selected.item_number ?? "-"}</dd></div>
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">설명</dt><dd className="mt-1 break-words">{selected.description ?? "-"}</dd></div>
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">참조 정보</dt><dd className="mt-1 break-words">{selected.reference_info ?? "-"}</dd></div>
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">기본 심각도 / 구현 상태</dt><dd className="mt-1 break-words">{selected.default_severity} / {selected.implementation_status}</dd></div>
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">활성 여부</dt><dd className="mt-1">{selected.active ? "활성" : "비활성"}</dd></div>
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">조치 권고</dt><dd className="mt-1 break-words whitespace-pre-wrap">{selected.recommendation ?? "-"}</dd></div>
                </dl>
              )}
            </aside>
          )}
        </div>
      )}

      {createOpen && admin && (
        <ActionDrawer title="진단 기준 등록" onClose={() => setCreateOpen(false)} footer={<button form="catalog-create" type="submit" className="secscan-primary-button w-full">등록</button>}>
          <form id="catalog-create" onSubmit={submitCreate} className="space-y-4">
            {([ ["kisa_code", "KISA 코드", true], ["name", "명칭", true], ["category", "분류", true], ["default_severity", "기본 심각도", true], ["description", "설명", false], ["criterion_id", "기준 식별자", false], ["item_number", "항목 번호", false], ["reference_info", "참조 정보", false] ] as const).map(([key, label, required]) => (
              <label key={key} className="block text-sm font-medium">{label}
                {key === "default_severity" ? <select required={required} value={create.default_severity} onChange={(event) => setCreate({ ...create, default_severity: event.target.value })} className="mt-2">{["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => <option key={value}>{value}</option>)}</select> : <input required={required} type={key === "item_number" ? "number" : "text"} value={create[key]} onChange={(event) => setCreate({ ...create, [key]: event.target.value })} className="mt-2" />}
              </label>
            ))}
          </form>
        </ActionDrawer>
      )}
    </section>
  );
}
