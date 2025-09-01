# General Healthcare Triage Simulator

A comprehensive simulation system for general healthcare triage using an enhanced Manchester Triage System (MTS) that handles both routine healthcare encounters and emergency presentations.

## Overview

This simulator models patient flow through a general healthcare facility, including:
- **Routine Care**: Wellness visits, check-ups, preventive care
- **Emergency Care**: Urgent symptoms, acute conditions, life-threatening situations
- **Mixed Scenarios**: Realistic healthcare environments with varied patient acuity

## Quick Start

### Basic Simulation
```bash
# Run default simulation (24 hours, 0.5 patients/minute)
python -m src.main

# Run with verbose logging
python -m src.main --verbose

# Run shorter simulation (2 hours)
python -m src.main --duration 120
```

### 🚀 Comprehensive Analysis (One Command)
```bash
# Run EVERYTHING: all scenarios, comparisons, metrics, and reports
python -m src.main --all

# Run comprehensive analysis with custom output directory
python -m src.main --all --output my_complete_analysis
```
**This single command will:**
- Run all 4 predefined scenarios (Low Demand, High Demand, Crisis, Optimization Test)
- Generate scenario comparisons and cross-analysis
- Execute comprehensive metrics demonstration
- Create detailed visualizations and statistical reports
- Produce executive summaries and performance benchmarks
- Save everything in organized output directories

### Predefined Scenarios

#### 1. Low Demand Scenario
```bash
python -m src.main --scenario low_demand
```
- **Duration**: 12 hours
- **Arrival Rate**: 0.3 patients/minute
- **Resources**: 3 doctors, 6 cubicles, 2 nurses
- **Use Case**: Quiet periods, rural practices

#### 2. High Demand Scenario
```bash
python -m src.main --scenario high_demand
```
- **Duration**: 24 hours
- **Arrival Rate**: 0.8 patients/minute
- **Resources**: 6 doctors, 12 cubicles, 3 nurses
- **Use Case**: Busy urban practices, flu season

#### 3. Crisis Scenario
```bash
python -m src.main --scenario crisis
```
- **Duration**: 48 hours
- **Arrival Rate**: 1.2 patients/minute
- **Resources**: 8 doctors, 16 cubicles, 4 nurses
- **Use Case**: Pandemic conditions, major incidents

#### 4. Optimization Test
```bash
python -m src.main --scenario optimization_test
```
- **Duration**: 16 hours
- **Features**: Dynamic resource optimization enabled
- **Use Case**: Testing adaptive resource allocation

### Custom Configuration

#### Manual Parameters
```bash
# Custom duration and arrival rate
python -m src.main --duration 480 --rate 0.6

# Custom staffing levels
python -m src.main --doctors 5 --nurses 3 --cubicles 10

# Specific random seed for reproducibility
python -m src.main --seed 12345
```

#### Configuration File
```bash
# Use custom configuration file
python -m src.main --config my_config.json
```

Example configuration file (`my_config.json`):
```json
{
  "simulation": {
    "duration": 720,
    "arrival_rate": 0.4,
    "random_seed": 42
  },
  "resources": {
    "num_doctors": 4,
    "num_triage_nurses": 2,
    "num_cubicles": 8,
    "num_admission_beds": 20
  },
  "triage_system": {
    "type": "manchester"
  }
}
```

### Analysis and Visualization

#### Generate Comprehensive Analysis
```bash
# Run with detailed analysis and plots
python -m src.main --analyze --output results_folder

# Compare multiple scenarios
python -m src.main --compare low_demand high_demand --output comparison
```

#### Metrics Demo
```bash
# Run comprehensive metrics demonstration
python metrics_demo.py
```

## Understanding the Output

### Priority Distribution (General Healthcare)
- **IMMEDIATE**: 1-2% (true emergencies requiring immediate escalation)
- **VERY_URGENT**: 3-5% (serious acute conditions, 30-minute target)
- **URGENT**: 10-15% (same-day attention required, 2-hour target)
- **STANDARD**: 25-30% (routine problems, 8-hour target)
- **NON_URGENT**: 50-60% (preventive care, wellness visits, 24-hour target)

