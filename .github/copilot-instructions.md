# Dexter v3 - Autonomous AI Skill Builder

**CRITICAL DIRECTIVE: Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here. These instructions are comprehensive and tested - follow them exactly.**

Dexter v3 is an autonomous AI system with multi-LLM collaboration, campaign management, and secure VM-based skill creation. The system consists of a React frontend, FastAPI backend, and supports Windows Server deployment with Hyper-V VMs.

## Working Effectively

### Environment Setup and Dependencies
- Install Node.js 20+ for frontend development: `node --version` (should be 20+)
- Install Python 3.12+ for backend: `python3 --version` (should be 3.12+)
- Clone repository to local development environment

### Bootstrap, Build, and Test Repository

1. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   ```
   - Takes 8-10 seconds. NEVER CANCEL.
   - If firewall issues occur, document them as "npm install may fail due to firewall restrictions"

2. **Frontend Build**:
   ```bash
   npm run build
   ```
   - Takes 1-2 seconds. NEVER CANCEL. Set timeout to 3+ minutes.
   - Output goes to `frontend/dist/` directory
   - Always run this before deploying or testing production builds

3. **Backend Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
   - Takes 10-15 seconds depending on network. NEVER CANCEL. Set timeout to 10+ minutes.
   - Critical packages: fastapi, uvicorn, pydantic, httpx, python-multipart, aiosqlite, pyjwt, ldap3, cryptography, psutil

### Running the Applications

1. **Frontend Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```
   - Starts on http://localhost:3000
   - Takes <1 second to start. NEVER CANCEL.
   - Use Ctrl+C to stop

2. **Frontend Preview Server**:
   ```bash
   cd frontend
   npm run preview
   ```
   - Starts on http://localhost:4173
   - Serves production build for testing
   - Requires `npm run build` to be run first

3. **Backend Development Server**:
   ```bash
   cd backend
   DEXTER_CONFIG_FILE="/path/to/config.json" DEXTER_DOWNLOADS_DIR="/tmp/dexter_downloads" python3 main.py
   ```
   - Starts on http://localhost:8080 (default FastAPI port)
   - Requires config.json in project root
   - Environment variables must be set for proper operation

4. **Demo System** (No dependencies required):
   ```bash
   python3 demo_system.py
   ```
   - Takes 2-3 seconds to complete. NEVER CANCEL.
   - Shows LLM collaboration simulation
   - Use this to understand system functionality without full setup

### Production Deployment (Windows Server Only)
```powershell
# Run as Administrator
.\production_setup.ps1 -DomainName "www.gliksbot.com" -VMPassword "YourSecureVMPassword"
```
- Takes 10-30 minutes depending on downloads. NEVER CANCEL. Set timeout to 60+ minutes.
- Installs IIS, creates application pool, configures SSL
- Requires Windows Server 2022 with Hyper-V enabled

## Validation

### Manual Validation Scenarios
After making changes, ALWAYS validate these scenarios:

1. **Frontend Build Validation**:
   - Run `npm run build` successfully
   - Verify `frontend/dist/index.html` exists
   - Check build output shows no errors

2. **Development Server Validation**:
   - Start `npm run dev` 
   - Access http://localhost:3000
   - Verify page loads without console errors
   - Test at least one tab/component loads
   - Confirm chat interface and LLM collaboration slots are visible

3. **Demo System Validation**:
   - Run `python3 demo_system.py`
   - Verify output shows collaboration simulation
   - Check all phases complete successfully
   - Confirm "Dexter v3 represents the future of autonomous AI collaboration!" message appears

4. **Backend API Validation** (if dependencies available):
   - Start backend server with proper environment variables
   - Access http://localhost:8080/docs (FastAPI docs)
   - Test `/health` endpoint returns `{"ok":true,"version":"3.0"}`

### Testing Commands
- No automated test suite currently exists
- Use demo system for functional validation
- Frontend linting: Not configured (no lint script in package.json)
- Backend linting: Not configured (no pytest configuration found)
- pytest is available for backend testing if test files are created

## Configuration and Important Files

### Critical Configuration Files
- **config.json** - Main application configuration (LLM providers, VM settings, domain config)
- **.env.template** - Environment variables template
- **frontend/package.json** - Frontend dependencies and scripts
- **backend/requirements.txt** - Python dependencies
- **backend/main.py** - FastAPI application entry point

### Key Project Structure
```
/
├── frontend/          # React/Vite frontend
│   ├── src/          # React components
│   ├── dist/         # Build output
│   └── package.json  # Dependencies
├── backend/          # FastAPI backend
│   ├── dexter_brain/ # Core modules
│   ├── main.py       # API server
│   └── requirements.txt
├── config.json       # Main configuration
├── production_setup.ps1  # Windows deployment
└── demo_system.py    # Standalone demo
```

