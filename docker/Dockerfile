# =========================
# docker/Dockerfile (multi-stage, slim)
# =========================

# ---- Base ----
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app/server

# ---- Builder (có build deps) ----
FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# copy requirements riêng để tối ưu cache
COPY server/requirements.txt /tmp/requirements.txt
RUN pip install --prefix=/install -r /tmp/requirements.txt

# ---- Runtime (nhẹ, non-root) ----
FROM base AS runtime

# có thể cần curl nếu sau này dùng HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# tạo user không quyền root
RUN useradd -m -u 10001 appuser
USER appuser

# copy site-packages đã build từ stage builder
COPY --from=builder /install /usr/local

# copy mã nguồn
COPY --chown=appuser:appuser server/ /app/server/

EXPOSE 5000
CMD ["python", "-u", "server.py"]
