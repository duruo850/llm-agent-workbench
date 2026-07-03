import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_db(db: AsyncSession) -> None:
    """skills 工具链依赖 PostgreSQL；仅检查连通性，不跑迁移。"""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        print(f"PostgreSQL 未就绪: {exc}\n请先运行: docker compose up -d", file=sys.stderr)
        sys.exit(1)