# docker/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/server

# Cài build deps cho các gói như greenlet/eventlet nếu cần biên dịch
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để cache layer pip
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install -r requirements.txt

# Copy phần còn lại của source
COPY server/ /app/server/

EXPOSE 5000
CMD ["python", "server.py"]
