"""上传文件类型识别 — Agent 按类型路由到对应 skill。"""

from __future__ import annotations

from enum import Enum


class FileKind(str, Enum):
    CSV = "csv"
    IMAGE = "image"
    UNKNOWN = "unknown"


def detect_file_kind(
    *,
    filename: str | None = None,
    mime: str | None = None,
    content: str | bytes | None = None,
    data_url: str | None = None,
) -> FileKind:
    """根据文件名、MIME、data URL 或内容判断文件类型。"""
    if data_url:
        if data_url.startswith("data:image/"):
            return FileKind.IMAGE
        return FileKind.UNKNOWN

    name = (filename or "").lower()
    media = (mime or "").lower()

    if name.endswith(".csv") or media in {"text/csv", "application/csv"}:
        return FileKind.CSV
    if media.startswith("image/") or any(
        name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")
    ):
        return FileKind.IMAGE

    if content is not None:
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
        if text.strip() and "\n" in text.strip() and not text.lstrip().startswith("{"):
            return FileKind.CSV

    return FileKind.UNKNOWN
