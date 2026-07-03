FROM python:3.14-slim-bookworm

ARG APP_VERSION=1.0.0
LABEL org.opencontainers.image.version="${APP_VERSION}"

WORKDIR /app

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir 'psycopg[binary]>=3.2.0'

COPY server/ server/
COPY agent/ agent/
COPY storage/ storage/
COPY common/ common/
COPY utils/ utils/

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=30s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
