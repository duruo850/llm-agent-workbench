"""地理与天气 API — IP 定位 + 当地天气。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from agent.mcp.gaode import AmapMCPClient, resolve_ip_location, resolve_weather
from server.model.response.geo import GeoMeResponse
from utils.client_ip import get_client_ip

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/me", response_model=GeoMeResponse)
async def geo_me(
    request: Request,
    ip: str | None = Query(default=None, description="调试用 IP 覆盖"),
) -> GeoMeResponse:
    if not AmapMCPClient.is_configured():
        raise HTTPException(status_code=503, detail="未配置 AMAP_MAPS_API_KEY")

    # 获取客户端IP
    client_ip = get_client_ip(request, override=ip)
    
    # 解析IP地理位置
    try:
        location = await resolve_ip_location(client_ip)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # 获取天气信息
    if location.adcode:
        weather = await resolve_weather(location.adcode)
        print(f"天气: {weather.weather or '-'} {weather.temperature or '-'}°C")
    else:
        print("天气: (无 adcode,跳过)")

    return GeoMeResponse(
        ip=location.ip,
        province=location.province,
        city=location.city,
        adcode=location.adcode,
        weather=weather.weather,
        temperature=weather.temperature,
    )
