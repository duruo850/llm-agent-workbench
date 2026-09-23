import { useCallback, useEffect, useState } from "react";

import {
  clearAuth,
  ensureAuthSession,
  getAccountName,
  isGuestAccount,
  postGuestLogin,
  setAuth,
  setSessionExpiredHandler,
} from "./api/auth";
import LoginPage from "./components/LoginPage";
import ChatPage from "./components/ChatPage";

type Screen = "boot" | "chat" | "login" | "expired" | "error";

export default function App() {
  const [screen, setScreen] = useState<Screen>("boot");
  const [bootError, setBootError] = useState<string | null>(null);
  const [accountName, setAccountName] = useState(
    () => getAccountName() ?? "",
  );

  const enterChat = useCallback((name: string) => {
    setAccountName(name);
    setScreen("chat");
    setBootError(null);
  }, []);

  const bootstrap = useCallback(async () => {
    setScreen("boot");
    setBootError(null);
    try {
      const session = await ensureAuthSession();
      enterChat(session.name);
    } catch (err) {
      setBootError(err instanceof Error ? err.message : "初始化会话失败");
      setScreen("error");
    }
  }, [enterChat]);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    setSessionExpiredHandler(() => {
      setScreen("expired");
    });
    return () => setSessionExpiredHandler(null);
  }, []);

  const handleLogout = useCallback(() => {
    clearAuth();
    void bootstrap();
  }, [bootstrap]);

  const handleNamedLogin = useCallback(() => {
    enterChat(getAccountName() ?? "");
  }, [enterChat]);

  const handleGuestContinue = useCallback(async () => {
    setScreen("boot");
    try {
      clearAuth();
      const session = await postGuestLogin();
      setAuth(session.token, session.name);
      enterChat(session.name);
    } catch (err) {
      setBootError(err instanceof Error ? err.message : "游客登录失败");
      setScreen("error");
    }
  }, [enterChat]);

  if (screen === "expired") {
    return (
      <div className="login-app">
        <div className="login-card">
          <div className="login-brand" aria-hidden>
            BM
          </div>
          <h1>BillMind</h1>
          <p className="login-subtitle">会话已超时，选择一种方式继续记账</p>
          <span className="login-hint">登录状态已失效</span>
          <div className="login-actions">
            <button
              type="button"
              className="login-button"
              onClick={() => void handleGuestContinue()}
            >
              游客登录
            </button>
            <button
              type="button"
              className="login-button login-button--secondary"
              onClick={() => setScreen("login")}
            >
              账号密码登录
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (screen === "login") {
    return (
      <LoginPage
        onLogin={handleNamedLogin}
        onCancel={() => void handleGuestContinue()}
      />
    );
  }

  if (screen === "error") {
    return (
      <div className="login-app">
        <div className="login-card">
          <div className="login-brand" aria-hidden>
            BM
          </div>
          <h1>BillMind</h1>
          <p className="login-error" style={{ textAlign: "center", marginTop: "1rem" }}>
            {bootError}
          </p>
          <div className="login-actions" style={{ marginTop: "1.25rem" }}>
            <button
              type="button"
              className="login-button"
              onClick={() => void bootstrap()}
            >
              重试
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (screen === "boot") {
    return (
      <div className="login-app">
        <div className="login-card">
          <div className="login-brand" aria-hidden>
            BM
          </div>
          <h1>BillMind</h1>
          <p className="login-subtitle">正在准备会话…</p>
        </div>
      </div>
    );
  }

  const guest = isGuestAccount(accountName);

  return (
    <ChatPage
      accountName={guest ? "访客" : accountName}
      isGuest={guest}
      onLogout={handleLogout}
      onLoginRequest={() => setScreen("login")}
    />
  );
}
