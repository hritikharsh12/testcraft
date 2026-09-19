import { AUTH_BASE_URL, apiFetch, setAccessToken, setRefreshToken } from "./http";

export async function login(username, password) {
  const data = await apiFetch("/auth/login/", {
    baseUrl: AUTH_BASE_URL,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  setAccessToken(data.access);
  setRefreshToken(data.refresh);
  return data;
}

export async function register(username, email, password) {
  return apiFetch("/auth/register/", {
    baseUrl: AUTH_BASE_URL,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
}

export async function fetchMe() {
  return apiFetch("/auth/me/", { baseUrl: AUTH_BASE_URL });
}

export async function logout(refreshToken) {
  try {
    await apiFetch("/auth/logout/", {
      baseUrl: AUTH_BASE_URL,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });
  } finally {
    setAccessToken(null);
    setRefreshToken(null);
  }
}
