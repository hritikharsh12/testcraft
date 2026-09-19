const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL || "http://localhost:8000";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

const REFRESH_TOKEN_KEY = "testcraft_refresh_token";

// Access token is deliberately kept in memory only (not localStorage) so it
// never sits somewhere an XSS payload could quietly read it later. The
// refresh token DOES need to survive a page reload, so it's in
// localStorage — a real deployment should move this to an httpOnly cookie
// set directly by the Django auth service instead; that's a backend change
// (SIMPLE_JWT doesn't do this by default), noted here rather than hidden.
let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export function setRefreshToken(token) {
  if (token) localStorage.setItem(REFRESH_TOKEN_KEY, token);
  else localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new ApiError("Not signed in.", 401);

  const res = await fetch(`${AUTH_BASE_URL}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    setAccessToken(null);
    setRefreshToken(null);
    throw new ApiError("Session expired. Sign in again.", 401);
  }

  const data = await res.json();
  // ROTATE_REFRESH_TOKENS is on in the Django settings, so every refresh
  // call returns a brand new refresh token too — the old one is now dead.
  setAccessToken(data.access);
  setRefreshToken(data.refresh);
  return data.access;
}

/**
 * Wraps fetch with the access token attached, and transparently refreshes
 * + retries exactly once on a 401 before giving up. `baseUrl` picks which
 * backend service this call targets, since auth lives on Django and
 * everything else lives on FastAPI.
 */
export async function apiFetch(path, { baseUrl = API_BASE_URL, ...options } = {}) {
  const doFetch = (token) =>
    fetch(`${baseUrl}${path}`, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

  let response = await doFetch(accessToken);

  if (response.status === 401 && getRefreshToken()) {
    const newToken = await refreshAccessToken();
    response = await doFetch(newToken);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(body.detail || `Request failed (${response.status})`, response.status);
  }

  if (response.status === 204 || response.status === 205) return null;
  return response.json();
}

export { AUTH_BASE_URL, API_BASE_URL };
