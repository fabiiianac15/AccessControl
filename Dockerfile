FROM python:3.13-slim

ENV UV_LOCKED=1 PYTHONUNBUFFERED=1 PORTERO_HOST=0.0.0.0 PORTERO_DATA_DIR=/data

# opencv-python-headless necesita estas librerías del sistema.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.8.* \
    && useradd --system --uid 10001 --home-dir /app portero \
    && mkdir -p /data /app \
    && chown portero /data

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --no-dev --no-editable --no-cache

USER portero
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]
CMD ["/app/.venv/bin/portero", "serve"]
