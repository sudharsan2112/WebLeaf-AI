FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY backend ./backend
COPY frontend ./frontend

RUN mkdir -p /app/data/faiss_store

EXPOSE 8080

CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
