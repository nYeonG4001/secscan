import { createContext } from "react";

import { AuthenticatedUser } from "../api/auth";

export interface AuthContextValue {
  user: AuthenticatedUser | null;
  loading: boolean;
  initializationError: boolean;
  retryAuthentication: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<AuthenticatedUser>;
  signOut: () => Promise<void>;
  clearUser: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
