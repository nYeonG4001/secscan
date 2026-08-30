import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthProvider";
import LoginPage from "./LoginPage";
import { getDemoPrefill } from "./loginDemoPrefill";

const { getCurrentUser, login, logout } = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}));
const setItem = vi.fn();

vi.mock("../api/auth", () => ({ getCurrentUser, login, logout }));

describe("LoginPage", () => {
  it("renders empty fields without complete demo configuration or a .local hint", () => {
    render(
      <MemoryRouter>
        <AuthProvider><LoginPage /></AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "SecScan" })).toBeInTheDocument();
    expect(screen.getByLabelText("이메일")).toHaveValue("");
    expect(screen.getByLabelText("이메일")).not.toHaveAttribute("placeholder");
    expect(screen.getByLabelText("비밀번호")).toHaveValue("");
    expect(screen.queryByText(/\.local/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "로그인" })).toBeInTheDocument();
    expect(getDemoPrefill({ MODE: "development", VITE_DEMO_PREFILL: "true" })).toEqual({
      email: "",
      password: "",
    });
  });

  beforeEach(() => {
    login.mockReset();
    getCurrentUser.mockRejectedValue({ response: { status: 401 } });
    setItem.mockReset();
    vi.stubGlobal("localStorage", { setItem });
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("prefills only when every demo configuration value is provided", () => {
    const suffix = String(Date.now());
    const demoEmail = `demo-${suffix}@example.test`;
    const demoPassword = `demo-${suffix}`;
    expect(getDemoPrefill({
      MODE: "development",
      VITE_DEMO_PREFILL: "true",
      VITE_DEMO_ADMIN_EMAIL: demoEmail,
      VITE_DEMO_ADMIN_PASSWORD: demoPassword,
    })).toEqual({ email: demoEmail, password: demoPassword });
  });

  it.each(["test", "production"])("does not prefill in %s mode", (mode) => {
    const suffix = String(Date.now());
    expect(getDemoPrefill({
      MODE: mode,
      VITE_DEMO_PREFILL: "true",
      VITE_DEMO_ADMIN_EMAIL: `demo-${suffix}@example.test`,
      VITE_DEMO_ADMIN_PASSWORD: `demo-${suffix}`,
    })).toEqual({ email: "", password: "" });
  });

  it("does not store login credentials or role in localStorage", async () => {
    login.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    const submittedPassword = String(Date.now());
    render(
      <MemoryRouter>
        <AuthProvider><LoginPage /></AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("이메일"), {
      target: { value: "user@secscan.io" },
    });
    fireEvent.change(screen.getByLabelText("비밀번호"), {
      target: { value: submittedPassword },
    });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() => expect(login).toHaveBeenCalledWith("user@secscan.io", submittedPassword));
    expect(setItem).not.toHaveBeenCalled();
  });
});
