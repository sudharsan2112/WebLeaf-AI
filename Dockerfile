FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY backend ./backend
COPY frontend ./frontend

# Runtime application data is mounted here by the hosting provider.
RUN mkdir -p /app/data/faiss_store

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
