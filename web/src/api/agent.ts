const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export interface AgentChatResponse {
  reply: string;
  thread_id: string;
}

export class AgentApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AgentApiError";
  }
}

export async function postAgentChat(params: {
  message: string;
  imageDataUrl?: string | null;
  threadId?: string | null;
}): Promise<AgentChatResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/agent/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: params.message,
        image_data_url: params.imageDataUrl ?? null,
        thread_id: params.threadId ?? null,
      }),
    });
  } catch {
    throw new AgentApiError(
      `无法连接后端 API（${API_BASE}）。请先运行：python server/main.py`,
    );
  }

  if (!response.ok) {
    let detail = `请求失败 (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore parse errors
    }
    throw new AgentApiError(detail);
  }

  return (await response.json()) as AgentChatResponse;
}
