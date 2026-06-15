FROM python:3.12-slim

WORKDIR /app

# Build context = project root (Railway default)
COPY api/ /app/api/
RUN pip install --no-cache-dir -r /app/api/requirements.txt

EXPOSE 8080

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
