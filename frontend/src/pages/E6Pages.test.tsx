import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import CatalogPage from "./CatalogPage";
import FindingsPage from "./FindingsPage";
import ProjectsPage from "./ProjectsPage";

const {
  api,
  auth,
  createCatalog,
  createProject,
  getCatalog,
  getFinding,
  getFindings,
  updateCatalog,
} = vi.hoisted(() => ({
  api: { get: vi.fn() },
  auth: { clearUser: vi.fn(), user: null as { email: string; role: "ADMIN" | "USER" } | null },
  createCatalog: vi.fn(),
  createProject: vi.fn(),
  getCatalog: vi.fn(),
  getFinding: vi.fn(),
  getFindings: vi.fn(),
  updateCatalog: vi.fn(),
}));

vi.mock("../api/auth", () => ({ api }));
vi.mock("../api/findings", () => ({ getFinding, getFindings }));
vi.mock("../api/catalog", () => ({ createCatalog, getCatalog, updateCatalog }));
vi.mock("../api/projects", () => ({ createProject }));
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ clearUser: auth.clearUser, user: auth.user }),
}));

const finding = {
  id: 9,
  severity: "HIGH",
  rule_name: "운영체제 명령어 삽입",
  kisa_code: "KISA-005",
  file_path: "src/App.java",
  line: 12,
  end_line: 12,
  language: "JAVA",
  confidence: "UNKNOWN",
  mapping_status: "KISA_MAPPED",
};

const secondFinding = {
  ...finding,
  id: 10,
  rule_name: "SQL 삽입",
  kisa_code: "KISA-006",
  file_path: "src/Query.java",
  line: 24,
};

const catalogItem = {
  kisa_code: "KISA-005",
  criterion_id: "5",
  item_number: 5,
  category: "입력데이터 검증 및 표현",
  name: "운영체제 명령어 삽입",
  description: "설명",
  reference_info: null,
  default_severity: "HIGH",
  active: true,
  implementation_status: "부분 지원" as const,
  recommendation: "외부 입력을 검증합니다.",
};

const secondCatalogItem = {
  ...catalogItem,
  kisa_code: "KISA-006",
  criterion_id: "6",
  item_number: 6,
  name: "SQL 삽입",
};

function renderPage(page: React.ReactNode) {
  return render(<MemoryRouter>{page}</MemoryRouter>);
}

