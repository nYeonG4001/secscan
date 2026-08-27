import { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/useAuth";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await signOut();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4">
          <Link to="/projects" className="font-bold">SecScan</Link>
          <nav className="flex gap-4 text-sm" aria-label="주 메뉴">
            <Link to="/projects">프로젝트</Link>
            <Link to="/catalog">진단 기준</Link>
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span>{user?.email}</span>
            <button type="button" onClick={handleLogout} className="rounded border px-3 py-1">
              로그아웃
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-6">{children}</main>
    </div>
  );
}
