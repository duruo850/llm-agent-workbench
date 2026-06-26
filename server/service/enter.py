"""Service 层 FastCRUD 实例入口（各 ``{entity}.py`` Service 内部使用）。"""

from __future__ import annotations

from fastcrud import FastCRUD

from server.model.account import Account
from server.model.budget import Budget
from server.model.category import Category
from server.model.transaction import Transaction

account_crud = FastCRUD(Account)
category_crud = FastCRUD(Category)
budget_crud = FastCRUD(Budget)
transaction_crud = FastCRUD(Transaction)
