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


def _log_fn(name: str, fmt: str, *args: object) -> None:
    """统一函数日志 — 前缀为 ``Class.method()``。"""
    logger.info("%s " + fmt, name, *args)


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
        _log_fn("ConversationController.__init__()", "create queue maxsize=%s", _QUEUE_SIZE)
        self._tasks: queue.Queue[TurnPersistTask | object] = queue.Queue(maxsize=_QUEUE_SIZE)
        self._thread: threading.Thread | None = None
        self._started = False
        self._shutting_down = False

    @classmethod
    def instance(cls) -> ConversationController:
        """返回进程内单例。"""
        _log_fn("ConversationController.instance()", "enter")
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def start(self) -> None:
        """启动 daemon worker 线程。"""
        _log_fn("ConversationController.start()", "enter started=%s", self._started)
        if self._started:
            _log_fn("ConversationController.start()", "skip already started")
            return
        self._thread = threading.Thread(
            target=self._run_worker,
            name="conversation-persist",
            daemon=True,
        )
        self._thread.start()
        self._started = True
        _log_fn("ConversationController.start()", "worker thread started")

    def shutdown(self) -> None:
        """排空队列后停止 worker。"""
        _log_fn("ConversationController.shutdown()", "enter started=%s", self._started)
        if not self._started:
            _log_fn("ConversationController.shutdown()", "skip not started")
            return
        self._shutting_down = True
        pending = self._tasks.qsize()
        _log_fn(
            "ConversationController.shutdown()",
            "draining queue pending=%s",
            pending,
        )
        self._tasks.join()
        self._tasks.put(_SHUTDOWN_SENTINEL)
        if self._thread is not None:
            self._thread.join(timeout=_WORKER_JOIN_TIMEOUT_SECONDS)
            if self._thread.is_alive():
                logger.error("ConversationController.shutdown() worker join timeout")
        self._started = False
        _log_fn("ConversationController.shutdown()", "done")

    async def enqueue(self, task: TurnPersistTask) -> None:
        """异步入队，不阻塞调用方。"""
        _log_fn(
            "ConversationController.enqueue()",
            "turn_id=%s thread_id=%s steps=%s shutting_down=%s",
            task.ctx.turn_id,
            task.ctx.thread_id,
            task.run_result.total_steps,
            self._shutting_down,
        )
        if self._shutting_down:
            logger.warning(
                "ConversationController.enqueue() during shutdown turn_id=%s",
                task.ctx.turn_id,
            )
        try:
            self._tasks.put_nowait(task)
            _log_fn(
                "ConversationController.enqueue()",
                "ok qsize=%s",
                self._tasks.qsize(),
            )
        except queue.Full:
            logger.error(
                "ConversationController.enqueue() queue full turn_id=%s qsize=%s",
                task.ctx.turn_id,
                self._tasks.qsize(),
            )

    def _run_worker(self) -> None:
        """worker 线程入口 — 独立 event loop + 独立 DB 连接池（不可复用主 loop 的 engine）。"""
        _log_fn("ConversationController._run_worker()", "enter")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._worker_loop())
        finally:
            loop.close()
            _log_fn("ConversationController._run_worker()", "exit")

    async def _worker_loop(self) -> None:
        """从队列取 task 并落库，直至收到 shutdown sentinel。"""
        _log_fn("ConversationController._worker_loop()", "enter")
        # 使用独立的线程池，避免主进程线程池耗尽
        # 使用独立的DB连接池，避免主进程DB连接池耗尽
        main_db = Database.get()
        worker_engine = create_async_engine(
            main_db.database_url,
            pool_size=2,
            max_overflow=2,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        session_factory = async_sessionmaker(worker_engine, expire_on_commit=False)
        _log_fn("ConversationController._worker_loop()", "worker db pool ready")
        try:
            while True:
                task = await asyncio.get_running_loop().run_in_executor(None, self._tasks.get)
                try:
                    if task is _SHUTDOWN_SENTINEL:
                        _log_fn("ConversationController._worker_loop()", "shutdown sentinel")
                        break
                    assert isinstance(task, TurnPersistTask)
                    _log_fn(
                        "ConversationController._worker_loop()",
                        "dequeue turn_id=%s",
                        task.ctx.turn_id,
                    )
                    await self._persist_until_success(task, session_factory)
                finally:
                    self._tasks.task_done()
        finally:
            await worker_engine.dispose()
            _log_fn("ConversationController._worker_loop()", "worker db pool disposed")

    async def _persist_until_success(
        self,
        task: TurnPersistTask,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """落库失败则 error 日志 + 1s 后重试，直至成功。"""
        attempt = 0
        while True:
            attempt += 1
            _log_fn(
                "ConversationController._persist_until_success()",
                "turn_id=%s attempt=%s",
                task.ctx.turn_id,
                attempt,
            )
            try:
                async with session_factory() as db:
                    async with db.begin():
                        await self._persist_turn_in_tx(db, task)
                _log_fn(
                    "ConversationController._persist_until_success()",
                    "ok turn_id=%s steps=%s attempt=%s",
                    task.ctx.turn_id,
                    task.run_result.total_steps,
                    attempt,
                )
                return
            except Exception as exc:
                logger.error(
                    "ConversationController._persist_until_success() failed turn_id=%s attempt=%s: %s",
                    task.ctx.turn_id,
                    attempt,
                    exc,
                    exc_info=True,
                )
                _log_fn(
                    "ConversationController._persist_until_success()",
                    "retry in %ss turn_id=%s",
                    PERSIST_RETRY_DELAY_SECONDS,
                    task.ctx.turn_id,
                )
                await asyncio.sleep(PERSIST_RETRY_DELAY_SECONDS)

    @staticmethod
    async def _persist_turn_in_tx(db: AsyncSession, task: TurnPersistTask) -> None:
        """单事务写入 user/assistant message、loop_steps、loop_run。"""
        ctx = task.ctx
        run_result = task.run_result
        conversation_id = ctx.conversation.id
        _log_fn(
            "ConversationController._persist_turn_in_tx()",
            "turn_id=%s conversation_id=%s pending_steps=%s",
            ctx.turn_id,
            conversation_id,
            len(ctx.pending_steps),
        )
        if conversation_id is None:
            raise RuntimeError("conversation has no id")

        reply = extract_reply(run_result.messages)
        user_message_id: int | None = None

        # 创建用户消息
        if ctx.message.strip():
            user_row = await svc.chat_message_service.create(
                db,
                ChatMessage(
                    conversation_id=conversation_id,
                    role="user",
                    content=ctx.message,
                ),
            )
            user_message_id = user_row.id

        # 创建助手消息
        await svc.chat_message_service.create(
            db,
            ChatMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=reply,
            ),
        )

        # 创建agent loop步骤
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
            )

        # 创建agent loop运行情况信息
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
        )
        _log_fn(
            "ConversationController._persist_turn_in_tx()",
            "done turn_id=%s user_message_id=%s tokens=%s",
            ctx.turn_id,
            user_message_id,
            run_result.total_tokens,
        )


conversation_controller = ConversationController.instance()
