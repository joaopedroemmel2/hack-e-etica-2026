const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000/api';
const ACCESS_TOKEN = 'flowlog_access_token';
const REFRESH_TOKEN = 'flowlog_refresh_token';
let refreshPromise: Promise<boolean> | null = null;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

export function getAccessToken() {
  return typeof window === 'undefined' ? null : localStorage.getItem(ACCESS_TOKEN);
}

export function saveTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN, accessToken);
  localStorage.setItem(REFRESH_TOKEN, refreshToken);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN);
  localStorage.removeItem(REFRESH_TOKEN);
}

async function parseError(response: Response) {
  try {
    const body = (await response.json()) as { message?: string | string[] };
    return Array.isArray(body.message) ? body.message.join(', ') : body.message;
  } catch {
    return undefined;
  }
}

async function performRefresh() {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN);
  if (!refreshToken) return false;
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken }),
  });
  if (!response.ok) {
    clearTokens();
    return false;
  }
  const tokens = (await response.json()) as { accessToken: string; refreshToken: string };
  saveTokens(tokens.accessToken, tokens.refreshToken);
  return true;
}

function refreshSession() {
  refreshPromise ??= performRefresh().finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

export async function revokeSession() {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN);
  if (!refreshToken) return;
  try {
    await fetch(`${API_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    });
  } finally {
    clearTokens();
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (response.status === 401 && retry && !path.startsWith('/auth/')) {
    if (await refreshSession()) return apiFetch<T>(path, init, false);
    window.dispatchEvent(new Event('flowlog:unauthorized'));
  }
  if (!response.ok) {
    throw new ApiError((await parseError(response)) ?? 'Não foi possível concluir a operação.', response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export { API_URL };
