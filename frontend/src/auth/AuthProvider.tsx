import { ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";

import { AuthenticatedUser, getCurrentUser, login, logout } from "../api/auth";
import { AuthContext } from "./AuthContext";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [initializationError, setInitializationError] = useState(false);

  const retryAuthentication = useCallback(async () => {
    setLoading(true);
    setInitializationError(false);
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      if ((error as AxiosError).response?.status === 401) {
        setUser(null);
      } else {
        setInitializationError(true);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void retryAuthentication();
  }, [retryAuthentication]);

  const signIn = useCallback(async (email: string, password: string) => {
    const currentUser = await login(email, password);
    setUser(currentUser);
    setInitializationError(false);
    return currentUser;
  }, []);

  const signOut = useCallback(async () => {
    try {
      await logout();
    } finally {
      setUser(null);
    }
  }, []);

  const clearUser = useCallback(() => setUser(null), []);

  const value = useMemo(
    () => ({
      user,
      loading,
      initializationError,
      retryAuthentication,
      signIn,
      signOut,
      clearUser,
    }),
    [clearUser, initializationError, loading, retryAuthentication, signIn, signOut, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
