import { resolveApiBase } from "./base";

const TOKEN_KEY = "billmind_token";
const ACCOUNT_NAME_KEY = "billmind_account_name";
/** 浏览器持久访客 ID；退出登录后仍保留，用于静默 upsert 同一 guest Account。 */
const GUEST_ID_KEY = "billmind_guest_id";

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

/** 清除 token；保留 guest_id，便于再次静默登录同一访客。 */
export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ACCOUNT_NAME_KEY);
}

export function getOrCreateGuestId(): string {
  let id = localStorage.getItem(GUEST_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(GUEST_ID_KEY, id);
  }
  return id;
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

export async function postLogin(name: string): Promise<LoginResponse> {
  let response: Response;
  try {
    response = await fetch(`${resolveApiBase()}/accounts/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim() }),
    });
  } catch {
    throw new AuthApiError(
      `无法连接后端 API（${resolveApiBase()}）。请先运行：python server/main.py`,
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

/** 有 token 则复用；否则用持久 guest_id 调 login upsert 访客账号。 */
export async function ensureAuthSession(): Promise<LoginResponse> {
  const token = getToken();
  const name = getAccountName();
  if (token && name) {
    return { token, account_id: 0, name };
  }
  const result = await postLogin(`guest_${getOrCreateGuestId()}`);
  setAuth(result.token, result.name);
  return result;
}
