# Gliksbot CLI - Local Multi-LLM Interface

A simplified, local-first CLI user interface for Gliksbot featuring five equally distributed panels for LLM slots. This interface eliminates the need for FastAPI/server by operating entirely locally with editable configurations and chat functionality.

## Features

### Five LLM Panels Layout
- **Dexter** (always first) - Main orchestrator and team coordinator
- **Analyst** - Data analysis and strategic planning specialist  
- **Engineer** - Software development and architecture specialist
- **Researcher** - Research and information specialist
- **Specialist** - Configurable domain expert

### Key Capabilities
- **Local-Only Operation**: No FastAPI or server dependency required
- **Live Chat Interface**: Real-time communication with each LLM
- **Editable Configuration**: Per-slot configuration editing and saving
- **Independent Panel Management**: Each panel operates independently with error isolation
- **Skills Folder Integration**: All panels can access local skills in `./skills/` folder
- **Enable/Disable Controls**: Toggle switches for each LLM slot
- **Configuration Persistence**: All settings saved locally to `config.json`

## Quick Start

### Prerequisites
- Python 3.8+
- `textual` library for TUI interface
- `httpx` for HTTP requests to LLM providers

### Installation
```bash
# Install required dependencies
pip install textual httpx

# Run the CLI interface
python3 cli_ui_simple.py
```

### Configuration
1. **API Keys**: Set environment variables for your LLM providers:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export NEMOTRON_API_KEY="your-nemotron-key"
   ```

2. **LLM Configuration**: Use the Config tab in each panel to set:
   - Provider (openai, ollama, anthropic, etc.)
   - Model name (gpt-4, llama3.1:8b, etc.)
   - Endpoint URL
   - API key environment variable name
   - Identity and role descriptions
   - System prompts

## Interface Layout

```
┌─────────────────────────────────┐ ┌─────────────────────────────────┐
│ Dexter                    [ON]  │ │ Analyst                   [OFF] │
│ Chat | Config                   │ │ Chat | Config                   │
├─────────────────────────────────┤ ├─────────────────────────────────┤
│ Chat Area...                    │ │ Chat Area...                    │
│                                 │ │                                 │
│ [Type your message...] [Send]   │ │ [Type your message...] [Send]   │
└─────────────────────────────────┘ └─────────────────────────────────┘

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Engineer   [OFF] │ │ Researcher [OFF] │ │ Specialist [OFF] │
│ Chat | Config    │ │ Chat | Config    │ │ Chat | Config    │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ Chat Area...     │ │ Chat Area...     │ │ Chat Area...     │
│                  │ │                  │ │                  │
│ [Input] [Send]   │ │ [Input] [Send]   │ │ [Input] [Send]   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

## Key Bindings

- **Q** or **Ctrl+C**: Quit the application
- **F1**: Show help information
- **F5**: Refresh configuration from file
- **Tab**: Navigate between UI elements
- **Enter**: Send message in chat input
- **Space**: Toggle switches and buttons

## Panel Features

### Chat Tab
- Real-time conversation with assigned LLM
- Conversation history display
- Message input with Enter-to-send
- Error messages displayed inline
- Auto-scroll to latest messages

### Config Tab
- **Provider**: LLM provider (openai, ollama, anthropic, vultr, nvidia, custom)
- **Model**: Model name specific to the provider
- **Endpoint**: API endpoint URL
- **API Key Env**: Environment variable name containing the API key
- **Identity**: Description of the LLM's identity and expertise
- **Role**: Specific role or job title
- **System Prompt**: Additional instructions and context
- **Save Button**: Persist configuration to `config.json`
- **Status Display**: Shows current state (Ready, Processing, Error, etc.)

## Supported LLM Providers

### OpenAI Compatible
- **OpenAI**: GPT models via official API
- **Vultr**: Vultr Inference API
- **NVIDIA**: Nemotron and other NVIDIA models  
- **Custom**: Any OpenAI-compatible endpoint

### Local Models
- **Ollama**: Local LLM server for open models
- **Self-hosted**: Custom local endpoints

### Other Providers
- **Anthropic**: Claude models via official API

## Configuration Examples

### OpenAI GPT-4
```
Provider: openai
Model: gpt-4o-mini
Endpoint: https://api.openai.com/v1
API Key Env: OPENAI_API_KEY
```

### Local Ollama
```
Provider: ollama
Model: llama3.1:8b
Endpoint: http://localhost:11434
API Key Env: (leave empty for local)
```

### Anthropic Claude
```
Provider: anthropic
Model: claude-3-sonnet-20240229
Endpoint: https://api.anthropic.com/v1
API Key Env: ANTHROPIC_API_KEY
```

## Skills Integration

The CLI interface automatically detects and provides access to skills in the local `./skills/` folder:

1. **Automatic Detection**: Skills are listed and made available to all LLMs
2. **Context Enhancement**: Skill names are added to chat context
3. **Local Access**: All panels can read from the skills folder
4. **No Remote Dependencies**: Skills work entirely locally

## Error Handling

- **Per-Panel Isolation**: Errors in one panel don't affect others
- **Graceful Degradation**: Disabled or misconfigured LLMs show clear error states
- **Retry Logic**: Failed requests can be retried by re-sending messages
- **Configuration Validation**: Invalid configurations are caught and reported

## Local-Only Operation

This CLI interface is designed to work entirely locally without server dependencies:

- **No FastAPI Required**: Direct imports from backend modules
- **Local Configuration**: Settings stored in local `config.json`
- **Environment Variables**: API keys managed through local environment
- **Skills Access**: Direct filesystem access to local skills folder
- **Independent Execution**: No need for web server or background services

## Troubleshooting

### Common Issues

1. **Module Import Errors**:
   ```bash
   # Ensure you're in the project root directory
   cd /path/to/gliksbot
   python3 cli_ui_simple.py
   ```

2. **API Key Errors**:
   ```bash
   # Set environment variables before running
   export OPENAI_API_KEY="your-key"
   python3 cli_ui_simple.py
   ```

3. **Configuration Not Loading**:
   - Check that `config.json` exists in the project root
   - Verify JSON syntax is valid
   - Use F5 to refresh configuration

4. **LLM Connection Errors**:
   - Verify provider and model settings in Config tab
   - Check endpoint URLs are correct
   - Ensure API keys are set and valid
   - For Ollama, make sure the server is running

## Development Notes

### Architecture
- Built with `textual` TUI framework for rich terminal interfaces
- Direct imports from `backend/dexter_brain/` modules
- Modular panel design for easy extension
- Async/await pattern for non-blocking LLM calls

### File Structure
```
cli_ui_simple.py    # Main CLI application
cli_ui.tcss         # CSS styling for interface
config.json         # Configuration file
backend/            # Backend modules (imported directly)
skills/             # Local skills folder
```

### Extending the Interface
- Add new panels by modifying `slot_names` list
- Customize styling in `cli_ui.tcss` file
- Add new provider support in `llm.py` module
- Enhance skills integration with additional context

## Comparison with Web UI

| Feature | CLI Interface | Web UI |
|---------|---------------|---------|
| Server Dependency | None | FastAPI required |
| Installation | Minimal | Full stack setup |
| Resource Usage | Low | Higher |
| Configuration | Local files | API endpoints |
| Skills Access | Direct filesystem | Server-mediated |
| Panel Management | 5 fixed panels | Dynamic resizing |
| Real-time Updates | Terminal-based | WebSocket-based |
| Accessibility | Keyboard-driven | Mouse + keyboard |

The CLI interface is ideal for developers, power users, and server environments where a lightweight, local-first solution is preferred over a full web application.