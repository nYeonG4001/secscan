import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
  xsrfCookieName: "secscan_csrf",
  xsrfHeaderName: "X-CSRF-Token",
});

export interface AuthenticatedUser {
  email: string;
  role: string;
}

export async function login(email: string, password: string): Promise<AuthenticatedUser> {
  const res = await api.post<AuthenticatedUser>("/auth/login", { email, password });
  return res.data;
}

export async function getCurrentUser(): Promise<AuthenticatedUser> {
  const res = await api.get<AuthenticatedUser>("/auth/me");
  return res.data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}
