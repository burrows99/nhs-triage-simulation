# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY *.py ./

# Create output directory with proper permissions
RUN mkdir -p output && chmod 777 output

# Set Python path
ENV PYTHONPATH=/app

# Set default environment variables
ENV OLLAMA_BASE_URL=http://ollama:11434

# Default command (can be overridden in docker-compose)
CMD ["python3", "test_all_triage_systems.py"]
