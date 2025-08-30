# NHS Triage Simulator

A simulation of an NHS emergency department triage system using SimPy. This project models patient flow through an emergency department, including triage, consultation, and potential admission processes.

## Project Structure

```
src/
  ├── __init__.py
  ├── main.py                # Main simulation runner
  ├── core/                  # Core simulation components
  │   ├── __init__.py
  │   ├── emergency_department.py  # ED simulation logic
  │   ├── patient.py              # Patient class
  │   └── parameters.py           # Simulation parameters
  ├── utils/                 # Utility functions
  │   ├── __init__.py
  │   └── time_utils.py           # Time estimation functions
  └── visualization/         # Visualization components
      ├── __init__.py
      ├── metrics.py              # Metrics collection and analysis
      └── plots.py                # Data visualization functions
```

## Features

- NHS Manchester Triage System simulation (5 priority levels)
- Poisson arrival process following queuing theory principles
- Realistic time distributions for triage and consultation
- Priority-based doctor allocation
- Comprehensive metrics collection and analysis
- Data visualization of wait times and patient flow
- Statistical verification of Poisson arrival distribution
- Docker containerization with hot reload for development

## Running the Simulation

### Using Docker Compose (Recommended)

```bash
docker-compose up --build
```

This will build and run the simulation in a Docker container with hot reload enabled. Any changes to the Python files will automatically trigger a re-run of the simulation.

### Running Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the simulation:

```bash
python -m src.main
```

## Simulation Parameters

The simulation parameters can be modified in `src/core/parameters.py`. Key parameters include:

- Number of nurses and doctors
- Number of cubicles
- Mean and standard deviation for triage and consultation times
- Simulation duration
- Patient inter-arrival time (`inter` parameter)

## Queueing Theory Implementation

This simulation implements a Poisson arrival process, a fundamental concept in queueing theory:

- Patient arrivals follow a Poisson distribution with rate parameter λ = 1/`inter`
- Inter-arrival times follow an exponential distribution with mean = `inter`
- The `generate_interarrival_time()` function in `src/utils/time_utils.py` generates these times
- Statistical verification is performed using the `verify_poisson_arrivals()` function in `src/visualization/plots.py`
- Verification includes:
  - Histogram of arrivals per time interval compared to theoretical Poisson distribution
  - Histogram of inter-arrival times compared to theoretical exponential distribution
  - Kolmogorov-Smirnov test for exponential distribution fit

## Output

The simulation produces:

1. Console output with summary statistics including:
   - Total patients processed
   - Admission rate
   - Average wait times for triage and consultation
   - Average total time in system
   - Average wait times by priority level
   - Statistical verification of Poisson arrival process

2. Visualizations saved as:
   - `simulation_results.png` - showing wait times by priority and total time distribution
   - `priority_distribution.png` - showing the distribution of patient priorities
   - `poisson_verification.png` - verifying that patient arrivals follow a Poisson distribution