import { useCallback, useState } from "react";

import { clearAuth, getAccountName, getToken } from "./api/auth";
import LoginPage from "./components/LoginPage";
import ChatPage from "./components/ChatPage";

export default function App() {
  const [authed, setAuthed] = useState(() => Boolean(getToken()));

  const handleLogout = useCallback(() => {
    clearAuth();
    setAuthed(false);
  }, []);

  if (!authed || !getToken()) {
    return <LoginPage onLogin={() => setAuthed(true)} />;
  }

  return (
    <ChatPage
      accountName={getAccountName() ?? "未知账号"}
      onLogout={handleLogout}
    />
  );
}
