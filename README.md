# Hospital Simulation with Preemptive Resource Management

A comprehensive SimPy-based hospital simulation implementing intelligent resource allocation, Manchester Triage System (MTS), and AI-driven preemption decisions for optimal patient care.

## Overview

This simulation models a hospital emergency department with:
- **Preemptive Resources**: Doctors and MRI machines that can interrupt current services for higher priority patients
- **Non-preemptive Resources**: Hospital beds where patients cannot be displaced once admitted
- **Intelligent Triage**: Manchester Triage System implementation for priority assignment
- **AI-Driven Preemption**: Mock AI service for optimal preemption decisions
- **Comprehensive Metrics**: Real-time performance tracking and analysis

## Features

### Core Simulation Components
- **Patient Flow**: Log-normal arrival patterns based on NHS data
- **Resource Management**: Doctors, MRI machines, beds, and triage nurses
- **Priority System**: 5-level MTS priority classification
- **Preemption Logic**: Intelligent interruption of lower priority services
- **Metrics Collection**: Wait times, resource utilization, and system performance

### Key Capabilities
- **Realistic Time Generation**: NHS-based service time distributions
- **Strict Validation**: Comprehensive data integrity checks throughout
- **Modular Design**: Separate classes for each entity and service
- **Type Safety**: Full type annotations with strict checking
- **Performance Analysis**: Statistical analysis and visualization

## Project Structure

```
dissertation/
├── entities/                 # Core hospital entities
│   ├── patient.py           # Patient class with metrics tracking
│   ├── doctor.py            # Doctor resource (preemptive)
│   ├── mri_machine.py       # MRI machine resource (preemptive)
│   ├── bed.py               # Hospital bed resource (non-preemptive)
│   ├── triage_nurse.py      # Triage nurse with MTS implementation
│   ├── hospital.py          # Main hospital orchestrator
│   └── __init__.py
├── services/                # Supporting services
│   ├── time_service.py      # NHS-based time generation
│   ├── preemption_agent.py  # AI-driven preemption decisions
│   ├── metrics_service.py   # Performance analysis and visualization
│   └── __init__.py
├── enums/                   # Type-safe enumerations
│   ├── priority.py          # MTS priority levels
│   ├── resource_type.py     # Hospital resource types
│   ├── patient_status.py    # Patient status tracking
│   └── __init__.py
├── main_simulation.py       # Main simulation orchestrator
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd dissertation
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Simulation

Run a standard 8-hour simulation:
```bash
python main_simulation.py
```

### Custom Configuration

Customize hospital resources and simulation parameters:
```bash
python main_simulation.py \
    --name "City General Hospital" \
    --doctors 5 \
    --mri 3 \
    --beds 20 \
    --nurses 3 \
    --duration 720 \
    --seed 42
