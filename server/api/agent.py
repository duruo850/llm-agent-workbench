"""Agent HTTP API — 编排文本 / 文件 / 图片输入，统一交给 Agent.invoke。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from agent import Agent
from common.file_kind import FileKind, detect_file_kind
from server.db.session import get_db
from server.service.account import get_current_account
from server.model.account import Account
from server.model.request.agent import AgentChatRequest
from server.model.response.agent import AgentChatResponse
from utils.client_ip import get_client_ip

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    body: AgentChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> AgentChatResponse:
    try:
        message = body.message.strip()
        extra_blocks: list[str] = []

        if body.file_name is not None and body.file_text is not None:
            kind = detect_file_kind(filename=body.file_name, content=body.file_text)
            if kind != FileKind.CSV:
                raise ValueError(f"暂不支持的文件类型：{body.file_name}")
            extra_blocks.append(
                f"用户上传了 CSV 文件「{body.file_name}」。"
                f"请根据用户意图调用 import_csv_file 导入；"
                f"csv_text 参数使用以下内容：\n{body.file_text}"
            )

        if body.image_data_url:
            if detect_file_kind(data_url=body.image_data_url) != FileKind.IMAGE:
                raise ValueError("image_data_url 格式无效")
            extra_blocks.append(
                f"用户上传了图片「{body.image_data_url}」。"
                f"请根据用户意图调用 recognize_image_file 识别；"
                f"image_data_url 参数使用以下内容：\n{body.image_data_url}"
            )

        if extra_blocks:
            message = "\n\n".join([message, *extra_blocks]) if message else "\n\n".join(extra_blocks)

        client_ip = get_client_ip(request)
        if message:
            message = f"{message}\n\n用户当前 IP: {client_ip}"
        else:
            message = f"用户当前 IP: {client_ip}"

        reply, thread_id = await Agent.invoke(
            message,
            db=db,
            account_id=account.id,
            thread_id=body.thread_id,
        )
        return AgentChatResponse(reply=reply, thread_id=thread_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
