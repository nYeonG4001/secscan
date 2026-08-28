import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { AuthProvider } from "./auth/AuthProvider";
import { FORBIDDEN_MESSAGE, RoleGuard, SESSION_EXPIRED_MESSAGE } from "./auth/RouteGuards";

const { api, getCurrentUser, login, logout } = vi.hoisted(() => ({
  api: { delete: vi.fn(), get: vi.fn(), post: vi.fn() },
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
    api.delete.mockReset();
  });

  afterEach(() => {
    cleanup();
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
    getCurrentUser.mockRejectedValue({ response: { status: 401 } });
    login.mockResolvedValue({ email: `${role.toLowerCase()}@secscan.io`, role });
    api.get.mockResolvedValue({ data: [] });

    renderApp("/login");
    await screen.findByRole("button", { name: "로그인" });
    fireEvent.change(screen.getByLabelText("이메일"), {
      target: { value: `${role.toLowerCase()}@secscan.io` },
    });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password" } });
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

  it("renders the access-management entry point only for ADMIN", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get.mockResolvedValue({ data: { id: 1, name: "관리자 프로젝트", description: null } });

    renderApp("/projects/1");

    expect(await screen.findByRole("button", { name: "접근권한 관리" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "소스 등록" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "분석 실행" })).not.toBeInTheDocument();
  });

  it("opens an admin-only access drawer and closes it with Escape", async () => {
    getCurrentUser.mockResolvedValue({ email: "admin@secscan.io", role: "ADMIN" });
    api.get
      .mockResolvedValueOnce({ data: { id: 1, name: "관리자 프로젝트", description: null } })
      .mockResolvedValueOnce({ data: [] });

    renderApp("/projects/1");
    fireEvent.click(await screen.findByRole("button", { name: "접근권한 관리" }));

    expect(await screen.findByRole("dialog", { name: "접근권한 관리" })).toBeInTheDocument();
    expect(document.body.style.overflow).toBe("hidden");
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "접근권한 관리" })).not.toBeInTheDocument());
    expect(document.body.style.overflow).toBe("");
  });

  it("does not render the access-management drawer for USER", async () => {
    getCurrentUser.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    api.get.mockResolvedValue({ data: { id: 1, name: "사용자 프로젝트", description: null } });

    renderApp("/projects/1");

    expect(await screen.findByRole("heading", { name: "사용자 프로젝트" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "접근권한 관리" })).not.toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "접근권한 관리" })).not.toBeInTheDocument();
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
    const setItem = vi.fn();
    vi.stubGlobal("localStorage", { setItem });
    vi.stubGlobal("sessionStorage", { setItem });
    getCurrentUser.mockRejectedValue({ response: { status: 401 } });
    login.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    api.get.mockResolvedValue({ data: [] });

    renderApp("/login");
    await screen.findByRole("button", { name: "로그인" });
    fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "user@secscan.io" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password" } });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() => expect(login).toHaveBeenCalled());
    expect(setItem).not.toHaveBeenCalled();
  });
});
