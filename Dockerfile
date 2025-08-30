# Base stage with common dependencies
FROM python:3.9-slim as base

ENV PYTHONPATH="/app"
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

# Production target
FROM base as main
CMD ["python", "-m", "src.main"]

# Debug target with hot reload capabilities
FROM base as debug
RUN apt-get update && apt-get install -y entr && rm -rf /var/lib/apt/lists/*
RUN pip install debugpy
EXPOSE 5678
CMD ["sh", "-c", "find /app/src -name '*.py' | entr -rn python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m src.main"]
