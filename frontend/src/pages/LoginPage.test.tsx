import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthProvider";
import LoginPage from "./LoginPage";

const { getCurrentUser, login, logout } = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}));
const setItem = vi.fn();

vi.mock("../api/auth", () => ({ getCurrentUser, login, logout }));

describe("LoginPage", () => {
  it("renders the login form", () => {
    render(
      <MemoryRouter>
        <AuthProvider><LoginPage /></AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "SecScan" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("admin@secscan.local")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "로그인" })).toBeInTheDocument();
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

  it("does not store login credentials or role in localStorage", async () => {
    login.mockResolvedValue({ email: "user@secscan.io", role: "USER" });
    render(
      <MemoryRouter>
        <AuthProvider><LoginPage /></AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("이메일"), {
      target: { value: "user@secscan.io" },
    });
    fireEvent.change(screen.getByLabelText("비밀번호"), {
      target: { value: "correct-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() => expect(login).toHaveBeenCalledWith("user@secscan.io", "correct-password"));
    expect(setItem).not.toHaveBeenCalled();
  });
});
