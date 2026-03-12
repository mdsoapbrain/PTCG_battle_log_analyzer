import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

interface User {
  id: string;
  email: string;
  name?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name?: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

/**
 * Stub auth provider. In stub mode, we simulate auth.
 * When switching to Supabase JWT mode, replace the internals here.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const stored = localStorage.getItem("ptcg_user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch { /* ignore */ }
    }
    setIsLoading(false);
  }, []);

  const signIn = useCallback(async (email: string, _password: string) => {
    // Stub: create a fake user session
    const stubUser: User = {
      id: `user_${email.split("@")[0]}`,
      email,
      name: email.split("@")[0],
    };
    localStorage.setItem("ptcg_user", JSON.stringify(stubUser));
    localStorage.setItem("auth_token", `user:${stubUser.id}`);
    setUser(stubUser);
  }, []);

  const signUp = useCallback(async (email: string, _password: string, name?: string) => {
    const stubUser: User = {
      id: `user_${email.split("@")[0]}`,
      email,
      name: name || email.split("@")[0],
    };
    localStorage.setItem("ptcg_user", JSON.stringify(stubUser));
    localStorage.setItem("auth_token", `user:${stubUser.id}`);
    setUser(stubUser);
  }, []);

  const signOut = useCallback(() => {
    localStorage.removeItem("ptcg_user");
    localStorage.removeItem("auth_token");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
