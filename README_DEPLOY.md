# Dexter v3 - Quick Deployment Guide

Welcome to Dexter v3, an autonomous AI system with multi-LLM collaboration capabilities! This guide will help you get the system running quickly on any platform.

## 🚀 Quick Start

### One-Click Installation

**For Linux/macOS:**
```bash
chmod +x install.sh && ./install.sh
```

**For Windows:**
```cmd
install.bat
```

**Then launch the system:**

**Linux/macOS:**
```bash
./launch.sh
```

**Windows:**
```cmd
launch.bat
```

That's it! The system will be available at:
- 🌐 **Web Interface**: http://localhost:3000
- 🔧 **API Backend**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs

## 📋 System Requirements

### Minimum Requirements
- **Python 3.8+** (Required)
- **Node.js 16+** (Required for web interface)
- **4GB RAM** (Recommended: 8GB+)
- **2GB free disk space**

### Optional Components
- **Docker** (For secure sandbox mode)
- **Git** (For version control)

## 🛠️ Manual Installation

If the automatic installer doesn't work, follow these steps:

### 1. Install Dependencies

**Backend (Python):**
```bash
pip install -r requirements.txt
```

**Frontend (Node.js):**
```bash
cd frontend
npm install
npm run build
cd ..
```

### 2. Start Services

**Backend:**
```bash
cd backend
python main.py
```

**Frontend (Development):**
```bash
cd frontend
npm run dev
```

## 🧪 Testing Without Installation

You can test the core system functionality without installing dependencies:

```bash
python demo_system.py
```

This runs a complete simulation of the multi-LLM collaboration system.

## 🐳 Docker Sandbox

For secure code execution, the system includes a Docker sandbox:

```bash
# Build the sandbox (done automatically by installer)
docker build -f Dockerfile.sandbox -t dexter-sandbox .

# The sandbox is used automatically when available
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
cp .env.template .env
```

Edit `.env` with your API keys (optional for basic functionality):

```env
# LLM Provider API Keys (Optional)
OPENAI_API_KEY=your_openai_key_here
NEMOTRON_API_KEY=your_nemotron_key_here

# System Configuration
DEXTER_VM_PASSWORD=your_vm_password
DEXTER_JWT_SECRET=your_secret_key
```

### Main Configuration

Edit `config.json` to configure LLM providers and system settings.

## 🏭 Production Deployment

For production deployment on Windows Server:

```powershell
# Run as Administrator
.\production_setup.ps1 -DomainName "your-domain.com" -VMPassword "SecurePassword"
```

See `DEPLOYMENT.md` for complete production deployment instructions.

## 📁 Project Structure

```
dexter-v3/
├── 📱 frontend/          # React web interface
├── 🔧 backend/           # FastAPI backend
├── 🛠️ install.sh         # Linux/Mac installer
├── 🛠️ install.bat        # Windows installer  
├── 🚀 launch.sh          # Linux/Mac launcher
├── 🚀 launch.bat         # Windows launcher
├── 🐳 Dockerfile.sandbox # Secure testing environment
├── 📋 requirements.txt   # Python dependencies
├── ⚙️ config.json        # System configuration
└── 📚 README_DEPLOY.md   # This file
```

## 🔧 Troubleshooting

### Common Issues

**Python not found:**
- Install Python 3.8+ from https://python.org
- Make sure Python is in your PATH

**Node.js not found:**
- Install Node.js from https://nodejs.org
- Restart your terminal after installation

**Permission denied on scripts:**
```bash
chmod +x install.sh launch.sh
```

**Port already in use:**
- Default ports: 3000 (frontend), 8000 (backend)
- Kill existing processes or change ports in configuration

### Logs

Check logs in the `logs/` directory:
- `backend.log` - Backend server logs
- `frontend.log` - Frontend development server logs

### Getting Help

1. Check the logs for error messages
2. Run `python demo_system.py` to test core functionality
3. Visit http://localhost:8000/docs for API documentation
4. Review `DEPLOYMENT.md` for detailed deployment instructions

## 🎯 Features

- **Multi-LLM Collaboration**: Democratic voting system between AI models
- **Autonomous Campaign Management**: Automatic objective tracking and progress
- **Secure Code Execution**: Docker-based sandbox for testing AI-generated code
- **Real-time Web Interface**: Live monitoring of AI collaboration
- **Enterprise Integration**: LDAP/AD authentication and SSL support
- **Cross-platform Support**: Works on Windows, Linux, and macOS

## 📚 Next Steps

1. **Configure LLM providers** in `config.json`
2. **Set up API keys** in `.env` for external LLM services
3. **Explore the web interface** at http://localhost:3000
4. **Read the documentation** in the repository
5. **Create your first AI collaboration** through the web interface

Enjoy using Dexter v3! 🤖✨