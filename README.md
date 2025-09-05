# Hospital Simulation Project

A modular hospital simulation system with proper separation of concerns.

## Project Structure

```
└── src/
    ├── main.py               # Main execution file
    ├── models/
    │   ├── entities/
    │   │   ├── entity.py          # Base Entity class
    │   │   ├── patient.py         # Patient class
    │   │   └── resources/
    │   │       ├── resource.py    # Base Resource class
    │   │       ├── doctor.py      # Doctor resource
    │   │       ├── bed.py         # Bed resource
    │   │       └── mri.py         # MRI resource
    │   ├── actions/
    │   │   └── hospital_action.py # Hospital action enums
    │   ├── simulation/
    │   │   └── snapshot.py        # Simulation snapshot
    │   ├── systems/
    │   │   └── triage_system.py   # Triage system
    │   ├── agents/
    │   │   └── preemption_agent.py # Preemption agent
    │   └── hospital/
    │       └── hospital.py        # Main Hospital class
    ├── services/
    │   └── plotting_service.py    # Plotting utilities
    └── utils/
        └── constants.py           # Global constants
```

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the simulation:
   ```bash
   python -m src.main
   ```

## Features

- **Modular Design**: Each class is in its own file for better maintainability
- **Proper Separation**: Models, services, and utilities are clearly separated
- **Type Hints**: Full type annotation support
- **Documentation**: Comprehensive docstrings for all classes and methods

## Classes Overview

- **Entity**: Base class for all simulation entities
- **Patient**: Represents patients with triage priorities and timing
- **Resource**: Base class for hospital resources (Doctor, Bed, MRI)
- **Hospital**: Main simulation controller
- **TriageSystem**: Handles patient priority assignment
- **PreemptionAgent**: Makes preemption decisions
- **PlottingService**: Visualization utilities
- **Snapshot**: Captures simulation state at specific steps