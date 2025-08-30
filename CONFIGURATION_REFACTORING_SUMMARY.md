# Configuration Refactoring Summary

## Overview
This document summarizes the comprehensive refactoring of configuration management in the NHS Triage Simulation project. All hardcoded configuration values and embedded logic have been moved to a centralized configuration management system.

## Key Changes Made

### 1. Created Centralized Configuration Manager
- **File**: `src/config/config_manager.py`
- **Purpose**: Single source of truth for all configuration settings
- **Features**:
  - Centralized logging configuration
  - Simulation parameters management
  - Resource configuration
  - Service time parameters
  - Manchester Triage System specific settings
  - Visualization and plotting configuration
  - Output path management
  - Validation settings

### 2. Refactored Main Application (`src/main.py`)
**Before**:
```python
# Hardcoded logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('output/simulation.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Multiple hardcoded module log levels
logging.getLogger('matplotlib').setLevel(logging.WARNING)
# ... more hardcoded settings
```

**After**:
```python
# Clean, centralized configuration
from src.config.config_manager import configure_logging, get_simulation_config
configure_logging()
```

### 3. Refactored Emergency Department (`src/entities/emergency_department.py`)
**Before**:
```python
from src.config.parameters import p
# Direct parameter usage
self.doctors = simpy.PriorityResource(env, capacity=p.number_docs)
self.nurses = simpy.Resource(env, capacity=p.number_nurses)
self.cubicles = simpy.Resource(env, capacity=p.ae_cubicles)
```

**After**:
```python
from src.config.config_manager import get_resource_config, get_patient_generation_config
# Configuration-driven resource initialization
resource_config = get_resource_config()
self.doctors = simpy.PriorityResource(env, capacity=resource_config['doctors'])
self.nurses = simpy.Resource(env, capacity=resource_config['nurses'])
self.cubicles = simpy.Resource(env, capacity=resource_config['cubicles'])
```

### 4. Refactored Manchester Triage System (`src/triage_systems/manchester_triage.py`)
**Before**:
```python
# Hardcoded fuzzy logic parameters
self.priority_weights = [0.05, 0.15, 0.3, 0.3, 0.2]
self.membership = {
    'very_low': lambda x: self.trapezoid(x, 0, 0, 0.1, 0.3),
    'low': lambda x: self.triangle(x, 0.2, 0.4, 0.6),
    # ... more hardcoded values
}
```

**After**:
```python
# Configuration-driven fuzzy logic
self.config = get_manchester_triage_config()
self.priority_weights = self.config['priority_weights']
self.membership = self._build_membership_functions()  # Built from config
```

### 5. Refactored Time Utilities (`src/utils/time_utils.py`)
**Before**:
```python
from src.config.parameters import p
def estimate_triage_time():
    return random.lognormvariate(np.log(p.mean_nurse_triage), p.stdev_nurse_triage / p.mean_nurse_triage)
```

**After**:
```python
from src.config.config_manager import get_service_time_config
def estimate_triage_time():
    service_config = get_service_time_config()
    mean_time = service_config['triage']['mean']
    stdev_time = service_config['triage']['stdev']
    return random.lognormvariate(np.log(mean_time), stdev_time / mean_time)
```

### 6. Refactored Visualization Components
**Before**:
```python
# Hardcoded output paths
self.base_dir = f'output/{self.triage_type.get_triage_system_name()}/plots'
os.makedirs(self.base_dir, exist_ok=True)
```

**After**:
```python
# Configuration-driven paths
from src.config.config_manager import get_visualization_config, get_output_paths, create_output_directories
self.viz_config = get_visualization_config()
self.paths = get_output_paths(triage_system_name)
create_output_directories(triage_system_name)
```

## Configuration Categories

### 1. Logging Configuration
- Centralized log level management
- Module-specific log levels
- Configurable output handlers
- Standardized log format

### 2. Simulation Parameters
- Runtime duration and warm-up periods
- Patient arrival rates
- Expected throughput calculations

### 3. Resource Configuration
- Number of doctors, nurses, and cubicles
- Resource capacity management

### 4. Service Time Configuration
- Triage, consultation, and admission wait times
- Mean and standard deviation parameters
- Distribution parameters

### 5. Manchester Triage System Configuration
- Fuzzy logic membership functions
- Priority weights and rules
- Time adjustment factors
- Recommended actions by priority

### 6. Visualization Configuration
- Output directory structure
- Plot formatting and styling
- Color schemes for priorities
- File formats and quality settings

### 7. Patient Generation Configuration
- Severity distributions
- Priority weights
- Admission probabilities
- Default values for error handling

## Benefits Achieved

### 1. **Maintainability**
- Single location for all configuration changes
- No more hunting through multiple files for hardcoded values
- Clear separation of configuration from business logic

### 2. **Flexibility**
- Easy to modify simulation parameters without code changes
- Support for different triage system configurations
- Configurable output paths and formats

### 3. **Consistency**
- Standardized configuration access patterns
- Consistent error handling and validation
- Uniform logging across all modules

### 4. **Testability**
- Configuration can be easily mocked for testing
- Different configurations for different test scenarios
- Isolated configuration logic

### 5. **Extensibility**
- Easy to add new configuration categories
- Support for environment-specific configurations
- Plugin-style architecture for new triage systems

## Verification

The refactored system has been successfully tested:
- ✅ Simulation runs without errors
- ✅ All plots are generated correctly
- ✅ Logging works as expected
- ✅ Configuration values are properly applied
- ✅ Output directories are created automatically

## Usage Examples

### Adding New Configuration
```python
# In config_manager.py
def get_new_feature_config(self) -> Dict[str, Any]:
    return {
        'feature_enabled': True,
        'feature_parameters': {...}
    }

# Convenience function
def get_new_feature_config() -> Dict[str, Any]:
    return config_manager.get_new_feature_config()
```

### Using Configuration in Code
```python
from src.config.config_manager import get_new_feature_config

def some_function():
    config = get_new_feature_config()
    if config['feature_enabled']:
        # Use feature_parameters
        pass
```

## Future Enhancements

1. **Environment-specific configurations** (dev, test, prod)
2. **Configuration validation with schemas**
3. **Runtime configuration updates**
4. **Configuration file support** (YAML, JSON)
5. **Configuration versioning and migration**

This refactoring establishes a solid foundation for maintainable, flexible, and extensible configuration management in the NHS Triage Simulation project.