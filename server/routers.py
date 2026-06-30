"""HTTP 路由注册。"""

from __future__ import annotations

from fastapi import Depends, FastAPI

from server.api import account, agent, budgets, categories, geo, knowledge, summary, transactions
from server.service.account import get_current_account

protected = [Depends(get_current_account)]


def register_routers(app: FastAPI) -> None:
    app.include_router(account.router)
    app.include_router(categories.router, dependencies=protected)
    app.include_router(budgets.router, dependencies=protected)
    app.include_router(transactions.router, dependencies=protected)
    app.include_router(summary.router, dependencies=protected)
    app.include_router(geo.router, dependencies=protected)
    app.include_router(knowledge.router, dependencies=protected)
    app.include_router(agent.router, dependencies=protected)
