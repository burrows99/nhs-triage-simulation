# LLM Triage System - Mixture of Agents Architecture

A sophisticated NHS emergency triage system implementing TogetherAI-style mixture of agents architecture with dynamic prompt generation and parallel processing.

## Architecture Overview

### Mixture of Agents (MoA)

Unlike traditional sequential processing, this system uses a **Mixture of Agents** approach where:

- **Multiple agents of each type** work in parallel (ensemble)
- **Intelligent result combination** using voting and averaging
- **Dynamic prompt generation** from triage constants
- **Async processing** for improved performance
- **Clinical consistency validation** across all outputs

### Agent Types

1. **Flowchart Selection Agents** - Determine appropriate MTS flowchart
2. **Symptom Processing Agents** - Extract and quantify clinical discriminators
3. **Fuzzy Scoring Agents** - Apply fuzzy logic for uncertainty handling
4. **Priority Classification Agents** - Assign MTS priority categories
5. **Wait Time Calculator Agents** - Calculate realistic wait times
6. **Numeric Input Processor Agents** - Convert to standardized arrays
7. **JSON Finalizer Agent** - Compile and validate final results

## Key Features

### 🔄 Dynamic Prompt Generation
- Prompts generated from **triage constants** (no hardcoded strings)
- **Flowchart-specific discriminators** automatically included
- **Severity levels** and **categories** pulled from constants
- **Customizable parameters** for different scenarios

### 🚀 Parallel Processing
- **Multiple agents per type** for ensemble decision-making
- **Async processing** with concurrent execution
- **Result combination** using clinical logic (majority vote, most severe, etc.)
- **Fallback mechanisms** if individual agents fail

### 🏥 Clinical Accuracy
- **MTS protocol compliance** with official NHS standards
- **Fuzzy logic** for handling clinical uncertainty
- **Override conditions** for life-threatening presentations
- **Consistency validation** across all outputs

## Quick Start

### 1. Start Ollama with Docker Compose

```bash
# Start Ollama service
docker-compose up -d

# Pull the required model
docker exec ollama-triage ollama pull llama3.1

# Verify service is running
curl http://localhost:11434/api/tags
```

### 2. Basic Usage

```python
from src.triage.llm_triage_system import LLMTriageSystem

# Initialize with 3 agents per type (default)
triage_system = LLMTriageSystem(num_agents_per_type=3)

# Perform triage assessment
result = triage_system.triage_patient(
    presenting_complaint="Severe chest pain with shortness of breath",
    symptoms={'pain': 'severe', 'breathing_difficulty': 'moderate'}
)

print(f"Triage Category: {result['triage_category']}")
print(f"Wait Time: {result['wait_time']}")
print(f"Fuzzy Score: {result['fuzzy_score']}")
```

### 3. Expected Output Format

```json
{
    "flowchart_used": "chest_pain",
    "triage_category": "ORANGE", 
    "wait_time": "10 min",
    "fuzzy_score": 1.2,
    "symptoms_processed": {
        "severe_pain": "severe",
        "crushing_sensation": "moderate",
        "breathing_difficulty": "moderate",
        "sweating": "mild",
        "radiation": "none"
    },
    "numeric_inputs": [0.8, 0.6, 0.8, 0.6, 0.2],
    "priority_score": 2
}
```

## Advanced Usage

### Custom Prompt Generation

```python
# Get the prompt factory
prompt_factory = triage_system.get_prompt_factory()

# Generate custom symptom processing prompt for wounds
custom_prompt = triage_system.create_custom_agent_prompt(
    'symptom_processing',
    flowchart='wounds',
    severity_levels=['none', 'mild', 'moderate', 'severe'],
    additional_discriminators=['contamination', 'depth', 'location']
)
```

### Batch Processing

```python
cases = [
    {
        'presenting_complaint': 'Chest pain',
        'symptoms': {'pain': 'severe'}
    },
    {
        'presenting_complaint': 'Cut on hand',
        'symptoms': {'bleeding': 'minor', 'pain': 'mild'}
    }
]

results = triage_system.process_batch(cases)
```

### Async Processing

```python
import asyncio
from src.triage.llm_triage_system.mixture_of_agents import MixtureOfAgents

async def async_triage():
    moa_system = MixtureOfAgents(num_agents_per_type=2)
    result = await moa_system.triage_patient_async(
        "Severe headache with confusion",
        {'pain': 'severe', 'confusion': 'moderate'}
    )
    return result

# Run async
result = asyncio.run(async_triage())
```

## System Configuration

### Agent Ensemble Size

