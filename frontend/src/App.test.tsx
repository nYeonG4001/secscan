import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { AuthProvider } from "./auth/AuthProvider";
import { FORBIDDEN_MESSAGE, RoleGuard, SESSION_EXPIRED_MESSAGE } from "./auth/RouteGuards";

const { api, getCurrentUser, login, logout } = vi.hoisted(() => ({
  api: { delete: vi.fn(), get: vi.fn(), post: vi.fn(), put: vi.fn() },
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}));

vi.mock("./api/auth", () => ({ api, getCurrentUser, login, logout }));

function renderApp(path: string) {
  window.history.pushState({}, "", path);
  return render(<App />);
}

describe("authentication routes", () => {
  beforeEach(() => {
    getCurrentUser.mockReset();
    login.mockReset();
    logout.mockReset();
    api.get.mockReset();
    api.post.mockReset();
    api.put.mockReset();
    api.delete.mockReset();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
    window.history.pushState({}, "", "/");
  });

  it("renders the protected projects page after /auth/me succeeds", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get.mockResolvedValue({ data: [] });

    renderApp("/projects");

    expect(screen.getByText("인증 정보를 확인하는 중...")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "프로젝트" })).toBeInTheDocument();
    expect(getCurrentUser).toHaveBeenCalledOnce();
    expect(screen.getByText("관리자")).toBeInTheDocument();
  });

  it("redirects a /auth/me 401 to login with the generic session message", async () => {
    getCurrentUser.mockRejectedValue({ response: { status: 401 } });

    renderApp("/projects");

    expect(await screen.findByText(SESSION_EXPIRED_MESSAGE)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "로그인" })).toBeInTheDocument();
  });

  it("keeps the user off the login redirect when /auth/me has a server error and retries", async () => {
    getCurrentUser
      .mockRejectedValueOnce({ response: { status: 500 } })
      .mockResolvedValueOnce({ email: "user@secscan.io", role: "USER" });
    api.get.mockResolvedValue({ data: [] });

    renderApp("/projects");

    expect(await screen.findByText("인증 정보를 확인하지 못했습니다. 다시 시도해 주세요.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "로그인" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "다시 시도" }));
    expect(await screen.findByRole("heading", { name: "프로젝트" })).toBeInTheDocument();
  });

  it.each(["ADMIN", "USER"])("moves %s to /projects after login", async (role) => {
    const submittedPassword = String(Date.now());
    getCurrentUser.mockRejectedValue({ response: { status: 401 } });
    login.mockResolvedValue({ email: `${role.toLowerCase()}@secscan.io`, role });
    api.get.mockResolvedValue({ data: [] });

    renderApp("/login");
    await screen.findByRole("button", { name: "로그인" });
    fireEvent.change(screen.getByLabelText("이메일"), {
      target: { value: `${role.toLowerCase()}@secscan.io` },
    });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: submittedPassword } });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    expect(await screen.findByRole("heading", { name: "프로젝트" })).toBeInTheDocument();
  });

  it("hides admin actions from USER and renders project navigation for both roles", async () => {
    getCurrentUser.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    api.get.mockResolvedValue({ data: [] });

    renderApp("/projects");

    expect(await screen.findByRole("link", { name: "프로젝트" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "진단 기준" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "새 프로젝트" })).not.toBeInTheDocument();
  });

  it("renders the consolidated project actions only for ADMIN", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get.mockResolvedValue({ data: { id: 1, name: "관리자 프로젝트", description: null } });

    renderApp("/projects/1");

    expect(await screen.findByRole("button", { name: "관리" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "분석" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "접근권한 관리" })).not.toBeInTheDocument();
  });

  it("opens the admin project-management drawer and closes it with Escape", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get
      .mockResolvedValueOnce({ data: { id: 1, name: "관리자 프로젝트", description: null } })
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [] });

    renderApp("/projects/1");
    fireEvent.click(await screen.findByRole("button", { name: "관리" }));

    expect(await screen.findByRole("dialog", { name: "프로젝트 관리" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "사용자 접근권한" })).toBeInTheDocument();
    expect(document.body.style.overflow).toBe("hidden");
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "프로젝트 관리" })).not.toBeInTheDocument());
    expect(document.body.style.overflow).toBe("");
  });

  it("disables the analysis action while the project has an active analysis", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get
      .mockResolvedValueOnce({ data: { id: 1, name: "분석 중 프로젝트", description: null } })
      .mockResolvedValueOnce({ data: [{ id: 9, status: "RUNNING" }] });

    renderApp("/projects/1");

    await waitFor(() => expect(screen.getByRole("button", { name: "분석" })).toBeDisabled());
    expect(screen.getByText("분석 요청 시각")).toBeInTheDocument();
    expect(screen.getByText("분석 진행 중")).toBeInTheDocument();
  });

  it("does not render the access-management drawer for USER", async () => {
    getCurrentUser.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    api.get.mockResolvedValue({ data: { id: 1, name: "사용자 프로젝트", description: null } });

    renderApp("/projects/1");

    expect(await screen.findByRole("heading", { name: "사용자 프로젝트" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "관리" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "분석" })).not.toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "프로젝트 관리" })).not.toBeInTheDocument();
  });

  it("shows analysis request, start, and completion fields in a keyboard-accessible history row", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get
      .mockResolvedValueOnce({ data: { id: 1, name: "이력 프로젝트", description: null, source_status: "REGISTERED" } })
      .mockResolvedValueOnce({
        data: [{
          id: 11,
          project_id: 1,
          executed_by: 1,
          status: "COMPLETED",
          created_at: "2026-08-30T09:00:00Z",
          started_at: "2026-08-30T09:01:00Z",
          completed_at: "2026-08-30T09:02:00Z",
        }],
      });

    renderApp("/projects/1");

    expect(await screen.findByRole("columnheader", { name: "분석 요청 시각" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "시작 시각" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "완료 시각" })).toBeInTheDocument();
    const analysisRow = screen.getByRole("row", { name: /분석 완료/ });
    expect(analysisRow).toHaveAttribute("tabindex", "0");
    fireEvent.keyDown(analysisRow, { key: "Enter" });
    await waitFor(() => expect(window.location.pathname).toBe("/projects/1/analyses/11"));
  });

  it("shows the generic not-found message for project detail 404", async () => {
    getCurrentUser.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    api.get.mockRejectedValue({ response: { status: 404 } });

    renderApp("/projects/999");

    expect(await screen.findByText("요청한 정보를 찾을 수 없습니다.")).toBeInTheDocument();
  });

  it("clears the session when a protected project request returns 401", async () => {
    getCurrentUser.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    api.get.mockRejectedValue({ response: { status: 401 } });

    renderApp("/projects");

    expect(await screen.findByText(SESSION_EXPIRED_MESSAGE)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "로그인" })).toBeInTheDocument();
  });

  it("shows the generic forbidden message through RoleGuard", async () => {
    getCurrentUser.mockResolvedValue({ email: "user@secscan.io", role: "USER" });

    render(
      <MemoryRouter>
        <AuthProvider><RoleGuard><p>관리자 화면</p></RoleGuard></AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText(FORBIDDEN_MESSAGE)).toBeInTheDocument();
    expect(screen.queryByText("관리자 화면")).not.toBeInTheDocument();
  });

  it("does not persist role or authentication tokens in browser storage", async () => {
    const submittedPassword = String(Date.now());
    const setItem = vi.fn();
    vi.stubGlobal("localStorage", { setItem });
    vi.stubGlobal("sessionStorage", { setItem });
    getCurrentUser.mockRejectedValue({ response: { status: 401 } });
    login.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    api.get.mockResolvedValue({ data: [] });

    renderApp("/login");
    await screen.findByRole("button", { name: "로그인" });
    fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "user@secscan.io" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: submittedPassword } });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() => expect(login).toHaveBeenCalled());
    expect(setItem).not.toHaveBeenCalled();
  });

  it("polls active analysis status and stops polling after the page unmounts", async () => {
    vi.useFakeTimers();
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get.mockResolvedValue({
      data: {
        id: 7, project_id: 1, executed_by: 1, status: "RUNNING", created_at: "2026-08-28T00:00:00Z",
      },
    });

    const view = renderApp("/projects/1/analyses/7");
    await act(async () => { await Promise.resolve(); });
    expect(screen.getByText("상태: RUNNING")).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledTimes(2);
    await act(async () => { await Promise.resolve(); });
    await act(async () => { await vi.advanceTimersByTimeAsync(3_000); });
    expect(api.get).toHaveBeenCalledTimes(3);
    view.unmount();
    await act(async () => { await vi.advanceTimersByTimeAsync(6_000); });
    expect(api.get).toHaveBeenCalledTimes(3);
    vi.useRealTimers();
  });

  it("keeps a polling transport error refreshable instead of rendering it as failed", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    let analysisRequestCount = 0;
    api.get.mockImplementation((url: string) => {
      if (url === "/analyses/7") {
        analysisRequestCount += 1;
        if (analysisRequestCount === 1) return Promise.reject({ response: { status: 500 } });
        return Promise.resolve({
          data: {
            id: 7, project_id: 1, executed_by: 1, status: "COMPLETED", created_at: "2026-08-28T00:00:00Z",
          },
        });
      }
      if (url === "/projects/1") return Promise.resolve({ data: { name: "프로젝트" } });
      return Promise.resolve({ data: { items: [], total: 0, limit: 50, offset: 0 } });
    });

    renderApp("/projects/1/analyses/7");
    expect(await screen.findByText("상태를 갱신하지 못했습니다. 분석은 계속 진행 중일 수 있습니다.")).toBeInTheDocument();
    expect(screen.queryByText("분석을 완료하지 못했습니다. 관리자에게 문의하세요.")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "새로고침" }));
    expect(await screen.findByRole("heading", { name: "탐지 결과" })).toBeInTheDocument();
    expect(screen.queryByText("상태: COMPLETED")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "분석 상태" })).not.toBeInTheDocument();
  });

  it("returns to login when analysis polling receives 401", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get.mockRejectedValue({ response: { status: 401 } });

    renderApp("/projects/1/analyses/7");

    expect(await screen.findByText(SESSION_EXPIRED_MESSAGE)).toBeInTheDocument();
  });

  it.each([
    ["ANALYSIS_ACTIVE", { analysis_id: 8 }, "analysis"],
    ["SOURCE_UPLOAD_IN_PROGRESS", {}, "upload"],
  ])("handles project analysis conflict %s", async (code, data, expected) => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get.mockImplementation((url: string) => {
      if (url === "/projects/1") return Promise.resolve({ data: { id: 1, name: "등록 프로젝트" } });
      if (url === "/analyses/") return Promise.resolve({ data: [] });
      if (url === "/analyses/8") {
        return Promise.resolve({
          data: { id: 8, project_id: 1, executed_by: 1, status: "PENDING", created_at: "2026-08-28T00:00:00Z" },
        });
      }
      return Promise.resolve({ data: [] });
    });
    api.post.mockImplementation((url: string) => {
      if (url === "/projects/1/source/preflight") return Promise.resolve({ data: { safe: true } });
      return Promise.reject({ response: { status: 409, data: { code, ...data } } });
    });
    api.put.mockResolvedValue({ data: { project_id: 1, source_status: "REGISTERED", target_languages: ["JAVA"] } });

    renderApp("/projects/1");
    fireEvent.click(await screen.findByRole("button", { name: "분석" }));
    vi.useFakeTimers();
    fireEvent.change(screen.getByLabelText("ZIP 파일"), {
      target: { files: [new File(["source"], "sample.zip", { type: "application/zip" })] },
    });
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await vi.advanceTimersByTimeAsync(3_000);
    });
    expect(api.put).not.toHaveBeenCalled();
    vi.useRealTimers();
    fireEvent.click(screen.getByRole("button", { name: "분석 실행" }));

    if (expected === "analysis") {
      expect(await screen.findByRole("heading", { name: "분석 상태" })).toBeInTheDocument();
    } else {
      expect(await screen.findByText("소스 업로드가 진행 중입니다. 완료 후 다시 시도해 주세요.")).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "등록 프로젝트" })).toBeInTheDocument();
    }
  });
});
