from __future__ import annotations

from typing import Literal

from server.model.base import RequestBase


class SummaryQueryRequest(RequestBase):
    """GET /summary — 汇总查询参数."""

    period: Literal["hour", "day", "week", "month", "year"]
    start: str
    end: str