```python
# Light configuration (faster, less robust)
triage_system = LLMTriageSystem(num_agents_per_type=2)

# Standard configuration (balanced)
triage_system = LLMTriageSystem(num_agents_per_type=3)

# Heavy configuration (slower, more robust)
triage_system = LLMTriageSystem(num_agents_per_type=5)
```

### Model Selection

```python
# Use different Ollama model
triage_system = LLMTriageSystem(
    model="llama3.1:70b",  # Larger model for better accuracy
    num_agents_per_type=2   # Fewer agents due to model size
)
```

### Custom Ollama Endpoint

```python
# Remote Ollama instance
triage_system = LLMTriageSystem(
    ollama_url="http://remote-server:11434",
    model="llama3.1"
)
```

## Result Combination Logic

### Flowchart Selection
- **Majority Vote**: Most common flowchart selected by agents
- **Fallback**: Default to `chest_pain` if no consensus

### Symptom Processing
- **Most Severe**: For each symptom, take the most severe assessment
- **Merge Strategy**: Combine all unique symptoms from all agents

### Fuzzy Scoring
- **Average**: Mean of all valid fuzzy scores
- **Range Validation**: Ensure score stays within 0.0-5.0

### Priority Classification
- **Most Urgent**: Select the highest priority (lowest score)
- **Override Logic**: Life-threatening symptoms always trigger RED

### Wait Time Calculation
- **Majority Vote**: Most common wait time selected
- **MTS Compliance**: Never exceed maximum times for category

### Numeric Processing
- **Element-wise Average**: Average each array position across agents
- **Validation**: Ensure all values remain in 0.0-1.0 range

## Error Handling

### Agent Failures
- **Graceful Degradation**: System continues if some agents fail
- **Fallback Results**: Sensible defaults for failed agents
- **Error Logging**: Detailed logs for debugging

### Connection Issues
- **Retry Logic**: Automatic retries for transient failures
- **Timeout Handling**: Configurable timeouts for LLM calls
- **Offline Mode**: Fallback to rule-based triage if LLM unavailable

## Performance Optimization

### Async Processing
- **Parallel Execution**: All agents of same type run simultaneously
- **Non-blocking**: System remains responsive during processing
- **Resource Management**: Efficient thread pool usage

### Caching
- **Prompt Caching**: Reuse generated prompts for similar cases
- **Result Caching**: Cache results for identical inputs
- **Model Warming**: Keep models loaded for faster response

## Monitoring and Logging

### Processing Logs
```python
# Get detailed processing log
processing_log = triage_system.get_processing_log()
for step in processing_log:
    print(f"{step['step']}: {step['timestamp']}")
```

### System Information
```python
# Get system status
system_info = triage_system.get_agent_info()
print(f"Total Agents: {system_info['total_agents']}")
print(f"Architecture: {system_info['architecture']}")
```

### Health Checks
```python
# Test system connectivity
if triage_system.validate_ollama_connection():
    print("System ready")
else:
    print("Connection issues detected")
```

## Clinical Validation

### MTS Compliance
- **Official Categories**: RED, ORANGE, YELLOW, GREEN, BLUE
- **Wait Time Standards**: Compliant with NHS maximum times
- **Discriminator Logic**: Based on official MTS discriminators

### Safety Features
- **Conservative Bias**: When uncertain, assign higher priority
- **Override Conditions**: Life-threatening symptoms always prioritized
- **Consistency Checks**: Validate results across all agents

### Audit Trail
- **Decision Logging**: Every decision recorded with reasoning
- **Timestamp Tracking**: Full temporal audit trail
- **Agent Attribution**: Track which agents contributed to final result

## Troubleshooting

### Common Issues

1. **Ollama Not Running**
   ```bash
   docker-compose up -d
   docker exec ollama-triage ollama pull llama3.1
   ```

2. **Model Not Found**
   ```bash
   docker exec ollama-triage ollama list
   docker exec ollama-triage ollama pull llama3.1
   ```

3. **Slow Performance**
   - Reduce `num_agents_per_type`
   - Use smaller model (e.g., `llama3.1:8b`)
   - Enable GPU acceleration in Docker Compose

4. **Memory Issues**
   - Increase Docker memory limits
   - Use CPU-only mode (comment out GPU section in docker-compose.yml)

### Debug Mode

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test with simple case
result = triage_system.triage_patient("test complaint")
print(f"Debug result: {result}")
```

## Contributing

When extending the system:

1. **Add new constants** to `triage_constants.py`
2. **Update prompt factory** to use new constants
3. **Test with multiple agent configurations**
4. **Validate clinical accuracy** with medical professionals
5. **Update documentation** with new features

## License

This system is designed for NHS emergency care and should be validated by medical professionals before clinical use.