import type { ChatMessage } from "../types/chat";

interface MessageListProps {
  messages: ChatMessage[];
  loading: boolean;
}

export default function MessageList({ messages, loading }: MessageListProps) {
  return (
    <div className="message-list">
      {messages.length === 0 && !loading && (
        <div className="message-empty">
          <p>试试：</p>
          <ul>
            <li>刚才 Starbucks 花了 38，算餐饮</li>
            <li>查一下本月餐饮花了多少</li>
            <li>或上传支付截图自动识别</li>
          </ul>
        </div>
      )}
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message-row message-row--${message.role}${
            message.isError ? " message-row--error" : ""
          }`}
        >
          <div className="message-bubble">
            {message.imageDataUrl && (
              <img
                className="message-image"
                src={message.imageDataUrl}
                alt="用户上传的截图"
              />
            )}
            <p>{message.content}</p>
          </div>
        </div>
      ))}
      {loading && (
        <div className="message-row message-row--assistant">
          <div className="message-bubble message-bubble--loading">
            <p>思考中…</p>
          </div>
        </div>
      )}
    </div>
  );
}
