import { useCallback, useState } from "react";

import { AgentApiError, postAgentChat } from "../api/agent";
import type { ChatMessage } from "../types/chat";
import ChatInput from "./ChatInput";
import MessageList from "./MessageList";

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

interface ChatPageProps {
  accountName: string;
  onLogout: () => void;
}

export default function ChatPage({ accountName, onLogout }: ChatPageProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setThreadId(null);
  }, []);

  const handleSend = useCallback(
    async (text: string, imageDataUrl?: string | null) => {
      const trimmed = text.trim();
      if (!trimmed && !imageDataUrl) {
        return;
      }

      const userMessage: ChatMessage = {
        id: createId(),
        role: "user",
        content: trimmed || "（上传了支付截图）",
        imageDataUrl: imageDataUrl ?? undefined,
      };

      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);

      try {
        const { reply, thread_id } = await postAgentChat({
          message: trimmed,
          imageDataUrl,
          threadId,
        });
        setThreadId(thread_id);
        setMessages((prev) => [
          ...prev,
          { id: createId(), role: "assistant", content: reply },
        ]);
      } catch (error) {
        const detail =
          error instanceof AgentApiError
            ? error.message
            : error instanceof Error
              ? error.message
              : "未知错误";
        setMessages((prev) => [
          ...prev,
          {
            id: createId(),
            role: "assistant",
            content: detail,
            isError: true,
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [threadId],
  );

  return (
    <div className="chat-app">
      <header className="chat-header">
        <div className="chat-header-row">
          <div>
            <h1>BillMind</h1>
            <p>{accountName} · 记账 · 查账</p>
          </div>
          <div className="chat-header-actions">
            <button
              type="button"
              className="chat-new-button"
              disabled={loading}
              onClick={handleNewChat}
            >
              新对话
            </button>
            <button
              type="button"
              className="chat-logout-button"
              disabled={loading}
              onClick={onLogout}
            >
              退出
            </button>
          </div>
        </div>
      </header>
      <main className="chat-main">
        <MessageList messages={messages} loading={loading} />
      </main>
      <footer className="chat-footer">
        <ChatInput disabled={loading} onSend={handleSend} />
      </footer>
    </div>
  );
}