describe("E6 results and catalog pages", () => {
  beforeEach(() => {
    auth.user = { email: "admin@secscan.io", role: "ADMIN" };
    auth.clearUser.mockReset();
    api.get.mockReset();
    createCatalog.mockReset();
    createProject.mockReset();
    getCatalog.mockReset();
    getFinding.mockReset();
    getFindings.mockReset();
    updateCatalog.mockReset();
  });

  afterEach(cleanup);

  it("keeps the result list visible while a USER reads a finding without raw output", async () => {
    auth.user = { email: "user@secscan.io", role: "USER" };
    getFindings.mockResolvedValue({ items: [finding], total: 1, limit: 50, offset: 0 });
    getFinding.mockResolvedValue({
      ...finding,
      analysis_id: 4,
      engine_rule_id: "secscan.java.runtime-exec",
      criterion_id: "5",
      message: "외부 입력이 명령 실행으로 전달됩니다.",
      evidence: "외부 입력이 Runtime.exec에 전달됩니다.",
      code_snippet: "Runtime.getRuntime().exec(command);",
      recommendation: "입력값을 검증합니다.",
      raw_result: { hidden: true },
    });

    renderPage(<FindingsPage analysisId="4" />);

    fireEvent.click(await screen.findByRole("button", { name: /운영체제 명령어 삽입/ }));
    expect(await screen.findByLabelText("탐지 결과 상세")).toBeInTheDocument();
    expect(screen.getByTestId("finding-list")).toBeInTheDocument();
    expect(screen.getByText("탐지 근거")).toBeInTheDocument();
    expect(screen.queryByText("원본 분석 결과")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /운영체제 명령어 삽입/ }));
    expect(screen.queryByLabelText("탐지 결과 상세")).not.toBeInTheDocument();
    expect(screen.getByTestId("finding-list")).toBeInTheDocument();
    expect(getFinding).toHaveBeenCalledOnce();
  });

  it("resets finding-detail scroll when another finding is selected", async () => {
    getFindings.mockResolvedValue({ items: [finding, secondFinding], total: 2, limit: 50, offset: 0 });
    getFinding.mockImplementation(async (id: number) => ({
      ...(id === finding.id ? finding : secondFinding),
      analysis_id: 4,
      engine_rule_id: "secscan.java.rule",
      criterion_id: "5",
      message: "메시지",
      evidence: "근거",
      code_snippet: null,
      recommendation: null,
    }));

    renderPage(<FindingsPage analysisId="4" />);
    fireEvent.click(await screen.findByRole("button", { name: /운영체제 명령어 삽입/ }));
    const detail = await screen.findByLabelText("탐지 결과 상세");
    detail.scrollTop = 160;

    fireEvent.click(screen.getByRole("button", { name: /SQL 삽입/ }));

    await waitFor(() => expect(detail.scrollTop).toBe(0));
    expect(screen.getByRole("heading", { name: "SQL 삽입" })).toBeInTheDocument();
  });

  it("clears the session when a finding detail request returns 401", async () => {
    getFindings.mockResolvedValue({ items: [finding], total: 1, limit: 50, offset: 0 });
    getFinding.mockRejectedValue({ response: { status: 401 } });

    renderPage(<FindingsPage analysisId="4" />);
    fireEvent.click(await screen.findByRole("button", { name: /운영체제 명령어 삽입/ }));

    await waitFor(() => expect(auth.clearUser).toHaveBeenCalledOnce());
  });

  it("shows direct result filters and keeps their API query values", async () => {
    getFindings.mockResolvedValue({ items: [finding], total: 1, limit: 50, offset: 0 });

    renderPage(<FindingsPage analysisId="4" />);

    const severityFilter = await screen.findByLabelText("심각도 필터");
    expect(screen.getByLabelText("KISA 매핑 필터")).toBeInTheDocument();
    expect(screen.getByLabelText("언어 필터")).toBeInTheDocument();
    fireEvent.change(severityFilter, { target: { value: "HIGH" } });

    await waitFor(() => expect(getFindings).toHaveBeenLastCalledWith("4", expect.objectContaining({ severity: "HIGH", limit: 50, offset: 0 })));
    expect(screen.getByRole("button", { name: "필터 초기화" })).toBeInTheDocument();
  });

  it("keeps catalog search and filters read-only for USER", async () => {
    auth.user = { email: "user@secscan.io", role: "USER" };
    getCatalog.mockResolvedValue([catalogItem]);

    renderPage(<CatalogPage />);

    expect(await screen.findByText("운영체제 명령어 삽입")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "진단 기준 등록" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("분류 필터")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("카탈로그 검색"), {
      target: { value: "없는 항목" },
    });
    expect(screen.getByText("현재 조건에 맞는 카탈로그 항목이 없습니다.")).toBeInTheDocument();
  });

  it("keeps the catalog list visible beside the selected inspection panel", async () => {
    getCatalog.mockResolvedValue([catalogItem]);

    renderPage(<CatalogPage />);
    fireEvent.click(await screen.findByText("운영체제 명령어 삽입"));

    expect(screen.getByTestId("catalog-list")).toBeInTheDocument();
    expect(screen.getByLabelText("카탈로그 상세")).toBeInTheDocument();
  });

  it("resets catalog-detail scroll and closes it when the selected item is clicked", async () => {
    getCatalog.mockResolvedValue([catalogItem, secondCatalogItem]);

    renderPage(<CatalogPage />);
    fireEvent.click(await screen.findByRole("row", { name: /KISA-005 운영체제 명령어 삽입/ }));
    const detail = await screen.findByLabelText("카탈로그 상세");
    detail.scrollTop = 160;

    fireEvent.click(screen.getByRole("row", { name: /KISA-006 SQL 삽입/ }));

    await waitFor(() => expect(detail.scrollTop).toBe(0));
    expect(screen.getByRole("heading", { name: "SQL 삽입" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("row", { name: /KISA-006 SQL 삽입/ }));
    expect(screen.queryByLabelText("카탈로그 상세")).not.toBeInTheDocument();
  });

  it("shows the documented catalog 403 guidance and supports retry", async () => {
    getCatalog
      .mockRejectedValueOnce({ response: { status: 403 } })
      .mockResolvedValueOnce([catalogItem]);

    renderPage(<CatalogPage />);

    expect(await screen.findByText("이 기능은 관리자만 사용할 수 있습니다.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "다시 시도" }));
    expect(await screen.findByText("운영체제 명령어 삽입")).toBeInTheDocument();
  });

  it("opens the ADMIN catalog drawer without a create-time recommendation field", async () => {
    getCatalog.mockResolvedValue([catalogItem]);

    renderPage(<CatalogPage />);

    fireEvent.click(await screen.findByRole("button", { name: "진단 기준 등록" }));
    const dialog = await screen.findByRole("dialog", { name: "진단 기준 등록" });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByLabelText("KISA 코드")).toBeRequired();
    expect(screen.getByLabelText("기본 심각도")).toBeRequired();
    expect(screen.queryByLabelText("조치 권고")).not.toBeInTheDocument();
  });

  it("edits only allowed catalog fields and enables save after a change", async () => {
    getCatalog.mockResolvedValue([catalogItem]);
    updateCatalog.mockResolvedValue({ ...catalogItem, active: false });

    renderPage(<CatalogPage />);
    fireEvent.click(await screen.findByText("운영체제 명령어 삽입"));

    expect(screen.getByLabelText("진단 항목 코드")).toHaveAttribute("readonly");
    expect(screen.getByLabelText("기준명")).toHaveAttribute("readonly");
    expect(screen.getByLabelText("분류")).toHaveAttribute("readonly");
    expect(screen.queryByRole("button", { name: "수정" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "변경 사항 저장" })).toBeDisabled();

    fireEvent.click(screen.getByLabelText("활성 여부"));
    fireEvent.click(screen.getByRole("button", { name: "변경 사항 저장" }));

    await waitFor(() => expect(updateCatalog).toHaveBeenCalledWith("KISA-005", {
      description: "설명",
      reference_info: null,
      active: false,
      default_severity: "HIGH",
      implementation_status: "부분 지원",
      recommendation: "외부 입력을 검증합니다.",
    }));
  });

  it("opens the ADMIN project drawer and submits only the supported fields", async () => {
    api.get.mockResolvedValue({ data: [] });
    createProject.mockResolvedValue({ id: 12, name: "새 프로젝트" });

    renderPage(<ProjectsPage />);

    fireEvent.click(await screen.findByRole("button", { name: "새 프로젝트" }));
    fireEvent.change(screen.getByLabelText("프로젝트 이름"), {
      target: { value: "새 프로젝트" },
    });
    fireEvent.change(screen.getByLabelText("설명"), { target: { value: "설명" } });
    fireEvent.click(screen.getByRole("button", { name: "등록" }));

    await waitFor(() => {
      expect(createProject).toHaveBeenCalledWith({ name: "새 프로젝트", description: "설명" });
    });
  });

  it("renders the project summary table with source and latest analysis status", async () => {
    api.get.mockResolvedValue({
      data: [{
        id: 4,
        name: "고객 포털 웹 서비스",
        description: "설명은 목록에서 숨긴다.",
        target_languages: ["JAVA", "JAVASCRIPT"],
        source_status: "REGISTERED",
        latest_analysis_status: "COMPLETED",
        updated_at: "2026-08-30T12:00:00Z",
      }],
    });

    renderPage(<ProjectsPage />);

    expect(await screen.findByRole("columnheader", { name: "프로젝트명" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "최근 분석 상태" })).toBeInTheDocument();
    expect(screen.getByText("등록됨")).toBeInTheDocument();
    expect(screen.getByText("분석 완료")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "고객 포털 웹 서비스" })).toHaveAttribute("href", "/projects/4");
  });
});
