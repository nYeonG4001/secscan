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

    fireEvent.click(screen.getByRole("button", { name: "결과 상세 닫기" }));
    expect(screen.queryByLabelText("탐지 결과 상세")).not.toBeInTheDocument();
    expect(screen.getByTestId("finding-list")).toBeInTheDocument();
  });

  it("clears the session when a finding detail request returns 401", async () => {
    getFindings.mockResolvedValue({ items: [finding], total: 1, limit: 50, offset: 0 });
    getFinding.mockRejectedValue({ response: { status: 401 } });

    renderPage(<FindingsPage analysisId="4" />);
    fireEvent.click(await screen.findByRole("button", { name: /운영체제 명령어 삽입/ }));

    await waitFor(() => expect(auth.clearUser).toHaveBeenCalledOnce());
  });

  it("keeps catalog search and filters read-only for USER", async () => {
    auth.user = { email: "user@secscan.io", role: "USER" };
    getCatalog.mockResolvedValue([catalogItem]);

    renderPage(<CatalogPage />);

    expect(await screen.findByText("운영체제 명령어 삽입")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "새 진단 기준" })).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("카탈로그 검색"), {
      target: { value: "없는 항목" },
    });
    expect(screen.getByText("현재 조건에 맞는 카탈로그 항목이 없습니다.")).toBeInTheDocument();
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

    fireEvent.click(await screen.findByRole("button", { name: "새 진단 기준" }));
    const dialog = await screen.findByRole("dialog", { name: "새 진단 기준" });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByLabelText("KISA 코드")).toBeRequired();
    expect(screen.getByLabelText("기본 심각도")).toBeRequired();
    expect(screen.queryByLabelText("조치 권고")).not.toBeInTheDocument();
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
});
