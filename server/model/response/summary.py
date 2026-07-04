from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from server.model.base import ResponseBase


class SummaryResponse(ResponseBase):
    """汇总响应 — Agent ``get_summary`` 与 HTTP ``GET /summary`` 共用。"""

    period: str  # hour / day / week / month / year
    start: datetime  # 起点(含), YYYY-MM-DD 或 ISO datetime
    end: datetime  # 终点(含)
    total_amount: Decimal  # 总支出
    total_count: int  # 总笔数
