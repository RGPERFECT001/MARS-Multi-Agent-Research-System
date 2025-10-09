# Multi-Agent Research System

A sophisticated multi-agent research system built with LangGraph, Agent Swarm, and Google AI Studio Gemini API. This system implements a collaborative workflow where specialized agents work together to produce comprehensive research reports.

## System Architecture

The system follows the flowchart design with four specialized agents:

1. **Planner Agent**: Creates comprehensive research plans
2. **Researcher Agent**: Gathers and synthesizes information
3. **Writer Agent**: Creates detailed reports based on research
4. **Critic Agent**: Evaluates reports and provides feedback

### Workflow Flow

```
User Topic → Planner Agent → Researcher Agent → Writer Agent → Critic Agent
                                                      ↑           ↓
                                                 (revision)   (research)
                                                      ↑           ↓
                                                 Writer Agent ← Researcher Agent
                                                      ↓
                                               Final Report
```

## Features

- **Multi-Agent Collaboration**: Specialized agents working together
- **Multi-Model Support**: Automatic fallback between multiple AI models
- **Rate Limit Handling**: Intelligent switching when models hit rate limits
- **Iterative Refinement**: Feedback loops for continuous improvement
- **Quality Control**: Built-in critique and approval system
- **Comprehensive Research**: Systematic approach to information gathering
- **Professional Reports**: Well-structured, detailed output
- **Configurable Limits**: Prevents infinite loops with iteration limits
- **Model Status Tracking**: Monitor and manage model availability

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd multi-agent-research-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env_example.txt .env
# Edit .env and add your Google API key
```

4. Validate configuration:
```bash
python validate_config.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Basic configuration
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# Multi-model configuration file path
MODELS_CONFIG_FILE=models_config.json

# Optional: Multi-model fallback settings
MAX_MODEL_RETRIES=3
RATE_LIMIT_RETRY_DELAY=60
MODEL_SWITCH_DELAY=5
```

### Models Configuration

The system uses a separate JSON file for model configuration (`models_config.json`):

```json
[
    {
        "name": "gemini-2.5-flash",
        "api_key": "GOOGLE_API_KEY",
        "temperature": 0.7,
        "max_tokens": 10000,
        "priority": 1,
        "description": "Fast and efficient model"
    },
    {
        "name": "gemini-2.5-pro",
        "api_key": "GOOGLE_API_KEY",
        "temperature": 0.7,
        "max_tokens": 10000,
        "priority": 2,
        "description": "Most capable model"
    }
]
```

### Multi-Model Configuration

The system supports multiple AI models with automatic fallback:

- **Priority System**: Models are used in priority order (1 = highest priority)
- **Rate Limit Handling**: Automatically switches to next model when rate limits hit
- **Error Recovery**: Models are temporarily disabled after repeated failures
- **Status Tracking**: Monitor model availability and usage
- **Flexible Configuration**: Each model can have different settings

### Configuration Options

Edit `config.py` to customize:

- `MAX_ITERATIONS`: Maximum workflow iterations (default: 10)
- `MAX_RESEARCH_ATTEMPTS`: Maximum research attempts (default: 3)
- `MAX_WRITING_ATTEMPTS`: Maximum writing attempts (default: 3)
- `DEFAULT_SEARCH_DEPTH`: Research depth level (default: 3)
- `MAX_MODEL_RETRIES`: Maximum retries before marking model unavailable (default: 3)
- `RATE_LIMIT_RETRY_DELAY`: Delay before retrying rate-limited models (default: 60s)
- `MODEL_SWITCH_DELAY`: Delay when switching between models (default: 5s)

## Usage

### Basic Usage

```bash
python main.py "Your research topic here"
```

### Advanced Usage

```bash
# With verbose logging
python main.py "Artificial Intelligence in Healthcare" --verbose

# With streaming progress updates
python main.py "Climate Change Solutions" --stream

# Save to specific output file
python main.py "Quantum Computing" --output my_report.json

# Combine options
python main.py "Space Exploration" --verbose --stream --output space_report.json

# Check model status
python main.py --status

# Reset all models to available
python main.py --reset-models
```

### Programmatic Usage

```python
from workflow import MultiAgentResearchWorkflow
from gemini_client import gemini_client

# Initialize workflow
workflow = MultiAgentResearchWorkflow()

# Check model status
status = gemini_client.get_model_status()
print("Model status:", status)

# Run research
result = workflow.run("Your research topic")

# Access results
print(result['final_report'])
print(result['research_plan'])
print(result['synthesized_data'])

