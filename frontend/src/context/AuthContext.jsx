import { createContext, useContext, useEffect, useState } from "react";
import { fetchMe, login as loginRequest, logout as logoutRequest } from "../api/authClient";
import { getRefreshToken } from "../api/http";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // On a fresh page load there's no access token in memory yet, but a
    // refresh token may still be in localStorage from last time — the
    // first authenticated call (fetchMe) will trigger http.js's
    // refresh-and-retry path automatically.
    async function restoreSession() {
      if (!getRefreshToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await fetchMe();
        setUser(me);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    restoreSession();
  }, []);

  async function signIn(username, password) {
    await loginRequest(username, password);
    const me = await fetchMe();
    setUser(me);
  }

  async function signOut() {
    await logoutRequest(getRefreshToken());
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
