# NHS Triage Simulation - Docker Compose Guide

This guide explains how to run the NHS Triage Simulation using Docker Compose, which is now the **recommended and default method** for running simulations.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- docker-compose available
- At least 4GB of available RAM
- At least 2GB of free disk space

### Run Simulation (Recommended)

```bash
# Make the script executable (first time only)
chmod +x run_simulation.sh

# Run the complete simulation
./run_simulation.sh
```

This script will:
1. ✅ Check Docker availability
2. 🧹 Clean up any existing containers
3. 🔨 Build the simulation environment
4. 🚀 Start Ollama LLM service
5. ⏳ Wait for services to be ready
6. 🏥 Run all three triage systems
7. 📊 Generate comprehensive results

## 📁 Output Structure

After running the simulation, you'll find results in:

```
output/
├── Manchester Triage System/
│   ├── csv/
│   │   └── patient_data.csv          # Complete patient data
│   ├── plots/
│   │   ├── poisson_arrivals.png      # Arrival patterns
│   │   ├── priority_distribution.png # Priority analysis
│   │   └── wait_for_consult.png      # Wait time analysis
│   └── telemetry/
│       ├── patient_*_timeline.png    # Decision timelines
│       └── telemetry_report.md       # Detailed analysis
├── Single LLM-Based Triage System/
│   └── [same structure as above]
├── Multi-Agent LLM-Based Triage System/
│   └── [same structure as above]
└── comparison/
    ├── triage_systems_comparison.png # Cross-system comparison
    └── [telemetry comparisons]
```

## 🔧 Manual Docker Compose Commands

If you prefer manual control:

### Start Services
```bash
# Start Ollama service
docker-compose up -d ollama ollama-downloader

# Wait for Ollama to be ready
curl http://localhost:11434/api/tags
```

### Run Simulation
```bash
# Run all triage systems
docker-compose run --rm simulation

# Or run specific test
docker-compose run --rm simulation python3 main.py
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📊 CSV Data Fields

The generated CSV files contain comprehensive patient data:

### Patient Demographics
- `id`: Unique patient identifier
- `age`: Patient age (realistic ED distribution)
- `gender`: Male/Female/Other
- `arrival_time`: Simulation time of arrival

### Clinical Data
- `severity`: Calculated severity score (0.0-1.0)
- `chief_complaint`: Primary reason for ED visit
- `vital_signs`: JSON object with heart rate, BP, temperature, etc.
- `medical_history`: Relevant medical conditions

### Triage Results
- `priority`: Assigned triage priority (1-5)
- `triage_system`: Which system performed triage
- `triage_rationale`: Explanation of priority assignment
- `recommended_actions`: Suggested clinical actions

### Timing Data
- `triage_time`: When triage was completed
- `wait_for_triage`: Time waiting for triage assessment
- `consult_time`: When consultation began
- `wait_for_consult`: Time waiting for doctor
- `consultation_duration`: Length of consultation
- `discharge_time`: When patient left ED
- `total_time`: Total time in emergency department

### Outcomes
- `admitted`: Boolean - was patient admitted to hospital
- `admission_reason`: Why patient was admitted
- `discharge_reason`: Why patient was discharged
- `created_timestamp`: When record was created

## 🔍 Telemetry Features

The simulation includes comprehensive decision-making telemetry:

### Manchester Triage System
- Fuzzy logic membership calculations
- Rule activation tracking
- Defuzzification process details

### LLM-Based Systems
- Prompt generation timing
- LLM inference duration
- Response parsing success/failure
- Multi-agent coordination (for Multi-Agent system)

### Visualization
- Patient decision timelines
- System performance comparisons
- Error analysis and success rates
- Processing time distributions

## 🛠️ Troubleshooting

### Ollama Service Issues
```bash
# Check if Ollama is responding
curl http://localhost:11434/api/tags

# View Ollama logs
docker-compose logs ollama

# Restart Ollama service
docker-compose restart ollama
```

### Simulation Errors
```bash
# View simulation logs
docker-compose logs simulation

# Run simulation with debug output
docker-compose run --rm simulation python3 -u test_all_triage_systems.py
```

### Storage Issues
```bash
# Clean up Docker resources
docker system prune -f

# Remove simulation volumes
docker-compose down -v
```

### Permission Issues
```bash
# Fix output directory permissions
sudo chmod -R 755 output/
```

## ⚙️ Configuration

### Simulation Parameters
Edit `src/config/parameters.py`:
- `sim_duration`: Simulation length (default: 120 minutes)
- `patient_arrival_rate`: Patients per hour
- `resource_counts`: Nurses, doctors, cubicles

### Ollama Configuration
Edit `src/config/config_manager.py`:
- `base_url`: Ollama service URL
- `model`: LLM model to use
- `request_timeout`: API timeout settings

## 🔄 Development Workflow

### Code Changes
```bash
# Rebuild after code changes
docker-compose build simulation

# Run with live code mounting
docker-compose run --rm -v $(pwd)/src:/app/src simulation
```

### Testing Individual Systems
```bash
# Test only Manchester Triage
docker-compose run --rm simulation python3 -c "from src.main import run_simulation; from src.triage_systems.manchester_triage import ManchesterTriage; run_simulation(ManchesterTriage())"
```

## 📈 Performance Notes

- **Manchester Triage**: ~50-100ms per patient
- **Single LLM**: ~1-3 seconds per patient (depends on model)
- **Multi-Agent LLM**: ~3-10 seconds per patient
- **Memory Usage**: ~2-4GB during simulation
- **Disk Usage**: ~100-500MB for results

## 🎯 Best Practices

1. **Always use Docker Compose** for consistent environments
2. **Monitor resource usage** during long simulations
3. **Back up results** before running new simulations
4. **Check Ollama health** before starting LLM-based tests
5. **Use the shell script** for automated setup and cleanup

---

**Need Help?** Check the logs with `docker-compose logs` or run `./run_simulation.sh` for guided execution.