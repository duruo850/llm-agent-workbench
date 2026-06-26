import { useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";

interface ChatInputProps {
  disabled?: boolean;
  onSend: (text: string, imageDataUrl?: string | null) => void;
}

export default function ChatInput({ disabled = false, onSend }: ChatInputProps) {
  const [text, setText] = useState("");
  const [imageDataUrl, setImageDataUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setImageDataUrl(reader.result);
      }
    };
    reader.readAsDataURL(file);
    event.target.value = "";
  };

  const clearImage = () => {
    setImageDataUrl(null);
  };

  const submit = () => {
    if (disabled) {
      return;
    }
    if (!text.trim() && !imageDataUrl) {
      return;
    }
    onSend(text, imageDataUrl);
    setText("");
    setImageDataUrl(null);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <div className="chat-input">
      {imageDataUrl && (
        <div className="chat-input-preview">
          <img src={imageDataUrl} alt="待发送截图预览" />
          <button type="button" className="chat-input-remove" onClick={clearImage}>
            移除
          </button>
        </div>
      )}
      <div className="chat-input-bar">
        <button
          type="button"
          className="chat-input-attach"
          disabled={disabled}
          onClick={() => fileInputRef.current?.click()}
          aria-label="上传图片"
        >
          📎
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={handleImageChange}
        />
        <textarea
          className="chat-input-text"
          rows={1}
          placeholder="输入记账或查账内容，Enter 发送，Shift+Enter 换行"
          value={text}
          disabled={disabled}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          type="button"
          className="chat-input-send"
          disabled={disabled || (!text.trim() && !imageDataUrl)}
          onClick={submit}
        >
          发送
        </button>
      </div>
    </div>
  );
}
