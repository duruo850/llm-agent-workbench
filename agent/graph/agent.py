"""M4 LangGraph Agent — ``create_react_agent`` + MCP tools + checkpointer。"""

from __future__ import annotations

import logging
from uuid import uuid4

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.agent import Agent as ClassicAgent
import storage as storage
from agent.common.skill_category import SKILL_CATEGORY_IDS
from agent.common.skill_registry import skill_registry
from agent.graph.graph import build_agent_graph
from utils.agent.common.text import extract_reply, extract_tool_names
from agent.loop.harness import LoopHarness
from langgraph.graph.state import CompiledStateGraph
from agent.intent import init as init_intent, intent_manager
from common.env import is_intent_enabled

MAX_TOOL_ROUNDS = 5

logger = logging.getLogger("billmind.graph.agent")

_COMPILED_GRAPH: CompiledStateGraph | None = None  # 主图
_CATEGORY_GRAPHS: dict[str, CompiledStateGraph] = {}  # 分类图
_RECURSION_LIMIT: int = MAX_TOOL_ROUNDS * 2 + 1

# reply, thread_id, tool_names
InvokeResult = tuple[str, str, list[str]]


def _compile_category_graphs(checkpointer) -> dict[str, CompiledStateGraph]:
    """按 skill category 预编译子图(general_chat 无子图）。"""
    graphs: dict[str, CompiledStateGraph] = {}
    for category_id in (*SKILL_CATEGORY_IDS, "fallback_all"):
        if category_id == "general_chat":
            continue
        if category_id == "fallback_all":
            assert _COMPILED_GRAPH is not None
            graphs[category_id] = _COMPILED_GRAPH
            continue
        tools = intent_manager.resolve_tools(category_id)  # type: ignore[arg-type]
        graph, _ = build_agent_graph(tools, checkpointer, max_tool_rounds=MAX_TOOL_ROUNDS)
        graphs[category_id] = graph
    return graphs


class Agent:
    """LangGraph 版 Agent — init / invoke / invoke_v2 / parse_image（视觉链委托 M2）。"""

    @classmethod
    def init(cls) -> None:
        """skills + MCP tools → ``create_react_agent``。"""
        global _COMPILED_GRAPH, _CATEGORY_GRAPHS, _RECURSION_LIMIT
        
        # 加载技能和工具
        tools = skill_registry.all_tools()
        if is_intent_enabled():
            init_intent()

        # 检查点
        checkpointer = storage.working.get_checkpointer()
        
        # 预编译主图
        _COMPILED_GRAPH, _RECURSION_LIMIT = build_agent_graph(
            tools,
            checkpointer,
            max_tool_rounds=MAX_TOOL_ROUNDS,
        )

        # 预编译分类图（仅意图识别开启时）
        if is_intent_enabled():
            _CATEGORY_GRAPHS = _compile_category_graphs(checkpointer)
        else:
            _CATEGORY_GRAPHS = {}

        skill_names = ", ".join(skill_registry.all_tool_names())
        logger.info("graph agent skills loaded: skill_tools: %s", skill_names)

    @classmethod
    async def invoke(
        cls,
        message: str,
        *,
        account_id: int,
        db: AsyncSession | None = None,  # noqa: ARG003
        thread_id: str | None = None,
        debug: bool = False,
    ) -> InvokeResult:
        """处理用户消息，返回 (reply, thread_id, tool_names)。历史由 checkpointer 按 thread_id 累积。"""
        del db
        logger.info("input: %s", message)

        if _COMPILED_GRAPH is None:
            raise RuntimeError("Graph Agent 未初始化，请先调用 Agent.init()")

        effective_thread_id = thread_id or str(uuid4())
        config = {
            "configurable": {
                "thread_id": effective_thread_id,
                "debug": debug,
                "account_id": account_id,
            },
            "recursion_limit": _RECURSION_LIMIT,
        }

        result = await _COMPILED_GRAPH.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config,
        )
        messages = result["messages"]
        reply = extract_reply(messages)
        tool_names = extract_tool_names(messages)
        logger.info("output: %s tools=%s", reply, tool_names)
        return reply, effective_thread_id, tool_names

    @classmethod
    async def invoke_v2(
        cls,
        message: str,
        *,
        account_id: int,
        db: AsyncSession,
        thread_id: str | None = None,
        debug: bool = False,
    ) -> InvokeResult:
        """M10 Loop Harness 路径 — M12 先分类再选子图或直调 general_chat。"""
        if _COMPILED_GRAPH is None:
            raise RuntimeError("Graph Agent 未初始化，请先调用 Agent.init()")

        graph = _COMPILED_GRAPH
        # 意图分类开启时
        if is_intent_enabled():
            # 意图分类
            intent = intent_manager.classify(message)
            logger.info(
                "intent category=%s method=%s confidence=%.3f",
                intent.scene,
                intent.method,
                intent.confidence,
            )
            # 通用聊天分类
            if intent.scene == "general_chat":
                tool = skill_registry.get_tool("reply_general_chat")
                if tool is None:
                    raise RuntimeError("reply_general_chat tool 未注册")
                reply = await tool.ainvoke({}, config=ctx.config)
                effective_thread_id = ctx.config.get("configurable", {}).get("thread_id", str(uuid4()))
                logger.info("general_chat direct reply: %s", reply[:80])
                return str(reply), str(effective_thread_id), ["reply_general_chat"]

            # 选择子图
            graph = _CATEGORY_GRAPHS.get(intent.scene, _COMPILED_GRAPH)
        else:
            # 意图分类未开启时，直接使用主图
            graph = _COMPILED_GRAPH

        # 准备上下文
        ctx = await LoopHarness.prepare_turn(
            db,
            message,
            account_id=account_id,
            thread_id=thread_id,
            debug=debug,
        )
        run_result = await LoopHarness.invoke_turn(
            graph,
            ctx.graph_input,
            ctx.config,
            turn_id=ctx.turn_id,
            hooks=ctx.hooks,
        )

        # 完成回合
        reply, thread_id, _turn_id = await LoopHarness.complete_turn(db, ctx, run_result)
        tool_names = extract_tool_names(run_result.messages)
        return reply, thread_id, tool_names

    @classmethod
    async def parse_image(cls, image_data_url: str) -> str:
        """视觉链与 M2 相同，委托 ``agent.agent.Agent``。"""
        return await ClassicAgent.parse_image(image_data_url)
