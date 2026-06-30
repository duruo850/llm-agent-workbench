import { useCallback, useEffect, useState } from "react";

import { AgentApiError, postAgentChat } from "../api/agent";
import { getGeoMe } from "../api/geo";
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
  const [geoSubtitle, setGeoSubtitle] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void getGeoMe().then((geo) => {
      if (cancelled || !geo) {
        return;
      }
      const city = geo.city || geo.province;
      if (city && geo.weather) {
        const temp = geo.temperature ? ` ${geo.temperature}°C` : "";
        setGeoSubtitle(`${city} · ${geo.weather}${temp}`);
      } else if (city) {
        setGeoSubtitle(city);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setThreadId(null);
  }, []);

  const handleSend = useCallback(
    async (
      text: string,
      attachment?: {
        imageDataUrl?: string | null;
        fileName?: string | null;
        fileText?: string | null;
      },
    ) => {
      const trimmed = text.trim();
      const imageDataUrl = attachment?.imageDataUrl ?? null;
      const fileName = attachment?.fileName ?? null;
      const fileText = attachment?.fileText ?? null;
      if (!trimmed && !imageDataUrl && !fileName) {
        return;
      }

      const userMessage: ChatMessage = {
        id: createId(),
        role: "user",
        content:
          trimmed ||
          (fileName ? `（上传了文件 ${fileName}）` : "（上传了支付截图）"),
        imageDataUrl: imageDataUrl ?? undefined,
      };

      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);

      try {
        const { reply, thread_id } = await postAgentChat({
          message: trimmed,
          imageDataUrl,
          fileName,
          fileText,
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
            <p>
              {accountName} · 记账 · 查账 · 理财知识
              {geoSubtitle ? (
                <>
                  <br />
                  <span className="chat-geo-subtitle">{geoSubtitle}</span>
                </>
              ) : null}
            </p>
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
