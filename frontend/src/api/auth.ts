import { api } from './client';

export interface AuthUser {
  id: number;
  email: string;
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const { data } = await api.post('/auth/login', { email, password });
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function register(email: string, password: string): Promise<{ access_token: string }> {
  const { data } = await api.post('/auth/register', { email, password });
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await api.get('/auth/me');
  return data;
}

export function getToken(): string | null {
  return localStorage.getItem('token');
}

export function clearToken() {
  localStorage.removeItem('token');
}

// Set default auth header if token exists
const token = localStorage.getItem('token');
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}
