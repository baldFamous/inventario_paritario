const API_BASE = '/api/v1';

function getTokens() {
  if (typeof window === 'undefined') return { access: null, refresh: null };
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function refreshAccessToken(): Promise<string | null> {
  const { refresh } = getTokens();
  if (!refresh) return null;
  try {
    const res = await fetch(`${API_BASE}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    setTokens(data.access, data.refresh || refresh);
    return data.access;
  } catch {
    return null;
  }
}

export async function apiFetch<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const { access } = getTokens();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (access) headers['Authorization'] = `Bearer ${access}`;

  let res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (res.status === 401 && access) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`;
      res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    } else {
      clearTokens();
      window.location.href = '/login';
      throw new Error('Sesión expirada');
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || error.error || `Error ${res.status}`);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error('Credenciales inválidas');
  const data = await res.json();
  setTokens(data.access, data.refresh);
  return data;
}