# Reset models if needed
gemini_client.reset_all_models()
```

## HTTP API (FastAPI)

This repository includes a small FastAPI wrapper (`api.py`) which exposes endpoints useful for building a chatbot frontend.

Run the server with uvicorn:

```powershell
python -m api
# or
uvicorn api:app --host 0.0.0.0 --port 8000
```

Endpoints:

- POST /chat
    - Body: {"session_id": "optional-session-id", "message": "your message"}
    - Returns: {"session_id": "<id>", "reply": "assistant reply", "refusal": bool}

- POST /research
    - Body: {"session_id": "optional", "topic": "research topic", "stream": false}
    - If stream=true the endpoint streams Server-Sent Events (SSE) with progress and final result.

- GET /status
    - Returns model status from the Gemini client.

Example chat request (PowerShell/curl):

```powershell
curl -X POST "http://127.0.0.1:8000/chat" -H "Content-Type: application/json" -d '{"message":"transformer neural networks"}'
```


## Output Structure

The system generates comprehensive reports with the following structure:

### Report Format
- **Executive Summary**: High-level overview
- **Introduction**: Background and context
- **Main Findings**: Detailed analysis organized by themes
- **Analysis and Insights**: Deeper examination of findings
- **Conclusions**: Summary and future implications

### Output Files
- **Reports**: Saved in `outputs/reports/` directory
- **Logs**: System logs in `outputs/logs/` directory
- **JSON Format**: Complete research data with metadata

## Agent Details

### Planner Agent
- Creates systematic research plans
- Identifies key questions and sub-topics
- Defines search strategies and expected sources
- Sets research depth requirements

### Researcher Agent
- Gathers information from multiple perspectives
- Synthesizes findings into coherent insights
- Identifies conflicting information
- Evaluates data quality and reliability

### Writer Agent
- Creates comprehensive, well-structured reports
- Maintains professional tone and clarity
- Supports claims with evidence
- Ensures balanced coverage of topics

### Critic Agent
- Evaluates report quality and completeness
- Provides constructive feedback
- Makes approval decisions
- Routes reports for revision or additional research

## Multi-Model Features

### Automatic Fallback
- **Rate Limit Detection**: Automatically detects when models hit rate limits
- **Smart Switching**: Seamlessly switches to the next available model
- **Priority Management**: Uses models in priority order (1 = highest priority)
- **Error Recovery**: Temporarily disables failed models and retries later

### Model Management
- **Status Tracking**: Real-time monitoring of model availability
- **Usage Statistics**: Track which models are being used most
- **Manual Reset**: Reset all models to available status when needed
- **Configuration Flexibility**: Each model can have different settings

### Benefits
- **Increased Reliability**: System continues working even if one model fails
- **Better Performance**: Uses fastest available models first
- **Cost Optimization**: Can use cheaper models as fallbacks
- **Scalability**: Easy to add new models or providers

## Quality Control

The system includes multiple quality control mechanisms:

1. **Iteration Limits**: Prevents infinite loops
2. **Attempt Limits**: Controls research and writing attempts
3. **Critique System**: Comprehensive evaluation of outputs
4. **Fallback Mechanisms**: Graceful handling of errors
5. **Progress Tracking**: Monitors workflow progress
6. **Multi-Model Reliability**: Automatic model switching for continuity

## Error Handling

The system includes robust error handling:

- **Graceful Degradation**: Continues operation with fallback data
- **Comprehensive Logging**: Detailed logs for debugging
- **User Feedback**: Clear error messages and progress updates
- **Recovery Mechanisms**: Automatic retry and fallback strategies

## Customization

### Adding New Agents
1. Create agent class in `agents/` directory
2. Implement required methods
3. Add to workflow in `workflow.py`
4. Update state model if needed

### Modifying Workflow
1. Edit `workflow.py` to change agent interactions
2. Update state transitions
3. Modify decision logic
4. Test with various topics

### Customizing Prompts
1. Edit agent-specific prompts in agent files
2. Modify system prompts for different behaviors
3. Adjust temperature and generation parameters
4. Test with different prompt variations

## Performance Considerations

- **API Limits**: Respect Google Gemini API rate limits
- **Token Usage**: Monitor token consumption for cost control
- **Processing Time**: Iterative workflow may take several minutes
- **Memory Usage**: Large reports may require significant memory

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure `GOOGLE_API_KEY` is set correctly
2. **Import Errors**: Check that all dependencies are installed
3. **Permission Errors**: Ensure write access to output directories
4. **Timeout Issues**: Increase timeout settings in configuration

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python main.py "Your topic" --verbose
```

Check logs in `outputs/logs/research_system.log` for detailed information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue with detailed information
4. Include system configuration and error messages

## Future Enhancements

Potential improvements:
- Web interface for easier interaction
- Additional research sources and APIs
- Custom agent configurations
- Export to different formats (PDF, Word, etc.)
- Integration with external databases
- Real-time collaboration features
