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
   - Takes 10-30 seconds. NEVER CANCEL.
   - If firewall issues occur, document them as "npm install may fail due to firewall restrictions"

2. **Frontend Build**:
   ```bash
   npm run build
   ```
   - Takes 30-90 seconds. NEVER CANCEL. Set timeout to 3+ minutes.
   - Output goes to `frontend/dist/` directory
   - Always run this before deploying or testing production builds

3. **Backend Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
   - Takes 1-5 minutes depending on network. NEVER CANCEL. Set timeout to 10+ minutes.
   - Note: `python-ldap3` package name is incorrect in requirements.txt, use `ldap3` instead
   - Critical packages: fastapi, uvicorn, pydantic, httpx, python-multipart, aiosqlite, pyjwt, ldap3, cryptography, psutil

### Running the Applications

1. **Frontend Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```
   - Starts on http://localhost:3000
   - Takes 5-10 seconds to start. NEVER CANCEL.
   - Use Ctrl+C to stop

2. **Backend Development Server**:
   ```bash
   cd backend
   python3 main.py
   ```
   - Starts on http://localhost:8000 (default FastAPI port)
   - Requires config.json in project root
   - Environment variables from .env.template may be needed

3. **Demo System** (No dependencies required):
   ```bash
   python3 demo_system.py
   ```
   - Takes 3-10 seconds to complete. NEVER CANCEL.
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

3. **Demo System Validation**:
   - Run `python3 demo_system.py`
   - Verify output shows collaboration simulation
   - Check all phases complete successfully

4. **Backend API Validation** (if dependencies available):
   - Start backend server with `python3 main.py`
   - Access http://localhost:8000/docs (FastAPI docs)
   - Test `/health` endpoint returns OK

### Testing Commands
- No automated test suite currently exists
- Use demo system for functional validation
- Frontend linting: Not configured (no lint script in package.json)
- Backend linting: Not configured (no pytest configuration found)

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

## Common Tasks

### Frequently Used Commands
```bash
# Frontend development
cd frontend && npm install && npm run dev

# Frontend production build  
cd frontend && npm run build

# Backend development (requires dependencies)
cd backend && python3 main.py

# Quick functionality test
python3 demo_system.py
```

### Build Time Expectations
- **npm install**: 10-30 seconds (tested: ~8 seconds)
- **npm run build**: 30-90 seconds (tested: ~1.4 seconds)
- **npm run dev**: Starts in <1 second (tested: ~207ms)
- **pip install**: 1-5 minutes (network dependent)
- **production_setup.ps1**: 10-30 minutes (Windows only)
- **Demo system**: 3-10 seconds (tested: ~2 seconds)

### Troubleshooting Common Issues
1. **npm install fails**: May be firewall/network restrictions - document this limitation
2. **Backend import errors**: Verify Python dependencies installed correctly
3. **Config.json missing**: Copy from repository root, check paths are correct
4. **VM integration fails**: Requires Windows with Hyper-V and VM named "DexterVM"
5. **LDAP auth fails**: Requires domain controller and proper AD configuration

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

The system is designed for enterprise deployment but can run in development mode with mock LLM providers and local authentication.