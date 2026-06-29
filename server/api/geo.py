"""地理与天气 API — IP 定位 + 当地天气。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from agent.mcp.gaode import AmapMCPClient, resolve_ip_weather
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

    client_ip = get_client_ip(request, override=ip)
    try:
        result = await resolve_ip_weather(client_ip)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return GeoMeResponse(
        ip=result.ip,
        province=result.province,
        city=result.city,
        adcode=result.adcode,
        weather=result.weather,
        temperature=result.temperature,
    )
