"""Milvus 连接、ORM patch 与向量检索栈就绪状态。"""

from __future__ import annotations

import logging
import urllib.error
import urllib.request

from pymilvus import MilvusClient, connections

from common.env import get_milvus_uri, get_ollama_embedding_model, get_ollama_uri

logger = logging.getLogger("billmind.milvus")


def _patch_milvus_client_orm_sync() -> None:
    """LangChain Milvus 混用 MilvusClient + ORM Collection，需为 client alias 注册 ORM 连接。"""
    if getattr(MilvusClient.__init__, "_billmind_patched", False):
        return

    _orig_init = MilvusClient.__init__

    def _wrapped(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        alias = getattr(self, "_using", None)
        if not alias or connections.has_connection(alias):
            return
        uri = kwargs.get("uri")
        if uri is None and args:
            uri = args[0]
        if not uri:
            uri = get_milvus_uri()
        connections.connect(alias=alias, uri=uri)

    _wrapped._billmind_patched = True  # type: ignore[attr-defined]
    MilvusClient.__init__ = _wrapped  # type: ignore[method-assign]


_patch_milvus_client_orm_sync()


def get_client() -> MilvusClient:
    """返回连接当前 ``MILVUS_URI`` 的 MilvusClient。"""
    return MilvusClient(uri=get_milvus_uri())


def available() -> bool:
    """Milvus 是否可达（仅 ping，不保证已有索引数据）。"""
    try:
        get_client()
        return True
    except Exception as exc:
        logger.warning("Milvus 不可达 (%s): %s", get_milvus_uri(), exc)
        return False


def ollama_embedding_ready() -> bool:
    """Ollama 是否已加载 embedding 模型。"""
    model = get_ollama_embedding_model()
    tags_url = f"{get_ollama_uri().rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=5) as resp:
            return model in resp.read().decode()
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def embedding_ready() -> bool:
    """Milvus 可达且 Ollama embedding 模型可用。"""
    return available() and ollama_embedding_ready()
