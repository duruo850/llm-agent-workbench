import { useCallback, useEffect, useState } from "react";

import {
  clearAuth,
  ensureAuthSession,
  getAccountName,
  isGuestAccount,
} from "./api/auth";
import LoginPage from "./components/LoginPage";
import ChatPage from "./components/ChatPage";

export default function App() {
  const [ready, setReady] = useState(false);
  const [bootError, setBootError] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [accountName, setAccountName] = useState(
    () => getAccountName() ?? "",
  );

  const bootstrap = useCallback(async () => {
    setBootError(null);
    try {
      const session = await ensureAuthSession();
      setAccountName(session.name);
      setReady(true);
      setShowLogin(false);
    } catch (err) {
      setReady(false);
      setBootError(err instanceof Error ? err.message : "初始化会话失败");
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const handleLogout = useCallback(() => {
    clearAuth();
    setReady(false);
    void bootstrap();
  }, [bootstrap]);

  const handleNamedLogin = useCallback(() => {
    setAccountName(getAccountName() ?? "");
    setShowLogin(false);
    setReady(true);
  }, []);

  if (showLogin) {
    return (
      <LoginPage
        onLogin={handleNamedLogin}
        onCancel={() => setShowLogin(false)}
      />
    );
  }

  if (bootError) {
    return (
      <div className="login-app">
        <div className="login-card">
          <h1>BillMind</h1>
          <p className="login-error">{bootError}</p>
          <button type="button" className="login-button" onClick={() => void bootstrap()}>
            重试
          </button>
        </div>
      </div>
    );
  }

  if (!ready) {
    return (
      <div className="login-app">
        <div className="login-card">
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
      onLoginRequest={() => setShowLogin(true)}
    />
  );
}
