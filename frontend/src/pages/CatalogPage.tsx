import { AxiosError } from "axios";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { CatalogItem, CatalogUpdate, createCatalog, getCatalog, updateCatalog } from "../api/catalog";
import { useAuth } from "../auth/useAuth";
import { ActionDrawer } from "../components/ActionDrawer";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";

const emptyCreate = { kisa_code: "", name: "", category: "", default_severity: "MEDIUM", description: "", criterion_id: "", item_number: "", reference_info: "" };

function implementationStatusClass(status: CatalogItem["implementation_status"]) {
  if (status === "지원") return "secscan-status-success";
  if (status === "부분 지원") return "secscan-status-active";
  return "secscan-status-neutral";
}

export default function CatalogPage() {
  const { user, clearUser } = useAuth();
  const navigate = useNavigate();
  const admin = user?.role === "ADMIN";
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [editing, setEditing] = useState(false);
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

  const filtered = useMemo(() => items.filter((item) => (
    (!status || item.implementation_status === status)
    && `${item.kisa_code} ${item.name} ${item.category}`.toLowerCase().includes(search.toLowerCase())
  )), [items, search, status]);

  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    const body: CatalogUpdate = {
      description: String(data.get("description") || "") || null,
      reference_info: String(data.get("reference_info") || "") || null,
      active: data.get("active") === "on",
      default_severity: String(data.get("default_severity")),
      implementation_status: String(data.get("implementation_status")) as CatalogItem["implementation_status"],
      recommendation: String(data.get("recommendation") || "") || null,
    };
    try {
      const updated = await updateCatalog(selected.kisa_code, body);
      setItems((current) => current.map((item) => item.kisa_code === updated.kisa_code ? updated : item));
      setSelected(updated);
      setEditing(false);
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
      setItems((current) => [...current, created].sort((a, b) => a.kisa_code.localeCompare(b.kisa_code)));
      setSelected(created);
      setCreateOpen(false);
      setCreate(emptyCreate);
    } catch (requestError) {
      setError((requestError as AxiosError).response?.status === 409 ? "같은 KISA 코드가 이미 등록되어 있습니다. 코드를 확인해 주세요." : "카탈로그 항목을 등록하지 못했습니다. 다시 시도해 주세요.");
    }
  };

  return (
    <section className="min-w-0">
      <div className="mb-6 flex min-w-0 flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0"><h1 className="text-3xl font-bold tracking-tight">진단 기준 카탈로그</h1><p className="mt-2 text-sm text-secscan-muted">KISA 진단 기준과 구현 상태를 확인합니다.</p></div>
        {admin && <button type="button" onClick={() => setCreateOpen(true)} className="secscan-primary-button shrink-0">새 진단 기준</button>}
      </div>

      {error && <div role="alert" className="secscan-error-state mb-4 text-sm"><p>{error}</p><button type="button" onClick={() => void loadCatalog()} className="secscan-secondary-button mt-4">다시 시도</button></div>}

      <div className="mb-5 flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center">
        <input aria-label="카탈로그 검색" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="KISA 코드, 명칭, 분류 검색" className="sm:max-w-sm" />
        <select aria-label="구현 상태 필터" value={status} onChange={(event) => setStatus(event.target.value)} className="sm:w-44"><option value="">모든 구현 상태</option>{["지원", "부분 지원", "미지원"].map((value) => <option key={value}>{value}</option>)}</select>
      </div>

      {filtered.length === 0 ? (
        <div className="secscan-empty-state">현재 조건에 맞는 카탈로그 항목이 없습니다.</div>
      ) : (
        <div className={`secscan-panel grid min-w-0 overflow-hidden ${selected ? "lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]" : "grid-cols-1"} lg:h-[600px]`}>
          <div className="min-w-0 overflow-y-auto" data-testid="catalog-list">
            {filtered.map((item) => (
              <button type="button" key={item.kisa_code} onClick={() => { setSelected(item); setEditing(false); }} aria-pressed={selected?.kisa_code === item.kisa_code} className={`block w-full min-w-0 border-b border-secscan-border px-5 py-4 text-left last:border-b-0 ${selected?.kisa_code === item.kisa_code ? "bg-violet-500/10" : "hover:bg-secscan-surface-2"}`}>
                <div className="flex min-w-0 flex-wrap items-center justify-between gap-3"><strong className="break-all text-sm">{item.kisa_code}</strong><span className={`secscan-status-badge ${implementationStatusClass(item.implementation_status)}`}>{item.implementation_status}</span></div>
                <p className="mt-2 break-words font-semibold">{item.name}</p>
                <p className="mt-2 break-words text-sm text-secscan-muted">{item.category} · {item.item_number ?? "-"} · {item.active ? "활성" : "비활성"}</p>
              </button>
            ))}
          </div>

          {selected && (
            <aside className="min-w-0 overflow-y-auto border-t border-secscan-border bg-secscan-surface p-5 lg:border-l lg:border-t-0 lg:p-6" aria-label="카탈로그 상세">
              <div className="flex min-w-0 items-start justify-between gap-4">
                <div className="min-w-0"><p className="text-sm font-semibold text-secscan-muted">{selected.kisa_code}</p><h2 className="mt-2 break-words text-2xl font-bold tracking-tight">{selected.name}</h2></div>
                <div className="flex shrink-0 gap-2">{admin && <button type="button" onClick={() => setEditing((value) => !value)} className="secscan-secondary-button px-3 py-1.5 text-xs">{editing ? "취소" : "수정"}</button>}<button type="button" onClick={() => setSelected(null)} className="secscan-secondary-button px-3 py-1.5 text-xs">닫기</button></div>
              </div>

              {editing && admin ? (
                <form className="mt-6 space-y-4" onSubmit={save}>
                  <label className="block text-sm font-medium">설명<textarea name="description" defaultValue={selected.description ?? ""} className="mt-2" /></label>
                  <label className="block text-sm font-medium">참조 정보<input name="reference_info" defaultValue={selected.reference_info ?? ""} className="mt-2" /></label>
                  <label className="flex items-center gap-2 text-sm font-medium"><input name="active" type="checkbox" defaultChecked={selected.active} />활성</label>
                  <label className="block text-sm font-medium">기본 심각도<select name="default_severity" defaultValue={selected.default_severity} className="mt-2">{["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => <option key={value}>{value}</option>)}</select></label>
                  <label className="block text-sm font-medium">구현 상태<select name="implementation_status" defaultValue={selected.implementation_status} className="mt-2">{["지원", "부분 지원", "미지원"].map((value) => <option key={value}>{value}</option>)}</select></label>
                  <label className="block text-sm font-medium">조치 권고<textarea name="recommendation" defaultValue={selected.recommendation ?? ""} className="mt-2" /></label>
                  <button type="submit" className="secscan-primary-button">저장</button>
                </form>
              ) : (
                <dl className="mt-6 grid min-w-0 gap-4 text-sm">
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">분류 / 항목 번호</dt><dd className="mt-1 break-words">{selected.category} / {selected.item_number ?? "-"}</dd></div>
                  <div className="secscan-panel p-3"><dt className="text-xs font-semibold text-secscan-muted">기준 식별자</dt><dd className="mt-1 break-words">{selected.criterion_id ?? "-"}</dd></div>
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
        <ActionDrawer title="새 진단 기준" onClose={() => setCreateOpen(false)} footer={<button form="catalog-create" type="submit" className="secscan-primary-button w-full">등록</button>}>
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
