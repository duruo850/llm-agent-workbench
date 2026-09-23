import { useState, type FormEvent } from "react";

import { AuthApiError, postLogin, setAuth } from "../api/auth";

interface LoginPageProps {
  onLogin: () => void;
  onCancel?: () => void;
}

export default function LoginPage({ onLogin, onCancel }: LoginPageProps) {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("请输入账号名");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await postLogin(trimmed);
      setAuth(result.token, result.name);
      onLogin();
    } catch (err) {
      setError(err instanceof AuthApiError ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-app">
      <div className="login-card">
        <h1>BillMind</h1>
        <p className="login-subtitle">输入账号名即可登录</p>
        <form className="login-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="login-input"
            placeholder="账号名"
            value={name}
            disabled={loading}
            onChange={(event) => setName(event.target.value)}
            autoFocus
          />
          {error ? <p className="login-error">{error}</p> : null}
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? "登录中…" : "登录"}
          </button>
          {onCancel ? (
            <button
              type="button"
              className="login-button"
              disabled={loading}
              onClick={onCancel}
              style={{ marginTop: "0.5rem", opacity: 0.85 }}
            >
              继续以访客使用
            </button>
          ) : null}
        </form>
      </div>
    </div>
  );
}
