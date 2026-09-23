"""地理与天气 API — IP 定位 + 当地天气。"""

from __future__ import annotations

import logging
import sys

from fastapi import APIRouter, HTTPException, Query, Request

from agent.mcp.gaode import AmapMCPClient, resolve_ip_location, resolve_weather
from server.model.response.geo import GeoMeResponse
from utils.client_ip import get_client_ip

router = APIRouter(prefix="/geo", tags=["geo"])
logger = logging.getLogger("billmind.geo")


def _geo_log(msg: str, *args: object) -> None:
    text = msg % args if args else msg
    logger.info("%s", text)
    # debugpy / uvicorn --reload 下 logger 有时不进调试终端，print 保证可见
    print(f"[billmind.geo] {text}", file=sys.stderr, flush=True)


@router.get("/me", response_model=GeoMeResponse)
async def geo_me(
    request: Request,
    ip: str | None = Query(default=None, description="调试用 IP 覆盖"),
) -> GeoMeResponse:
    if not AmapMCPClient.is_configured():
        raise HTTPException(status_code=503, detail="未配置 AMAP_MAPS_API_KEY")

    forwarded = request.headers.get("X-Forwarded-For")
    real_ip = request.headers.get("X-Real-IP")
    peer = request.client.host if request.client else None
    client_ip = get_client_ip(request, override=ip)
    _geo_log(
        "resolve client_ip=%s override=%s xff=%s x_real_ip=%s peer=%s",
        client_ip,
        ip,
        forwarded,
        real_ip,
        peer,
    )

    location = None
    weather_text: str | None = None
    temperature: str | None = None
    try:
        location = await resolve_ip_location(client_ip)
        _geo_log("location=%s", location)

        if location.adcode:
            weather = await resolve_weather(location.adcode)
            weather_text = weather.weather
            temperature = weather.temperature
            _geo_log("weather=%s", weather)
        else:
            _geo_log("no adcode, skip weather; location=%s", location)
    except Exception as exc:
        _geo_log(
            "FAILED client_ip=%s location=%s weather=%s temperature=%s err=%r",
            client_ip,
            location,
            weather_text,
            temperature,
            exc,
        )
        logger.exception("geo/me failed")
        raise

    return GeoMeResponse(
        ip=location.ip,
        province=location.province,
        city=location.city,
        adcode=location.adcode,
        weather=weather_text,
        temperature=temperature,
    )
