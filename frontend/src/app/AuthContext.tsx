import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { fetchMe, getToken, clearToken, type AuthUser } from '../api/auth';

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState>({
  user: null, loading: true,
  login: async () => {}, register: async () => {}, logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (getToken()) {
      fetchMe().then(setUser).catch(clearToken).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const loginFn = async (email: string, password: string) => {
    const { login } = await import('../api/auth');
    await login(email, password);
    const u = await fetchMe();
    setUser(u);
  };

  const registerFn = async (email: string, password: string) => {
    const { register } = await import('../api/auth');
    await register(email, password);
    const u = await fetchMe();
    setUser(u);
  };

  const logoutFn = () => { clearToken(); setUser(null); };

  return (
    <AuthContext.Provider value={{ user, loading, login: loginFn, register: registerFn, logout: logoutFn }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() { return useContext(AuthContext); }
