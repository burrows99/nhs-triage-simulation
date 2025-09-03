FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create directory for models
RUN mkdir -p /app/models

# Expose ports
EXPOSE 8000 11434

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Start Ollama in background\n\
echo "Starting Ollama server..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
\n\
# Wait for Ollama to be ready\n\
echo "Waiting for Ollama to start..."\n\
while ! curl -s http://localhost:11434/api/tags > /dev/null; do\n\
    sleep 2\n\
done\n\
echo "Ollama server is running!"\n\
\n\
# Download model BEFORE API becomes available for health checks\n\
echo "Downloading UK triage model (this may take several minutes)..."\n\
ollama pull hf.co/mradermacher/docmap-uk-triage-merged-qwen2.5-7b-GGUF:Q4_K_M\n\
echo "Model download completed!"\n\
\n\
# Verify model is available\n\
echo "Verifying model availability..."\n\
ollama list | grep -q "hf.co/mradermacher/docmap-uk-triage-merged-qwen2.5-7b-GGUF:Q4_K_M" && echo "✅ Model verified and ready!" || echo "⚠️  Model verification failed"\n\
\n\
# Now API is fully ready for use\n\
echo "🎯 Triage system ready! API available at http://localhost:11434"\n\
echo "Container ready! Ollama PID: $OLLAMA_PID"\n\
wait $OLLAMA_PID' > /app/start.sh

RUN chmod +x /app/start.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV OLLAMA_HOST=0.0.0.0

# Make start script executable
RUN chmod +x /app/start.sh

# Default command (can be overridden by docker-compose)
CMD ["/app/start.sh"]