"""HTTP 路由注册。"""

from __future__ import annotations

from fastapi import FastAPI

from server.api import agent, budgets, categories, summary, transactions


def register_routers(app: FastAPI) -> None:
    app.include_router(categories.router)
    app.include_router(budgets.router)
    app.include_router(transactions.router)
    app.include_router(summary.router)
    app.include_router(agent.router)