```

### Command Line Options

- `--name`: Hospital name (default: "General Hospital")
- `--doctors`: Number of doctors (default: 3)
- `--mri`: Number of MRI machines (default: 2)
- `--beds`: Number of beds (default: 10)
- `--nurses`: Number of triage nurses (default: 2)
- `--duration`: Simulation duration in minutes (default: 480)
- `--seed`: Random seed for reproducibility
- `--verbose`: Enable detailed logging

## Key Components

### Manchester Triage System (MTS)

Implements 5-level priority classification:
- **Priority 1 (Red)**: Immediate - life-threatening conditions
- **Priority 2 (Orange)**: Very urgent - potentially life-threatening
- **Priority 3 (Yellow)**: Urgent - serious conditions
- **Priority 4 (Green)**: Standard - less urgent conditions
- **Priority 5 (Blue)**: Non-urgent - minor conditions

### Preemption Agent

AI-driven decision making for resource preemption:
- Analyzes patient priority and system state
- Makes confidence-scored recommendations
- Considers system-wide impact
- Uses mock API for demonstration (ready for ML integration)

### Time Service

Realistic time generation based on NHS data:
- Log-normal patient arrivals
- Priority-adjusted service times
- Resource-specific time distributions
- Statistical validation and bounds checking

### Metrics Service

Comprehensive performance analysis:
- Wait time distributions by priority
- Resource utilization patterns
- System performance trends
- Statistical summaries and visualizations

## Output and Analysis

### Generated Reports

The simulation generates:
1. **Console Summary**: Key performance indicators
2. **Visualization Plots**: Wait times, utilization, system performance
3. **CSV Data Exports**: Detailed data for further analysis
4. **Performance Metrics**: Statistical summaries

### Key Metrics

- **Wait Times**: Mean, median, 95th percentile by priority
- **Resource Utilization**: Efficiency rates for all resource types
- **System Load**: Overall capacity utilization
- **Preemption Statistics**: Frequency and impact analysis
- **Patient Throughput**: Processing rates and discharge patterns

## Design Principles

### Object-Oriented Architecture
- **Single Responsibility**: Each class has a focused purpose
- **Strict Validation**: Comprehensive data integrity checks
- **Type Safety**: Full type annotations throughout
- **Immutable State**: Operations state snapshots for consistency

### NHS-Based Modeling
- **Evidence-Based**: Time distributions from NHS operational data
- **Clinical Protocols**: MTS implementation following NHS guidelines
- **Realistic Constraints**: Resource limitations and operational rules
- **Performance Standards**: Metrics aligned with NHS indicators

### Extensibility
- **Modular Design**: Easy to add new resource types or policies
- **Plugin Architecture**: Services can be easily replaced or extended
- **Configuration Driven**: Parameters externalized for easy modification
- **API Ready**: Mock services ready for real AI/ML integration

## Technical Implementation

### Dependencies

- **SimPy**: Discrete event simulation framework
- **NumPy**: Statistical distributions and numerical operations
- **Pandas**: Data manipulation and analysis
- **Matplotlib/Seaborn**: Visualization and plotting
- **Pydantic**: Data validation and settings management

### Performance Considerations

- **Memory Management**: Limited history storage to prevent memory bloat
- **Efficient Queuing**: Priority-based resource allocation
- **Lazy Evaluation**: Metrics calculated on-demand
- **Batch Processing**: Periodic metrics collection

## Validation and Testing

### Data Integrity
- **Input Validation**: All parameters validated at entry
- **State Consistency**: Operations state immutability
- **Temporal Validation**: Time-based constraint checking
- **Resource Constraints**: Capacity and availability validation

### Statistical Validation
- **Distribution Bounds**: Realistic time generation limits
- **Priority Consistency**: MTS guideline compliance
- **Performance Metrics**: NHS benchmark alignment
- **System Stability**: Resource utilization bounds

## Future Enhancements

### AI/ML Integration
- Replace mock preemption agent with real ML models
- Historical outcome analysis for learning
- Predictive patient flow modeling
- Dynamic resource allocation optimization

### Extended Modeling
- Additional resource types (labs, pharmacy, etc.)
- Multi-department patient flows
- Staff scheduling and shift patterns
- Equipment maintenance and downtime

### Advanced Analytics
- Real-time dashboard integration
- Comparative scenario analysis
- Cost-effectiveness modeling
- Patient satisfaction metrics

## References

1. **NHS England**: Emergency Care Data Set and Performance Standards
2. **Manchester Triage Group**: Emergency Triage Guidelines (3rd Edition)
3. **SimPy Documentation**: Discrete Event Simulation in Python
4. **Healthcare Operations Research**: Queuing Theory Applications
5. **NHS Operational Research**: Capacity Planning and Patient Flow

## License

This project is developed for academic research purposes. Please refer to your institution's guidelines for usage and distribution.

## Contact

For questions, suggestions, or collaboration opportunities, please contact the development team.

---

**Note**: This simulation is designed for research and educational purposes. Any clinical or operational decisions should be validated with appropriate healthcare professionals and regulatory bodies.