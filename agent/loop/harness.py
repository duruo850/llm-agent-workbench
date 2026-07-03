"""Loop Harness 核心 — 基于 LangGraph ``astream_events`` 旁路监控 ReAct 循环。

为什么不直接 ``ainvoke``?

- ``ainvoke`` 只返回最终结果，无法逐步采集 token / 工具名 / 步序
- ``astream_events(version="v2")`` 在**不改变 graph 拓扑**的前提下，逐步抛出：

  - ``on_chat_model_end``: LLM 完成一次推理
  - ``on_tool_end``：工具执行完毕
  - ``on_chain_end``(name=LangGraph)：整图结束，可拿到最终 ``messages``

适用前提：传入的 ``graph`` 必须是编译后的 LangGraph(具备 ``astream_events``)。
M2 ``agent/agent/`` 的 for 循环目前不走本 Harness,可复用 ``policy`` / ``prompt``。

一次 ``run()`` 的生命周期::

    1. 订阅事件流
    2. 每步 → 计数、抽 token、跟踪同工具 streak
    3. 每步 → 调用 hooks.on_step(落库)
    4. streak 达上限 / should_stop / GraphRecursionError → 返回 messages
    5. 正常结束 → 从 on_chain_end 取 messages,由调用方 extract_reply
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langgraph.errors import GraphRecursionError
from sqlalchemy.ext.asyncio import AsyncSession

from utils.agent.common.result import is_no_tool_result
from utils.agent.common.text import extract_reply
from utils.agent.common.token import extract_token_usage
from server.model.conversation import Conversation
from server.model.chat_message import ChatMessage
from agent.loop.hooks import LoopHooks, LoopStepMetrics
from agent.loop.policy import (
    RECURSION_LIMIT,
    SAME_TOOL_GIVE_UP_REPLY,
    SAME_TOOL_NO_RESULT_LIMIT,
)
from server.model.agent_loop_run import AgentLoopRun
from server.model.agent_loop_step import AgentLoopStep
from langchain_core.messages import AIMessage
from storage.postgres.service.agent_loop_run import agent_loop_run_service
from storage.postgres.service.agent_loop_step import agent_loop_step_service
from storage.postgres.service.conversation import conversation_service
from storage.postgres.service.chat_message import chat_message_service

logger = logging.getLogger("billmind.loop.harness")

# LangGraph 顶层图结束事件中的 name 字段（用于取最终 state.messages）
_GRAPH_END_NAME = "LangGraph"

# 计入 step_count 的事件类型：一次 LLM 或一次工具各算一步
_STEP_EVENTS = frozenset({"on_chat_model_end", "on_tool_end"})


@dataclass
class LoopTurnContext:
    """单次 turn 编排上下文 — ``prepare_turn`` 产出，``complete_turn`` 消费。"""

    turn_id: str # 本轮 turn ID
    thread_id: str # 会话线程 ID
    conversation: Conversation # 会话
    account_id: int # 账户 ID
    message: str # 用户消息 
    config: dict[str, Any] # 配置
    graph_input: dict[str, Any] # 图输入
    hooks: LoopHooks # 回调
    pending_steps: list[LoopStepMetrics] = field(default_factory=list) # 步骤列表


@dataclass
class LoopRunResult:
    """Harness.run 的返回值。"""
    messages: list  # LangGraph 最终 messages；被强制中断时可能不完整
    turn_id: str  # 单次 /agent/chat 的 UUID，关联 agent_loop_steps 一组 step 行
    total_steps: int  # 本轮 invoke 内从 1 递增
    total_tokens: int  # 各 LLM 步 token 合计
    stopped_reason: str | None = None  # 正常结束为 None


@dataclass
class _LoopRunState:
    """``run()`` 循环内的可变累积状态 — 由 ``run_event`` 逐步更新。"""

    step_count: int = 0 # 步骤计数
    total_tokens: int = 0 # 总token数
    messages: list = field(default_factory=list) # 消息列表
    stopped_reason: str | None = None # 停止原因
    same_tool_name: str | None = None # 同工具名称
    same_tool_streak: int = 0 # 同工具连续次数




class LoopHarness:
    """包装 LangGraph ``astream_events``，采集步级指标并执行循环策略。"""

    @staticmethod
    async def prepare_turn(
        db: AsyncSession,
        message: str,
        *,
        account_id: int,
        thread_id: str | None = None,
        debug: bool = False,
    ) -> LoopTurnContext:
        """turn 前置：ensure conversation、组装 config / hooks（不落库）。"""
        logger.info("invoke_v2 input: %s", message)

        # 会话线程 ID
        effective_thread_id = thread_id or str(uuid4())
        # 本轮 turn ID
        turn_id = str(uuid4())
        # 会话标题
        title = message.strip()[:200] if message.strip() else None

        # 确保会话存在
        conversation = await conversation_service.ensure(
            db,
            account_id,
            effective_thread_id,
            title,
        )
        if conversation.id is None:
            raise RuntimeError("conversation has no id")

        # 步骤列表
        pending_steps: list[LoopStepMetrics] = []

        # 步骤回调
        async def on_step(metrics: LoopStepMetrics) -> None:
            pending_steps.append(metrics)
            logger.info(
                "loop step turn_id=%s step=%s tokens=%s node=%s tool=%s",
                turn_id,
                metrics.step_count,
                metrics.token_usage,
                metrics.node_name,
                metrics.tool_name,
            )

        # 配置
        config = {
            "configurable": {
                "thread_id": effective_thread_id,
                "debug": debug,
                "account_id": account_id,
            },
            "recursion_limit": RECURSION_LIMIT, # 递归限制
        }

        return LoopTurnContext(
            turn_id=turn_id,
            thread_id=effective_thread_id,
            conversation=conversation,
            account_id=account_id,
            message=message,
            config=config,
            graph_input={"messages": [HumanMessage(content=message)]},
            hooks=LoopHooks(on_step=on_step),
            pending_steps=pending_steps,
        )

    @staticmethod
    async def complete_turn(
        db: AsyncSession,
        ctx: LoopTurnContext,
        run_result: LoopRunResult,
    ) -> tuple[str, str, str]:
        """
        完成turn轮次:创建 chat_messages / loop_run / loop_steps, 返回 (reply, thread_id, turn_id)。

        Args:
            db: 数据库会话
            ctx: turn 上下文
            run_result: turn 运行结果

        Returns:
            tuple[str, str, str]: 回复, 会话线程 ID, 本轮 turn ID
        """
        # 提取回复
        reply = extract_reply(run_result.messages)

        # 用户消息 ID
        user_message_id: int | None = None
        # 写入用户消息(一次turn轮次对应一个用户消息)
        if ctx.message.strip():
            user_row = await chat_message_service.create(
                db,
                ChatMessage(conversation_id=ctx.conversation.id, role="user", content=ctx.message),
            )
            user_message_id = user_row.id
            
        # 写入agent 反馈消息(一次turn轮次对应一个反馈消息)
        await chat_message_service.create(
            db,
            ChatMessage(conversation_id=ctx.conversation.id, role="assistant", content=reply),
        )
        
        # 写入agent loop 步骤记录(每个步骤对应一个步骤记录)
        for metrics in ctx.pending_steps:
            await agent_loop_step_service.create(
                db,
                AgentLoopStep(
                    account_id=ctx.account_id,
                    conversation_id=ctx.conversation.id,
                    thread_id=ctx.thread_id,
                    turn_id=ctx.turn_id,
                    user_chat_message_id=user_message_id,
                    step_count=metrics.step_count,
                    token_usage=metrics.token_usage,
                    node_name=metrics.node_name,
                    tool_name=metrics.tool_name,
                ),
            )

        # 写入agent loop 运行记录(一次turn轮次对应一个运行记录)
        await agent_loop_run_service.create(
            db,
            AgentLoopRun(
                account_id=ctx.account_id,
                conversation_id=ctx.conversation.id,
                thread_id=ctx.thread_id,
                turn_id=ctx.turn_id,
                user_chat_message_id=user_message_id,
                total_steps=run_result.total_steps,
                total_tokens=run_result.total_tokens,
                stopped_reason=run_result.stopped_reason,
                input_message=ctx.message,
                output_message=reply,
            ),
        )

        logger.info(
            "invoke_v2 output turn_id=%s steps=%s tokens=%s reason=%s reply=%s",
            ctx.turn_id,
            run_result.total_steps,
            run_result.total_tokens,
            run_result.stopped_reason,
            reply,
        )
        return reply, ctx.thread_id, ctx.turn_id

    @staticmethod
    async def invoke_turn_event(
        event: dict[str, Any],
        *,
        state: _LoopRunState,
        hooks: LoopHooks,
        should_stop: Callable[[LoopStepMetrics], bool],
    ) -> bool:
        """处理单个 ``astream_events`` 事件。

        Returns:
            True 表示应中断 ``run()`` 的事件循环。
        """
        event_kind = event.get("event")

        # 图跑完：抓取最终 messages 供 extract_reply 使用
        if event_kind == "on_chain_end" and event.get("name") == _GRAPH_END_NAME:
            output = event.get("data", {}).get("output") or {}
            if isinstance(output, dict) and output.get("messages"):
                state.messages = output["messages"]
            return False

        # 非 LLM / 工具步的事件（如 on_chain_start）不计入 step_count
        if event_kind not in _STEP_EVENTS:
            return False

        state.step_count += 1
        node_name = event.get("name")
        tool_name: str | None = None
        token_usage = 0

        if event_kind == "on_chat_model_end":
            token_usage = extract_token_usage(event)
            state.total_tokens += token_usage
        elif event_kind == "on_tool_end":
            tool_name = node_name
            output = event.get("data", {}).get("output")
            if is_no_tool_result(output):
                if tool_name == state.same_tool_name:
                    state.same_tool_streak += 1
                else:
                    state.same_tool_name = tool_name
                    state.same_tool_streak = 1
            else:
                state.same_tool_name = None
                state.same_tool_streak = 0

        # 创建步骤指标
        metrics = LoopStepMetrics(
            step_count=state.step_count,
            token_usage=token_usage,
            node_name=node_name,
            tool_name=tool_name,
        )

        if hooks.on_step is not None:
            await hooks.on_step(metrics)

        if state.same_tool_streak >= SAME_TOOL_NO_RESULT_LIMIT:
            state.stopped_reason = "same_tool_no_result"
            state.messages = [AIMessage(content=SAME_TOOL_GIVE_UP_REPLY)]
            return True

        if should_stop(metrics):
            state.stopped_reason = "recursion_limit"
            state.messages = [AIMessage(content=SAME_TOOL_GIVE_UP_REPLY)]
            return True

        return False

    @staticmethod
    async def invoke_turn(
        graph: Any,
        graph_input: dict[str, Any],
        config: dict[str, Any],
        *,
        turn_id: str,
        hooks: LoopHooks | None = None,
    ) -> LoopRunResult:
        """执行图并监控循环。

        Args:
            graph: 编译后的 LangGraph，需支持 ``astream_events(..., version="v2")``
            graph_input: 通常为 ``{"messages": [HumanMessage(...)]}``
            config: 含 ``configurable.thread_id``、``recursion_limit`` 等
            turn_id: 本轮 invoke 唯一 ID，写入每步落库记录
            hooks: 可选的 on_step / should_stop 扩展
        """
        effective_hooks = hooks or LoopHooks()
        state = _LoopRunState()

        try:
            # 遍历事件流
            # astream_events 在**不改变 graph 拓扑**的前提下，逐步抛出：
            # - ``on_chat_model_end``: LLM 完成一次推理
            # - ``on_tool_end``：工具执行完毕
            # - ``on_chain_end``(name=LangGraph)：整图结束，可拿到最终 ``messages``
            async for event in graph.astream_events(
                graph_input,
                config=config,
                version="v2",
            ):
                # 处理单个事件，返回 True 表示应中断 run() 的事件循环
                if await LoopHarness.invoke_turn_event(
                    event,
                    state=state,
                    hooks=effective_hooks,
                    should_stop=effective_hooks.should_stop,
                ):
                    break

        # config recursion_limit 触顶时 LangGraph 抛错；捕获后友好返回，避免 HTTP 500
        except GraphRecursionError:
            # config recursion_limit 触顶时 LangGraph 抛错；捕获后友好返回，避免 HTTP 500
            logger.warning("GraphRecursionError caught for turn_id=%s", turn_id)
            state.stopped_reason = "graph_recursion_error"
            state.messages = [AIMessage(content=SAME_TOOL_GIVE_UP_REPLY)]

        return LoopRunResult(
            messages=state.messages,
            turn_id=turn_id,
            total_steps=state.step_count,
            total_tokens=state.total_tokens,
            stopped_reason=state.stopped_reason,
        )
