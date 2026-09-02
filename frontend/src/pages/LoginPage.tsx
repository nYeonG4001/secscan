import { useState, FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { getDemoPrefill } from "./loginDemoPrefill";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn } = useAuth();
  const [initialCredentials] = useState(getDemoPrefill);
  const [email, setEmail] = useState(initialCredentials.email);
  const [password, setPassword] = useState(initialCredentials.password);
  const [error, setError] = useState<string | null>(location.state?.message ?? null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signIn(email, password);
      navigate("/projects", { replace: true });
    } catch {
      setError("이메일 또는 비밀번호가 올바르지 않습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-secscan-canvas px-4 py-8">
      <div className="w-full max-w-sm space-y-6 p-6 sm:p-8">
        <div>
          <h1 className="text-center text-3xl font-bold tracking-tight text-secscan-foreground">SecScan</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-secscan-foreground">
              이메일
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full border border-secscan-border rounded-lg px-3 py-2 text-sm focus:border-secscan-violet focus:outline-none focus:ring-2 focus:ring-secscan-violet/40"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-secscan-foreground">
              비밀번호
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border border-secscan-border rounded-lg px-3 py-2 text-sm focus:border-secscan-violet focus:outline-none focus:ring-2 focus:ring-secscan-violet/40"
            />
          </div>
          {error && <p role="alert" className="secscan-error-state text-sm">{error}</p>}
          <div className="pt-6">
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg border-secscan-violet bg-secscan-violet py-2 text-sm font-semibold text-secscan-canvas focus:border-secscan-violet focus:outline-none focus:ring-2 focus:ring-secscan-violet/40 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "로그인 중..." : "로그인"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
