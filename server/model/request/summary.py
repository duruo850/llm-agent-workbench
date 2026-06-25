from __future__ import annotations

from pydantic import Field

from server.model.base import RequestBase


class MonthlySummaryQueryRequest(RequestBase):
    """GET /summary/monthly — 月度汇总查询参数。"""

    month: str = Field(pattern=r"^\d{4}-\d{2}$")
