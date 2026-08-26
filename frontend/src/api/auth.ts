import axios from "axios";

const BASE_URL = "/api";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await axios.post<TokenResponse>(`${BASE_URL}/auth/login`, { email, password });
  return res.data;
}
