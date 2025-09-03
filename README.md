# Hospital Simulation with Multiple Triage Systems

A comprehensive hospital simulation system comparing three different triage approaches:
- **Manchester Triage System** (rule-based fuzzy logic)
- **Single LLM Triage System** (single AI agent)
- **Multi-Agent LLM Triage System** (6 specialized agents with LangGraph)

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Basic Usage
```bash
# Run all systems with default settings
python3 main.py

# Show help and all available options
python3 main.py --help
```

## 📋 Command Reference

### System Selection

```bash
# Run all three triage systems (default)
python3 main.py --systems all

# Run only Manchester Triage System
python3 main.py --systems manchester

# Run only Single LLM system
python3 main.py --systems single

# Run only Multi-Agent LLM system
python3 main.py --systems multi-agent

# Run multiple specific systems
python3 main.py --systems manchester single
python3 main.py --systems single multi-agent
```

### Patient Volume Control

```bash
# Small test with ~5 patients
python3 main.py --arrival-rate 5 --duration 60

# Medium test with ~25 patients
python3 main.py --arrival-rate 25 --duration 60

# Large test with ~100 patients
python3 main.py --arrival-rate 50 --duration 120

# Full 8-hour simulation (default: ~400 patients)
python3 main.py --arrival-rate 50 --duration 480
```

### Resource Configuration

```bash
# Default resources (3 nurses, 2 doctors, 4 beds)
python3 main.py

# High-capacity hospital
python3 main.py --nurses 6 --doctors 4 --beds 10

# Low-capacity clinic
python3 main.py --nurses 2 --doctors 1 --beds 2

# Stressed system (high patients, low resources)
python3 main.py --arrival-rate 80 --nurses 2 --doctors 1 --beds 3
```

### Output and Logging

```bash
# Quiet mode (minimal output)
python3 main.py --quiet

# Verbose debugging
python3 main.py --verbose

# Custom output directory
python3 main.py --output-dir ./my_results

# Skip plot generation (faster execution)
python3 main.py --skip-plots

# Set specific log level
python3 main.py --log-level DEBUG
python3 main.py --log-level WARNING
```

### Reproducible Results

```bash
# Set random seed for reproducible results
python3 main.py --seed 12345

# Research configuration with seed
python3 main.py --seed 42 --duration 480 --arrival-rate 50 --output-dir ./research_run_1
```

## 🎯 Common Scenarios

### Quick Testing (5 patients)
```bash
# All systems, minimal patients, quiet output
python3 main.py --systems all --arrival-rate 5 --duration 60 --quiet

# Single system test
python3 main.py --systems manchester --arrival-rate 5 --duration 60 --quiet
```

### Development Testing
```bash
# Fast iteration with verbose logging
python3 main.py --systems manchester --arrival-rate 10 --duration 30 --verbose --skip-plots

# Debug specific system
python3 main.py --systems single --arrival-rate 3 --duration 20 --log-level DEBUG
```

### Performance Comparison
```bash
# Standard comparison (all systems, 1 hour)
python3 main.py --systems all --duration 60 --arrival-rate 30

# Stress test comparison
python3 main.py --systems all --arrival-rate 80 --duration 120 --nurses 3 --doctors 2

# Capacity planning test
python3 main.py --systems all --arrival-rate 60 --nurses 5 --doctors 3 --beds 8
```

### Research Scenarios
```bash
# Baseline study
python3 main.py --seed 100 --duration 480 --arrival-rate 50 --output-dir ./baseline

# High-load study
python3 main.py --seed 100 --duration 480 --arrival-rate 80 --output-dir ./high_load

# Resource-constrained study
python3 main.py --seed 100 --nurses 2 --doctors 1 --beds 3 --output-dir ./constrained
```

### Multi-Agent System Testing
```bash
# Test multi-agent system only
python3 main.py --systems multi-agent --arrival-rate 10 --duration 60

# Compare single vs multi-agent
python3 main.py --systems single multi-agent --arrival-rate 20 --duration 90

# Multi-agent with verbose logging
python3 main.py --systems multi-agent --verbose --arrival-rate 5 --duration 30
```

## 📊 Output Structure

Results are saved to separate directories for each system:

