import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "./useAuth";

export const SESSION_EXPIRED_MESSAGE = "로그인 정보가 만료되었거나 유효하지 않습니다. 다시 로그인해 주세요.";
export const FORBIDDEN_MESSAGE = "이 기능은 관리자만 사용할 수 있습니다.";

export function AuthLoading() {
  return <p className="p-8 text-sm text-gray-500">인증 정보를 확인하는 중...</p>;
}

export function AuthInitializationError() {
  const { retryAuthentication } = useAuth();

  return (
    <div className="p-8" role="alert">
      <p>인증 정보를 확인하지 못했습니다. 다시 시도해 주세요.</p>
      <button type="button" onClick={() => void retryAuthentication()} className="mt-4 rounded border px-3 py-2 text-sm">
        다시 시도
      </button>
    </div>
  );
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { initializationError, loading, user } = useAuth();
  const location = useLocation();

  if (loading) return <AuthLoading />;
  if (initializationError) return <AuthInitializationError />;
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location, message: SESSION_EXPIRED_MESSAGE }} />;
  }
  return <>{children}</>;
}

export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { initializationError, loading, user } = useAuth();
  if (loading) return <AuthLoading />;
  if (initializationError) return <AuthInitializationError />;
  return user ? <Navigate to="/projects" replace /> : <>{children}</>;
}

export function RoleGuard({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "ADMIN") {
    return <p role="alert" className="p-4 text-sm text-red-600">{FORBIDDEN_MESSAGE}</p>;
  }
  return <>{children}</>;
}
