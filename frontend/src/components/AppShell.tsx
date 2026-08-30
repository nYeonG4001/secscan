import { ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/useAuth";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await signOut();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen min-w-0 overflow-x-hidden bg-secscan-canvas text-secscan-foreground">
      <header className="border-b border-secscan-border bg-secscan-canvas">
        <div className="mx-auto flex h-[72px] max-w-[1440px] min-w-0 items-center gap-3 px-4 sm:gap-6 sm:px-6 lg:px-12">
          <Link to="/projects" className="shrink-0 text-lg font-bold tracking-tight">SecScan</Link>
          <nav className="flex min-w-0 gap-4 text-sm font-semibold sm:gap-7" aria-label="주 메뉴">
            <NavLink to="/projects" className={({ isActive }) => `app-nav-link ${isActive ? "app-nav-link-active" : ""}`}>프로젝트</NavLink>
            <NavLink to="/catalog" className={({ isActive }) => `app-nav-link ${isActive ? "app-nav-link-active" : ""}`}>진단 기준</NavLink>
          </nav>
          <div className="ml-auto flex min-w-0 items-center gap-3 text-sm">
            <span className="max-w-48 truncate text-secscan-muted" title={user?.email}>{user?.email}</span>
            <button type="button" onClick={handleLogout} className="shrink-0 rounded-lg border border-secscan-border px-3 py-1.5 text-sm">
              로그아웃
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1440px] min-w-0 overflow-x-hidden px-6 py-8 lg:px-12">{children}</main>
    </div>
  );
}
