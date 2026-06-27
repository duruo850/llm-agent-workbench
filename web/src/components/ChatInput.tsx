import { useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";

type AttachmentKind = "image" | "csv" | null;

interface Attachment {
  kind: AttachmentKind;
  label: string;
  imageDataUrl?: string;
  fileName?: string;
  fileText?: string;
}

interface ChatInputProps {
  disabled?: boolean;
  onSend: (
    text: string,
    attachment?: {
      imageDataUrl?: string | null;
      fileName?: string | null;
      fileText?: string | null;
    },
  ) => void;
}

function detectAttachmentKind(file: File): AttachmentKind {
  const name = file.name.toLowerCase();
  if (name.endsWith(".csv") || file.type === "text/csv") {
    return "csv";
  }
  if (file.type.startsWith("image/")) {
    return "image";
  }
  return null;
}

export default function ChatInput({ disabled = false, onSend }: ChatInputProps) {
  const [text, setText] = useState("");
  const [attachment, setAttachment] = useState<Attachment | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const kind = detectAttachmentKind(file);
    if (kind === "csv") {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === "string") {
          setAttachment({
            kind: "csv",
            label: file.name,
            fileName: file.name,
            fileText: reader.result,
          });
        }
      };
      reader.readAsText(file);
    } else if (kind === "image") {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === "string") {
          setAttachment({
            kind: "image",
            label: file.name,
            imageDataUrl: reader.result,
          });
        }
      };
      reader.readAsDataURL(file);
    }
    event.target.value = "";
  };

  const clearAttachment = () => {
    setAttachment(null);
  };

  const submit = () => {
    if (disabled) {
      return;
    }
    if (!text.trim() && !attachment) {
      return;
    }
    onSend(text, {
      imageDataUrl: attachment?.imageDataUrl ?? null,
      fileName: attachment?.fileName ?? null,
      fileText: attachment?.fileText ?? null,
    });
    setText("");
    setAttachment(null);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <div className="chat-input">
      {attachment && (
        <div className="chat-input-preview">
          {attachment.kind === "image" && attachment.imageDataUrl ? (
            <img src={attachment.imageDataUrl} alt="待发送截图预览" />
          ) : (
            <span className="chat-input-file-label">📄 {attachment.label}</span>
          )}
          <button type="button" className="chat-input-remove" onClick={clearAttachment}>
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
          aria-label="上传文件"
        >
          📎
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.csv,text/csv"
          hidden
          onChange={handleFileChange}
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
          disabled={disabled || (!text.trim() && !attachment)}
          onClick={submit}
        >
          发送
        </button>
      </div>
    </div>
  );
}
