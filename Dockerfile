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
COPY scripts ./scripts

EXPOSE 8001

RUN chmod +x ./scripts/start_backend.sh

CMD ["./scripts/start_backend.sh"]
