import { resolveApiBase } from "./base";

const TOKEN_KEY = "billmind_token";
const ACCOUNT_NAME_KEY = "billmind_account_name";

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

export function isGuestAccount(name: string | null | undefined): boolean {
  return Boolean(name?.startsWith("guest_"));
}

export class AuthApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthApiError";
  }
}

type SessionExpiredHandler = () => void;

let sessionExpiredHandler: SessionExpiredHandler | null = null;

/** App 注册：token 过期 / 401 时弹出游客或登录选择，避免静默 reload。 */
export function setSessionExpiredHandler(handler: SessionExpiredHandler | null): void {
  sessionExpiredHandler = handler;
}

export function notifySessionExpired(): void {
  clearAuth();
  if (sessionExpiredHandler) {
    sessionExpiredHandler();
    return;
  }
  window.location.reload();
}

async function postJson(
  path: string,
  body: Record<string, unknown>,
): Promise<LoginResponse> {
  let response: Response;
  try {
    response = await fetch(`${resolveApiBase()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new AuthApiError(
      `无法连接后端 API（${resolveApiBase()}）。请先运行：python server/main.py`,
    );
  }

  if (!response.ok) {
    let detail = `请求失败 (${response.status})`;
    try {
      const parsed = (await response.json()) as { detail?: string };
      if (typeof parsed.detail === "string") {
        detail = parsed.detail;
      }
    } catch {
      // ignore
    }
    throw new AuthApiError(detail);
  }

  return (await response.json()) as LoginResponse;
}

export async function postLogin(
  name: string,
  password: string,
): Promise<LoginResponse> {
  return postJson("/accounts/login", {
    name: name.trim(),
    password,
  });
}

export async function postRegister(
  name: string,
  password: string,
): Promise<LoginResponse> {
  return postJson("/accounts/register", {
    name: name.trim(),
    password,
  });
}

export async function postGuestLogin(): Promise<LoginResponse> {
  return postJson("/accounts/login", { guest: true });
}

/** 本地已有 token 则复用；否则游客登录并持久化。 */
export async function ensureAuthSession(): Promise<LoginResponse> {
  const token = getToken();
  const name = getAccountName();
  if (token && name) {
    return { token, account_id: 0, name };
  }
  const result = await postGuestLogin();
  setAuth(result.token, result.name);
  return result;
}
