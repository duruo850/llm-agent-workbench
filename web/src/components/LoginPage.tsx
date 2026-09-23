import { useState, type FormEvent } from "react";

import {
  AuthApiError,
  postLogin,
  postRegister,
  setAuth,
} from "../api/auth";

interface LoginPageProps {
  onLogin: () => void;
  onCancel?: () => void;
}

export default function LoginPage({ onLogin, onCancel }: LoginPageProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || !password) {
      setError("请输入账号和密码");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result =
        mode === "register"
          ? await postRegister(trimmed, password)
          : await postLogin(trimmed, password);
      setAuth(result.token, result.name);
      onLogin();
    } catch (err) {
      setError(err instanceof AuthApiError ? err.message : "操作失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-app">
      <div className="login-card">
        <div className="login-brand" aria-hidden>
          BM
        </div>
        <h1>BillMind</h1>
        <p className="login-subtitle">
          {mode === "login" ? "使用账号密码继续" : "创建账号，开始记账"}
        </p>
        <form className="login-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="login-input"
            placeholder="账号名"
            value={name}
            disabled={loading}
            autoComplete="username"
            onChange={(event) => setName(event.target.value)}
            autoFocus
          />
          <input
            type="password"
            className="login-input"
            placeholder="密码"
            value={password}
            disabled={loading}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error ? <p className="login-error">{error}</p> : null}
          <div className="login-actions">
            <button type="submit" className="login-button" disabled={loading}>
              {loading
                ? "请稍候…"
                : mode === "login"
                  ? "登录"
                  : "注册"}
            </button>
            <button
              type="button"
              className="login-button login-button--ghost"
              disabled={loading}
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError(null);
              }}
            >
              {mode === "login" ? "没有账号？去注册" : "已有账号？去登录"}
            </button>
            {onCancel ? (
              <button
                type="button"
                className="login-button login-button--secondary"
                disabled={loading}
                onClick={onCancel}
              >
                继续以访客使用
              </button>
            ) : null}
          </div>
        </form>
      </div>
    </div>
  );
}