### Key Metrics
- **Throughput**: Patients processed per hour
- **Wait Times**: Time from arrival to consultation by priority
- **Resource Utilization**: Doctor, nurse, and cubicle usage
- **Compliance**: Adherence to healthcare time targets
- **System Efficiency**: Overall performance indicators

### Generated Files
- **Simulation Results**: JSON files with detailed metrics
- **Visualizations**: PNG charts showing performance analysis
- **Statistical Reports**: Comprehensive analysis with recommendations

## Advanced Usage

### 🎯 Complete Research Analysis
```bash
# Ultimate research command - runs everything
python -m src.main --all --output dissertation_results
```

### Scenario Comparison
```bash
# Compare three scenarios with custom output
python -m src.main --compare low_demand high_demand crisis --output multi_scenario_analysis
```

### Performance Optimization
```bash
# Enable dynamic optimization during simulation
python -m src.main --scenario optimization_test --analyze
```

### Research Mode
```bash
# Long-term study with detailed logging
python -m src.main --duration 2880 --verbose --analyze --output longitudinal_study

# Complete baseline establishment for AI comparison
python -m src.main --all --output baseline_for_ai_comparison
```

## Triage System Details

### Manchester Triage System (Enhanced)
The system uses an enhanced MTS that handles:

#### Emergency Presentations
- **Chest Pain**: Cardiac risk assessment
- **Shortness of Breath**: Respiratory evaluation
- **Neurological**: Stroke/seizure protocols
- **Trauma**: Injury severity assessment

#### Routine Healthcare
- **Wellness Visits**: Preventive care, screenings
- **General Examinations**: Routine check-ups
- **Prenatal Care**: Pregnancy-related visits
- **Follow-up Care**: Chronic condition management

### Fuzzy Logic Implementation
- **Discriminator Evaluation**: Pain, vital signs, symptoms
- **Confidence Scoring**: Uncertainty quantification
- **Vital Signs Modulation**: Conservative escalation for routine care
- **Medical History Integration**: Risk factor consideration

## Troubleshooting

### Common Issues

#### Empty Visualization Charts
```bash
# Ensure sufficient simulation duration for data collection
python -m src.main --duration 240  # At least 4 hours recommended
```

#### Low Resource Utilization
```bash
# Increase arrival rate or reduce resources
python -m src.main --rate 0.8 --doctors 3
```

#### Memory Issues with Long Simulations
```bash
# Reduce logging for very long simulations
python -m src.main --duration 2880 --quiet
```

### Performance Tips
- Use `--quiet` flag for faster execution
- Set appropriate `--seed` for reproducible results
- Monitor system resources during long simulations
- Use `--analyze` only when needed (computationally intensive)

## File Structure

```
src/
├── main.py                 # Main simulation runner
├── core/
│   ├── simulation_engine.py    # Core simulation logic
│   ├── emergency_department.py # Healthcare facility model
│   └── patient_generator.py    # Patient arrival simulation
├── triage/
│   ├── manchester_triage.py    # Enhanced MTS implementation
│   └── base_triage.py         # Triage system interface
├── metrics/
│   ├── metrics_collector.py   # Performance data collection
│   ├── analysis.py           # Statistical analysis
│   └── visualization.py      # Chart generation
└── config/
    └── simulation_parameters.py # Configuration management
```

## Research Applications

### Baseline Studies
```bash
# Establish MTS baseline performance
python -m src.main --scenario high_demand --analyze --output mts_baseline
```

### Comparative Analysis
```bash
# Compare different resource configurations
python -m src.main --compare low_demand high_demand optimization_test
```

### Longitudinal Studies
```bash
# Extended simulation for trend analysis
python -m src.main --duration 4320 --verbose --output week_long_study
```

## Contributing

To extend the system:
1. Add new triage algorithms in `src/triage/`
2. Implement custom scenarios in `simulation_parameters.py`
3. Create additional metrics in `metrics_collector.py`
4. Add visualization types in `visualization.py`

## License

This project is developed for academic research purposes.