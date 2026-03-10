FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY sample_log.txt ./sample_log.txt
COPY README_backend.md ./README_backend.md

EXPOSE 8001

CMD ["sh", "-c", "uvicorn backend.main:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8001}"]
