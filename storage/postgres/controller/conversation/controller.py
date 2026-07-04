"""Conversation 异步落库 — 队列 + 单 worker 线程，单事务写入 chat / loop 表。"""

from __future__ import annotations

import asyncio
import logging
import queue
import threading
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agent.loop.harness import LoopRunResult, LoopTurnContext
from server.db.session import Database
from server.model.agent_loop_run import AgentLoopRun
from server.model.agent_loop_step import AgentLoopStep
from server.model.chat_message import ChatMessage
from storage.postgres.controller.conversation import enter as svc
from utils.agent.common.text import extract_reply

logger = logging.getLogger("billmind.storage.postgres.conversation")

_QUEUE_SIZE = 100
PERSIST_RETRY_DELAY_SECONDS = 1.0
_SHUTDOWN_SENTINEL: object = object()
_WORKER_JOIN_TIMEOUT_SECONDS = 120.0


@dataclass
class TurnPersistTask:
    """异步入队元素 — 直传 Harness 上下文对象，不拆字段。"""

    ctx: LoopTurnContext
    run_result: LoopRunResult


class ConversationController:
    """单例:enqueue 异步入队，后台线程单事务落库。"""

    _instance: ConversationController | None = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._tasks: queue.Queue[TurnPersistTask | object] = queue.Queue(maxsize=_QUEUE_SIZE)
        self._thread: threading.Thread | None = None
        self._started = False
        self._shutting_down = False

    @classmethod
    def instance(cls) -> ConversationController:
        """返回进程内单例。"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def start(self) -> None:
        """启动 daemon worker 线程。"""
        if self._started:
            return
        self._thread = threading.Thread(
            target=self._run_worker,
            name="conversation-persist",
            daemon=True,
        )
        self._thread.start()
        self._started = True
        logger.info("ConversationController started (queue=%s)", _QUEUE_SIZE)

    def shutdown(self) -> None:
        """排空队列后停止 worker。"""
        if not self._started:
            return
        self._shutting_down = True
        pending = self._tasks.qsize()
        logger.info("ConversationController shutting down (pending=%s)", pending)
        self._tasks.join()
        self._tasks.put(_SHUTDOWN_SENTINEL)
        if self._thread is not None:
            self._thread.join(timeout=_WORKER_JOIN_TIMEOUT_SECONDS)
            if self._thread.is_alive():
                logger.error("ConversationController worker join timeout")
        self._started = False
        logger.info("ConversationController stopped")

    def enqueue_nowait(self, task: TurnPersistTask) -> None:
        """同步入队（thread-safe），不阻塞 HTTP 响应。"""
        if self._shutting_down:
            logger.warning(
                "conversation enqueue during shutdown turn_id=%s",
                task.ctx.turn_id,
            )
        try:
            self._tasks.put_nowait(task)
        except queue.Full:
            logger.error(
                "conversation queue full turn_id=%s qsize=%s",
                task.ctx.turn_id,
                self._tasks.qsize(),
            )

    def _run_worker(self) -> None:
        """worker 线程入口 — 独立 event loop + 独立 DB 连接池（不可复用主 loop 的 engine）。"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._worker_loop())
        finally:
            loop.close()

    async def _worker_loop(self) -> None:
        """从队列取 task 并落库，直至收到 shutdown sentinel。"""
        main_db = Database.get()
        worker_engine = create_async_engine(
            main_db.database_url,
            pool_size=2,
            max_overflow=2,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        session_factory = async_sessionmaker(worker_engine, expire_on_commit=False)
        try:
            while True:
                task = await asyncio.get_running_loop().run_in_executor(None, self._tasks.get)
                try:
                    if task is _SHUTDOWN_SENTINEL:
                        break
                    assert isinstance(task, TurnPersistTask)
                    await self._persist_until_success(task, session_factory)
                finally:
                    self._tasks.task_done()
        finally:
            await worker_engine.dispose()

    async def _persist_until_success(
        self,
        task: TurnPersistTask,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """落库失败则 error 日志 + 1s 后重试，直至成功。"""
        attempt = 0
        while True:
            attempt += 1
            try:
                async with session_factory() as db:
                    async with db.begin():
                        await self._persist_turn_in_tx(db, task)
                logger.info(
                    "conversation persist ok turn_id=%s thread_id=%s steps=%s attempt=%s",
                    task.ctx.turn_id,
                    task.ctx.thread_id,
                    task.run_result.total_steps,
                    attempt,
                )
                return
            except Exception as exc:
                logger.error(
                    "conversation persist failed turn_id=%s attempt=%s: %s",
                    task.ctx.turn_id,
                    attempt,
                    exc,
                    exc_info=True,
                )
                await asyncio.sleep(PERSIST_RETRY_DELAY_SECONDS)

    @staticmethod
    async def _persist_turn_in_tx(db: AsyncSession, task: TurnPersistTask) -> None:
        """单事务写入 user/assistant message、loop_steps、loop_run。"""
        ctx = task.ctx
        run_result = task.run_result
        conversation_id = ctx.conversation.id
        if conversation_id is None:
            raise RuntimeError("conversation has no id")

        reply = extract_reply(run_result.messages)
        user_message_id: int | None = None

        if ctx.message.strip():
            user_row = await svc.chat_message_service.create(
                db,
                ChatMessage(
                    conversation_id=conversation_id,
                    role="user",
                    content=ctx.message,
                ),
                commit=False,
            )
            user_message_id = user_row.id

        await svc.chat_message_service.create(
            db,
            ChatMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=reply,
            ),
            commit=False,
        )

        for metrics in ctx.pending_steps:
            await svc.agent_loop_step_service.create(
                db,
                AgentLoopStep(
                    account_id=ctx.account_id,
                    conversation_id=conversation_id,
                    thread_id=ctx.thread_id,
                    turn_id=ctx.turn_id,
                    user_chat_message_id=user_message_id,
                    step_count=metrics.step_count,
                    token_usage=metrics.token_usage,
                    node_name=metrics.node_name,
                    tool_name=metrics.tool_name,
                ),
                commit=False,
            )

        await svc.agent_loop_run_service.create(
            db,
            AgentLoopRun(
                account_id=ctx.account_id,
                conversation_id=conversation_id,
                thread_id=ctx.thread_id,
                turn_id=ctx.turn_id,
                user_chat_message_id=user_message_id,
                total_steps=run_result.total_steps,
                total_tokens=run_result.total_tokens,
                stopped_reason=run_result.stopped_reason,
                input_message=ctx.message,
                output_message=reply,
            ),
            commit=False,
        )


conversation_controller = ConversationController.instance()
