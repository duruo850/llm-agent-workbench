from __future__ import annotations

from fastcrud import crud_router

from server.crud.instances import budget_crud, category_crud, transaction_crud
from server.db.session import get_db
from server.model.budget import Budget
from server.model.category import Category
from server.model.request import (
    BudgetCreateRequest,
    BudgetUpdateRequest,
    CategoryCreateRequest,
    CategoryUpdateRequest,
    TransactionCreateRequest,
    TransactionUpdateRequest,
)
from server.model.response import BudgetGetResponse, CategoryGetResponse, TransactionGetResponse
from server.model.transaction import Transaction

category_router = crud_router(
    session=get_db,
    model=Category,
    crud=category_crud,
    create_schema=CategoryCreateRequest,
    update_schema=CategoryUpdateRequest,
    select_schema=CategoryGetResponse,
    path="/categories",
    tags=["categories"],
)

budget_router = crud_router(
    session=get_db,
    model=Budget,
    crud=budget_crud,
    create_schema=BudgetCreateRequest,
    update_schema=BudgetUpdateRequest,
    select_schema=BudgetGetResponse,
    path="/budgets",
    tags=["budgets"],
)

transaction_router = crud_router(
    session=get_db,
    model=Transaction,
    crud=transaction_crud,
    create_schema=TransactionCreateRequest,
    update_schema=TransactionUpdateRequest,
    select_schema=TransactionGetResponse,
    path="/transactions",
    tags=["transactions"],
    deleted_methods=["read_multi"],
)
