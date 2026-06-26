import { clearAuth, getToken } from "./auth";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function authFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const token = getToken();
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(
      `无法连接后端 API（${API_BASE}）。请先运行：python server/main.py`,
    );
  }

  if (response.status === 401) {
    clearAuth();
    window.location.reload();
  }

  return response;
}

export { API_BASE };