### Environment Variables (from .env.template)
Essential for production deployment:
- `DEXTER_VM_PASSWORD` - Hyper-V VM password
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `NEMOTRON_API_KEY` - Nemotron API key (optional)
- `DEXTER_JWT_SECRET` - JWT signing key (production)
- `DEXTER_CONFIG_FILE` - Path to config.json file
- `DEXTER_DOWNLOADS_DIR` - Directory for temporary downloads

## Common Tasks

### Frequently Used Commands
```bash
# Frontend development
cd frontend && npm install && npm run dev

# Frontend production build  
cd frontend && npm run build

# Backend development (requires dependencies)
cd backend && DEXTER_CONFIG_FILE="../config.json" DEXTER_DOWNLOADS_DIR="/tmp/dexter_downloads" python3 main.py

# Quick functionality test
python3 demo_system.py
```

### Build Time Expectations
- **npm install**: 8-10 seconds (tested: 8.4 seconds)
- **npm run build**: 1-2 seconds (tested: 1.6 seconds)
- **npm run dev**: Starts in <1 second (tested: 188ms)
- **pip install**: 10-15 seconds (tested: 12.3 seconds)
- **production_setup.ps1**: 10-30 minutes (Windows only)
- **Demo system**: 2-3 seconds (tested: 2.2 seconds)

### Troubleshooting Common Issues
1. **npm install fails**: May be firewall/network restrictions - document this limitation
2. **Backend import errors**: Verify Python dependencies installed correctly
3. **Config.json missing**: Copy from repository root, check paths are correct
4. **Backend startup fails**: Ensure environment variables `DEXTER_CONFIG_FILE` and `DEXTER_DOWNLOADS_DIR` are set
5. **VM integration fails**: Requires Windows with Hyper-V and VM named "DexterVM"
6. **LDAP auth fails**: Requires domain controller and proper AD configuration

## LLM Provider Integration

### Supported Providers (config.json)
- **Ollama**: Local LLM server (default: http://localhost:11434)
- **OpenAI**: GPT models via API key
- **Nemotron**: NVIDIA API endpoint

### Testing LLM Connections
```bash
cd backend
# Test basic imports and config loading
python3 -c "from dexter_brain.config import Config; c = Config.load('../config.json'); print('Config loaded successfully')"

# Test LLM module (requires dependencies)
python3 -c "from dexter_brain.llm import test_llm_call; import asyncio; asyncio.run(test_llm_call())"
```

## Security and VM Integration

### Hyper-V VM Requirements (Windows only)
- VM named "DexterVM" with Python installed
- Shared folder mapped between host and VM
- VM credentials configured in environment variables
- Used for secure skill testing and code execution

### Authentication
- Active Directory/LDAP integration for enterprise deployment
- JWT tokens for session management
- Domain authentication configured in config.json

## Development Workflow

When making changes:
1. **Always run demo system first** to verify core functionality
2. **Test frontend build** with `npm run build` 
3. **Validate development servers** start correctly
4. **Check configuration files** for syntax errors
5. **Document any new environment requirements**

### Validation Workflow
After any code changes, run this complete validation sequence:
```bash
# 1. Test demo system
python3 demo_system.py

# 2. Test frontend build
cd frontend && npm run build

# 3. Test frontend dev server
npm run dev &
# Access http://localhost:3000 in browser
# Ctrl+C to stop

# 4. Test backend (if dependencies available)
cd ../backend
DEXTER_CONFIG_FILE="../config.json" DEXTER_DOWNLOADS_DIR="/tmp/dexter_downloads" python3 main.py &
# Test http://localhost:8080/health
# Ctrl+C to stop
```

## System Architecture Overview

### Frontend (`frontend/`)
- **React + Vite** with Tailwind CSS
- **Campaign Dashboard** for tracking objectives and skills
- **Real-time Chat** with team collaboration
- **Live Logs** and collaboration file monitoring
- **Config Editor** for runtime system adjustments

### Backend (`backend/`)
- **FastAPI** REST API with async support
- **Config-driven** with JSON configuration
- **Campaign Management** for long-term autonomous operation  
- **LLM Orchestration** with immediate broadcast and collaboration
- **VM Sandbox** using Hyper-V PowerShell Direct
- **Memory & Patterns** for learning and context

### VM Integration (`vm_shared/`)
- **Hyper-V VM** with no network access for security
- **PowerShell Direct** for command execution
- **Shared folder** for code transfer and results
- **Automatic testing** before skill promotion

The system is designed for enterprise deployment but can run in development mode with mock LLM providers and local authentication.