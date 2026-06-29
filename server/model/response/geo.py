"""地理与天气 API 响应模型。"""

from __future__ import annotations

from pydantic import BaseModel


class GeoMeResponse(BaseModel):
    ip: str # 公网 IP
    province: str | None = None # 省份
    city: str | None = None # 城市
    adcode: str | None = None # 行政区划代码
    weather: str | None = None # 天气
    temperature: str | None = None # 温度
