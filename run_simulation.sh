#!/bin/bash

# NHS Triage Simulation Runner
# This script ensures simulations always run using Docker Compose

set -e  # Exit on any error

echo "======================================================"
echo "NHS TRIAGE SIMULATION - DOCKER COMPOSE RUNNER"
echo "======================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

echo "✅ Docker is running"
echo "✅ docker-compose is available"
echo ""

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Build and start services
echo "🔨 Building simulation environment..."
docker-compose build --no-cache simulation

echo "🚀 Starting Ollama service..."
docker-compose up -d ollama ollama-downloader

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama service to be ready..."
while ! curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "   Ollama not ready, waiting 5 seconds..."
    sleep 5
done
echo "✅ Ollama service is ready"

# Run the simulation
echo "🏥 Starting NHS Triage Simulation..."
echo "   This will run all three triage systems and generate:"
echo "   - Individual system plots and telemetry"
echo "   - CSV data exports"
echo "   - Comparison visualizations"
echo ""

docker-compose run --rm simulation

# Check results
echo ""
echo "📊 Simulation completed! Results available in:"
echo "   📁 output/Manchester Triage System/"
echo "      ├── 📈 plots/ (visualization charts)"
echo "      ├── 📋 csv/ (patient data)"
echo "      └── 🔍 telemetry/ (decision analysis)"
echo "   📁 output/Single LLM-Based Triage System/"
echo "   📁 output/Multi-Agent LLM-Based Triage System/"
echo "   📁 output/comparison/ (cross-system analysis)"
echo ""

# Optional: Keep services running for additional tests
read -p "🤔 Keep Ollama service running for additional tests? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "🛑 Stopping all services..."
    docker-compose down
    echo "✅ All services stopped"
else
    echo "🔄 Ollama service will continue running"
    echo "   Use 'docker-compose down' to stop when finished"
fi

echo ""
echo "======================================================"
echo "✅ SIMULATION COMPLETE"
echo "======================================================"