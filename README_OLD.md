# Dexter v3 - Autonomous Skill Builder

A complete autonomous AI system with LLM collaboration, campaign management, and secure VM-based skill creation.

## Features

- **Campaign Mode**: Long-running autonomous missions with objectives and progress tracking
- **LLM Collaboration**: Multiple LLMs work together, vote on solutions, and refine each other's work
- **Secure Skill Creation**: All code is tested in isolated Hyper-V VM before promotion
- **Real-time UI**: React frontend with live logs, collaboration files, and campaign dashboard
- **AD Authentication**: Enterprise-ready with Active Directory integration

## Architecture

### Backend (`./backend/`)
- **FastAPI** REST API with async support
- **Config-driven** with JSON configuration
- **Campaign Management** for long-term autonomous operation  
- **LLM Orchestration** with immediate broadcast and collaboration
- **VM Sandbox** using Hyper-V PowerShell Direct
- **Memory & Patterns** for learning and context

### Frontend (`./frontend/`)
- **React + Vite** with Tailwind CSS
- **Campaign Dashboard** for tracking objectives and skills
- **Real-time Chat** with team collaboration
- **Live Logs** and collaboration file monitoring
- **Config Editor** for runtime system adjustments

### VM Integration (`./vm_shared/`)
- **Hyper-V VM** with no network access for security
- **PowerShell Direct** for command execution
- **Shared folder** for code transfer and results
- **Automatic testing** before skill promotion

## Setup

### Prerequisites
1. **Windows with Hyper-V** enabled
2. **VM named "DexterVM"** with Python installed
3. **Shared folder** mapped between host and VM
4. **Environment variables** configured

### Environment Variables
```bash
$env:DEXTER_VM_PASSWORD = "YourVMAdminPassword"
$env:OPENAI_API_KEY = "your-openai-key"  # Optional
$env:NEMOTRON_API_KEY = "your-nemotron-key"  # Optional
```

### Quick Start
1. **Backend**:
   ```bash
   cd backend
   pip install fastapi uvicorn httpx pyyaml ldap3 pyjwt psutil python-multipart
   python main.py
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access**: http://localhost:3000

## Usage

### Campaign Mode
1. Click "Campaigns" tab (requires login)
2. Create new campaign with initial request
3. Watch as Dexter and his LLM team collaborate
4. Monitor objectives and skills in real-time
5. Track progress over days/weeks/months

### Normal Mode  
1. Use "Normal" tab for one-off requests
2. See live logs, collaboration files, and chat
3. LLMs work in background while Dexter responds
4. Skills are automatically created and tested

### Configuration
- Use "Config" tab to adjust LLM settings
- Enable/disable different AI models
- Modify voting weights and collaboration rules
- All changes are applied immediately

## Security

- **VM Isolation**: All code execution in air-gapped VM
- **PowerShell Direct**: No network access required
- **Code Testing**: Mandatory VM testing before promotion
- **AD Authentication**: Enterprise user management
- **Shared Folder**: Controlled file transfer only

## Key Workflows

### Skill Creation
1. User makes request
2. LLMs immediately start collaborating
3. Proposals → Peer review → Refinement → Voting
4. Dexter tests winning solution in VM
5. If successful, promotes to skill library
6. If failed, sends feedback to LLMs for retry

### Campaign Management
1. User creates campaign with high-level goal
2. System breaks down into objectives
3. LLMs collaborate to create execution plans
4. Skills are generated and tested as needed
5. Progress tracked automatically
6. Long-running autonomous operation

## Next Steps

- Integrate with your preferred LLM providers
- Set up VM shared folder permissions
- Configure AD/LDAP settings
- Create your first campaign!

## Technical Notes

- **PowerShell Direct** requires VM to be running
- **Shared folder** must be accessible to both host and VM
- **Config changes** reload the entire system
- **Campaign data** persists in SQLite database
- **Skills** are stored as Python files in `/skills/` folder
