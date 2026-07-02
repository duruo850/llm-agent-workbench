"""Service 层 FastCRUD 实例入口（各 ``{entity}.py`` Service 内部使用）。"""

from __future__ import annotations

from fastcrud import FastCRUD

from server.model.account import Account
from server.model.agent_loop_run import AgentLoopRun
from server.model.agent_loop_step import AgentLoopStep
from server.model.budget import Budget
from server.model.category import Category
from server.model.chat_message import ChatMessage
from server.model.conversation import Conversation
from server.model.transaction import Transaction

account_crud = FastCRUD(Account)
category_crud = FastCRUD(Category)
budget_crud = FastCRUD(Budget)
transaction_crud = FastCRUD(Transaction)
conversation_crud = FastCRUD(Conversation)
chat_message_crud = FastCRUD(ChatMessage)
agent_loop_step_crud = FastCRUD(AgentLoopStep)
agent_loop_run_crud = FastCRUD(AgentLoopRun)
