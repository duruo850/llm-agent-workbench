import { authFetch } from "./client";

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
  fileName?: string | null;
  fileText?: string | null;
  threadId?: string | null;
}): Promise<AgentChatResponse> {
  let response: Response;
  try {
    response = await authFetch("/agent/chat", {
      method: "POST",
      body: JSON.stringify({
        message: params.message,
        image_data_url: params.imageDataUrl ?? null,
        file_name: params.fileName ?? null,
        file_text: params.fileText ?? null,
        thread_id: params.threadId ?? null,
      }),
    });
  } catch (error) {
    if (error instanceof Error && error.name === "ApiError") {
      throw new AgentApiError(error.message);
    }
    throw new AgentApiError("无法连接后端 API。请先运行：python server/main.py");
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