```
output/simulation/
├── manchester_triage_system/
│   ├── metrics/
│   │   ├── nhs_metrics.json
│   │   ├── nhs_patient_data.csv
│   │   └── operational_metrics.json
│   └── plots/
│       ├── combined_dashboard.png
│       ├── nhs_compliance.png
│       ├── queue_analysis.png
│       ├── resource_utilization.png
│       └── triage_distribution.png
├── single_llm_system/
│   └── [same structure]
└── multi_agent_llm_system/
    └── [same structure]
```

## 🔧 Configuration Options

### Simulation Parameters
- `--duration, -d`: Simulation duration in minutes (default: 480 = 8 hours)
- `--arrival-rate, -a`: Patient arrival rate per hour (default: 50)
- `--delay-scaling`: Delay scaling factor for simulation speed (default: 0)

### Resource Allocation
- `--nurses, -n`: Number of nurses available (default: 3)
- `--doctors, -dr`: Number of doctors available (default: 2)
- `--beds, -b`: Number of beds available (default: 4)

### System Selection
- `--systems, -s`: Triage systems to run (choices: manchester, single, multi-agent, all)

### Output Control
- `--output-dir, -o`: Base output directory (default: ./output/simulation)
- `--log-level, -l`: Logging level (choices: DEBUG, INFO, WARNING, ERROR)
- `--skip-plots`: Skip generating plots and charts
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress non-essential output

### Reproducibility
- `--seed`: Random seed for reproducible results

## 🏥 Triage Systems

### Manchester Triage System
- **Type**: Rule-based fuzzy logic
- **Features**: NHS-compliant, deterministic, fast
- **Use Case**: Baseline comparison, clinical validation

### Single LLM Triage System
- **Type**: Single AI agent
- **Features**: Context-aware, explainable, adaptive
- **Use Case**: AI-assisted triage, operational context integration

### Multi-Agent LLM Triage System
- **Type**: 6 specialized agents with LangGraph
- **Agents**: Symptom Analyzer, History Evaluator, Guidelines Checker, Operations Analyst, Trends Analyzer, Finalizer
- **Features**: Comprehensive analysis, consensus-based decisions, parallel processing
- **Use Case**: Complex cases, research, maximum accuracy

## 🔑 Environment Setup

For LLM-based systems, set up Hugging Face API:

```bash
# Set environment variables
export HF_API_KEY="your-huggingface-api-key"
export HF_BASE_URL="https://router.huggingface.co/v1"
export HF_MODEL="openai/gpt-oss-120b:together"
```

Or create a `.env` file:
```
HF_API_KEY=your-huggingface-api-key
HF_BASE_URL=https://router.huggingface.co/v1
HF_MODEL=openai/gpt-oss-120b:together
```

## 📈 Performance Tips

- Use `--skip-plots` for faster execution during development
- Use `--quiet` to reduce logging overhead
- Set `--arrival-rate` and `--duration` appropriately for your testing needs
- Use `--seed` for reproducible results in research
- Monitor system resources when running multi-agent systems

## 🐛 Troubleshooting

### Common Issues

**LLM systems not running:**
- Check HF_API_KEY is set correctly
- Verify API credits are available
- Use `--verbose` to see detailed error messages

**Simulation running slowly:**
- Reduce `--arrival-rate` or `--duration`
- Use `--skip-plots` flag
- Check system resources

**Import errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility

### Debug Commands

```bash
# Test system imports
python3 -c "from src.triage.llm_triage_system import SingleLLMTriage; print('✅ Imports working')"

# Test with minimal configuration
python3 main.py --systems manchester --arrival-rate 1 --duration 5 --verbose

# Check available systems
python3 main.py --help
```

## 📚 Examples

### Example 1: Quick System Comparison
```bash
python3 main.py --systems all --arrival-rate 10 --duration 30 --quiet
```

### Example 2: Research Study
```bash
python3 main.py --seed 42 --systems all --duration 240 --arrival-rate 40 --nurses 4 --doctors 3 --output-dir ./study_results
```

### Example 3: Multi-Agent Deep Dive
```bash
python3 main.py --systems multi-agent --arrival-rate 5 --duration 60 --verbose --log-level DEBUG
```

### Example 4: Stress Testing
```bash
python3 main.py --systems all --arrival-rate 100 --duration 60 --nurses 2 --doctors 1 --beds 2
```

---

**Note**: LLM-based systems require valid Hugging Face API credentials. Manchester Triage System works without external dependencies.