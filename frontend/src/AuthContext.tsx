import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import type { LoginResponse } from "./types";

interface AuthContextValue {
  auth: LoginResponse | null;
  login: (data: LoginResponse) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<LoginResponse | null>(() => {
    const stored = sessionStorage.getItem("auth");
    return stored ? (JSON.parse(stored) as LoginResponse) : null;
  });

  const login = (data: LoginResponse) => {
    sessionStorage.setItem("auth", JSON.stringify(data));
    setAuth(data);
  };

  const logout = () => {
    sessionStorage.removeItem("auth");
    setAuth(null);
  };

  return (
    <AuthContext.Provider value={{ auth, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
