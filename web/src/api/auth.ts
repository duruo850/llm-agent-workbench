const TOKEN_KEY = "billmind_token";
const ACCOUNT_NAME_KEY = "billmind_account_name";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export interface LoginResponse {
  token: string;
  account_id: number;
  name: string;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getAccountName(): string | null {
  return localStorage.getItem(ACCOUNT_NAME_KEY);
}

export function setAuth(token: string, name: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ACCOUNT_NAME_KEY, name);
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ACCOUNT_NAME_KEY);
}

export class AuthApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthApiError";
  }
}

export async function postLogin(name: string): Promise<LoginResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/accounts/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim() }),
    });
  } catch {
    throw new AuthApiError(
      `无法连接后端 API（${API_BASE}）。请先运行：python server/main.py`,
    );
  }

  if (!response.ok) {
    let detail = `登录失败 (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore parse errors
    }
    throw new AuthApiError(detail);
  }

  return (await response.json()) as LoginResponse;
}
