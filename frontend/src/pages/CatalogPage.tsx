import { AxiosError } from "axios";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { CatalogItem, CatalogUpdate, createCatalog, getCatalog, updateCatalog } from "../api/catalog";
import { useAuth } from "../auth/useAuth";
import { ActionDrawer } from "../components/ActionDrawer";
import { SESSION_EXPIRED_MESSAGE } from "../auth/RouteGuards";
import { useNavigate } from "react-router-dom";

const emptyCreate = { kisa_code: "", name: "", category: "", default_severity: "MEDIUM", description: "", criterion_id: "", item_number: "", reference_info: "" };

export default function CatalogPage() {
  const { user, clearUser } = useAuth();
  const navigate = useNavigate();
  const admin = user?.role === "ADMIN";
  const [items, setItems] = useState<CatalogItem[]>([]); const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [search, setSearch] = useState(""); const [status, setStatus] = useState(""); const [editing, setEditing] = useState(false); const [createOpen, setCreateOpen] = useState(false); const [create, setCreate] = useState(emptyCreate); const [error, setError] = useState<string | null>(null);
  const loadCatalog = useCallback(async () => {
    try {
      setItems(await getCatalog());
      setError(null);
    } catch (requestError) {
      const status = (requestError as AxiosError).response?.status;
      if (status === 401) {
        clearUser();
        navigate("/login", {
          replace: true,
          state: { message: SESSION_EXPIRED_MESSAGE },
        });
      } else if (status === 403) {
        setError("이 기능은 관리자만 사용할 수 있습니다.");
      } else if (status === 404) {
        setError("요청한 정보를 찾을 수 없습니다.");
      } else {
        setError("카탈로그를 불러오지 못했습니다. 다시 시도해 주세요.");
      }
    }
  }, [clearUser, navigate]);

  useEffect(() => { void loadCatalog(); }, [loadCatalog]);
  const filtered = useMemo(() => items.filter((item) => (!status || item.implementation_status === status) && `${item.kisa_code} ${item.name} ${item.category}`.toLowerCase().includes(search.toLowerCase())), [items, search, status]);
  const save = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); if (!selected) return; const data = new FormData(event.currentTarget); const body: CatalogUpdate = { description: String(data.get("description") || "") || null, reference_info: String(data.get("reference_info") || "") || null, active: data.get("active") === "on", default_severity: String(data.get("default_severity")), implementation_status: String(data.get("implementation_status")) as CatalogItem["implementation_status"], recommendation: String(data.get("recommendation") || "") || null }; try { const updated = await updateCatalog(selected.kisa_code, body); setItems((current) => current.map((item) => item.kisa_code === updated.kisa_code ? updated : item)); setSelected(updated); setEditing(false); setError(null); } catch { setError("카탈로그 항목을 저장하지 못했습니다. 다시 시도해 주세요."); } };
  const submitCreate = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); try { const created = await createCatalog({ kisa_code: create.kisa_code, name: create.name, category: create.category, default_severity: create.default_severity, description: create.description || undefined, criterion_id: create.criterion_id || undefined, item_number: create.item_number ? Number(create.item_number) : undefined, reference_info: create.reference_info || undefined, active: true, implementation_status: "미지원" }); setItems((current) => [...current, created].sort((a, b) => a.kisa_code.localeCompare(b.kisa_code))); setSelected(created); setCreateOpen(false); setCreate(emptyCreate); } catch (requestError) { setError((requestError as AxiosError).response?.status === 409 ? "같은 KISA 코드가 이미 등록되어 있습니다. 코드를 확인해 주세요." : "카탈로그 항목을 등록하지 못했습니다. 다시 시도해 주세요."); } };
  return <section><div className="mb-4 flex justify-between gap-3"><div><h1 className="text-2xl font-bold">진단 기준 카탈로그</h1><p className="text-sm text-gray-500">KISA 진단 기준과 구현 상태를 확인합니다.</p></div>{admin && <button type="button" onClick={() => setCreateOpen(true)}>새 진단 기준</button>}</div>{error && <div role="alert"><p>{error}</p><button type="button" onClick={() => void loadCatalog()}>다시 시도</button></div>}<div className="mb-4 flex gap-2"><input aria-label="카탈로그 검색" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="KISA 코드, 명칭, 분류 검색"/><select aria-label="구현 상태 필터" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">모든 구현 상태</option>{["지원", "부분 지원", "미지원"].map((value) => <option key={value}>{value}</option>)}</select></div>{filtered.length === 0 ? <p>현재 조건에 맞는 카탈로그 항목이 없습니다.</p> : <div className="flex h-[560px] overflow-hidden rounded border border-gray-800 bg-[#121214]"><div className={`${selected ? "w-1/2 border-r" : "w-full"} overflow-y-auto`} data-testid="catalog-list">{filtered.map((item) => <button type="button" key={item.kisa_code} onClick={() => { setSelected(item); setEditing(false); }} className="block w-full border-b border-gray-800 p-4 text-left"><strong>{item.kisa_code}</strong><p>{item.name}</p><p className="text-sm text-gray-400">{item.category} · {item.item_number ?? "-"} · {item.implementation_status}</p></button>)}</div>{selected && <aside className="w-1/2 overflow-y-auto p-5" aria-label="카탈로그 상세"><div className="flex justify-between"><div><h2 className="text-xl font-bold">{selected.kisa_code}</h2><p>{selected.name}</p></div><div>{admin && <button type="button" onClick={() => setEditing((value) => !value)}>{editing ? "취소" : "수정"}</button>}<button type="button" className="ml-2" onClick={() => setSelected(null)}>닫기</button></div></div>{editing && admin ? <form className="mt-5 space-y-3" onSubmit={save}><label>설명<textarea name="description" defaultValue={selected.description ?? ""}/></label><label>참조 정보<input name="reference_info" defaultValue={selected.reference_info ?? ""}/></label><label><input name="active" type="checkbox" defaultChecked={selected.active}/> 활성</label><label>기본 심각도<select name="default_severity" defaultValue={selected.default_severity}>{["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => <option key={value}>{value}</option>)}</select></label><label>구현 상태<select name="implementation_status" defaultValue={selected.implementation_status}>{["지원", "부분 지원", "미지원"].map((value) => <option key={value}>{value}</option>)}</select></label><label>조치 권고<textarea name="recommendation" defaultValue={selected.recommendation ?? ""}/></label><button type="submit">저장</button></form> : <dl className="mt-5 space-y-3"><div><dt>분류 / 항목 번호</dt><dd>{selected.category} / {selected.item_number ?? "-"}</dd></div><div><dt>기준 식별자</dt><dd>{selected.criterion_id ?? "-"}</dd></div><div><dt>설명</dt><dd>{selected.description ?? "-"}</dd></div><div><dt>참조 정보</dt><dd>{selected.reference_info ?? "-"}</dd></div><div><dt>기본 심각도 / 구현 상태</dt><dd>{selected.default_severity} / {selected.implementation_status}</dd></div><div><dt>조치 권고</dt><dd>{selected.recommendation ?? "-"}</dd></div></dl>}</aside>}</div>}{createOpen && admin && <ActionDrawer title="새 진단 기준" onClose={() => setCreateOpen(false)} footer={<button form="catalog-create" type="submit" className="w-full">등록</button>}><form id="catalog-create" onSubmit={submitCreate} className="space-y-3">{([ ["kisa_code", "KISA 코드", true], ["name", "명칭", true], ["category", "분류", true], ["default_severity", "기본 심각도", true], ["description", "설명", false], ["criterion_id", "기준 식별자", false], ["item_number", "항목 번호", false], ["reference_info", "참조 정보", false] ] as const).map(([key, label, required]) => <label key={key} className="block">{label}{key === "default_severity" ? <select required={required} value={create.default_severity} onChange={(e) => setCreate({ ...create, default_severity: e.target.value })}>{["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => <option key={value}>{value}</option>)}</select> : <input required={required} type={key === "item_number" ? "number" : "text"} value={create[key]} onChange={(e) => setCreate({ ...create, [key]: e.target.value })}/>}</label>)}</form></ActionDrawer>}</section>;
}
