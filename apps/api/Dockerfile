FROM python:3.12.10-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY apps/api/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

FROM python:3.12.10-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"
WORKDIR /app
RUN addgroup --system --gid 1001 atlas && adduser --system --uid 1001 --ingroup atlas atlas
COPY --from=builder /opt/venv /opt/venv
COPY --chown=atlas:atlas apps/__init__.py apps/__init__.py
COPY --chown=atlas:atlas apps/api apps/api
COPY --chown=atlas:atlas packages/database packages/database
USER atlas
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live', timeout=3)"
CMD ["uvicorn", "apps.api.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--proxy-headers", "--forwarded-allow-ips=*"]
