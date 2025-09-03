# GliksBot - Advanced AI Collaboration Platform

GliksBot is a sophisticated AI collaboration platform featuring Dexter, an elite AI orchestrator, leading a team of specialized AI models to accomplish complex tasks and generate income opportunities.

## 🚀 Quick Start Deployment

**Ready to deploy? Use our one-click installers:**

**Linux/macOS:**
```bash
chmod +x install.sh && ./install.sh && ./launch.sh
```

**Windows:**
```cmd
install.bat && launch.bat
```

**Then open:** http://localhost:3000

📚 **For detailed deployment instructions, see [README_DEPLOY.md](README_DEPLOY.md)**

## 🚀 Recent Major Updates

### Enhanced Model Configuration System
- **8 Model Slots**: Expanded from 2 to 8 configurable AI model slots
- **Local & Remote Models**: Support for both local (Ollama) and cloud-based models
- **Complete Configurability**: Full control over all model parameters including temperature, top_p, max_tokens, penalties, and more
- **Dexter Leadership**: Dexter remains the primary orchestrator with enhanced team management capabilities

### Robust Collaboration System
- **Real-time File Sharing**: AI models can read and write collaboration files
- **Cross-Model Communication**: Models can see each other's work and collaborate effectively
- **Live Collaboration Viewer**: Monitor AI team activity in real-time through the UI
- **Persistent Collaboration History**: All AI interactions are logged and accessible

### Enhanced User Interface
- **Comprehensive Models Tab**: View and configure every aspect of your AI team
- **Advanced Normal Tab**: Enhanced chat interface with live collaboration monitoring
- **File Content Viewer**: Read collaboration files directly in the UI
- **Real-time Status**: Live indicators showing which models are active and working

## 🎯 Key Features

### AI Team Members
1. **Dexter** - Chief Orchestrator & Executive Officer
2. **Analyst** - Data Analysis & Strategic Planning
3. **Engineer** - Senior Software Engineer & Architect
4. **Researcher** - Information Research & Analysis Specialist
5. **Creative** - Creative Director & Innovation Specialist
6. **Specialist1** - Configurable Domain Expert
7. **Specialist2** - Secondary Domain Expert
8. **Validator** - Quality Assurance & Risk Assessment

### Model Flexibility
- **Multiple Providers**: OpenAI, Anthropic, Ollama, OpenAI-compatible APIs
- **Local Models**: Run models locally using Ollama (Llama, Mistral, CodeLlama, etc.)
- **Hybrid Deployments**: Mix local and cloud models based on your needs
- **Full Parameter Control**: Temperature, top_p, max_tokens, frequency/presence penalties

### Advanced Collaboration
- **File-Based Communication**: Models share insights through structured files
- **Voting Systems**: Democratic decision-making among AI team members
- **Real-time Monitoring**: Watch your AI team collaborate in real-time
- **Persistent Knowledge**: All collaboration is saved and searchable

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **Git**

### Quick Start
1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd gliksbot
   ```

2. **Run the startup script:**
   ```powershell
   .\start.ps1
   ```

This script will:
- Install all dependencies
- Create collaboration directories
- Start both backend and frontend servers
- Open the application in your browser

### Manual Setup

#### Backend Setup
```powershell
cd backend
pip install -r requirements.txt
python main.py
```

#### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

### Environment Variables
Create a `.env` file or set environment variables:

```env
# API Keys (required for respective models)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
NEMOTRON_API_KEY=your_nvidia_key_here
OLLAMAKEY=your_ollama_key_here  # if using cloud Ollama

# Optional Configuration
DEXTER_CONFIG_FILE=m:/gliksbot/config.json
DEXTER_DOWNLOADS_DIR=m:/gliksbot/downloads
```

## 🔧 Configuration

### Model Configuration
Each model can be configured with:

```json
{
  "enabled": true,
  "provider": "openai|ollama|anthropic|OpenAI",
  "endpoint": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "api_key_env": "OPENAI_API_KEY",
  "local_model": false,
  "local_endpoint": "http://localhost:11434",
  "identity": "Model's core identity and capabilities",
  "role": "Specific role in the team",
  "prompt": "System prompt defining behavior",
  "params": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2048,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
  },
  "collaboration_enabled": true,
  "collaboration_directory": "./collaboration/modelname"
}
```

### Local Model Setup
To use local models with Ollama:

1. **Install Ollama:**
   ```powershell
   # Download from https://ollama.ai
   ```

2. **Pull models:**
   ```bash
   ollama pull llama3.1:8b
   ollama pull codellama:13b
   ollama pull mistral:7b
   ```

3. **Configure in UI:**
   - Set provider to "ollama"
   - Enable "Local Model"
   - Set endpoint to "http://localhost:11434"

## 🎮 Usage

### Accessing the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs

### Default Login
- **Username**: `admin`
- **Password**: `gliksbot123`

### Using the Models Tab
1. Navigate to the Models tab
2. Select any model to view/edit configuration
3. Click "Edit" to modify settings
4. Save changes to apply immediately

### Using the Normal Tab
1. Navigate to the Normal tab
2. Type your request in the chat input
3. Watch the collaboration panel to see AI team activity
4. Click on models to view their collaboration files
5. Select files to read their content

### Collaboration Features
- **Auto-refresh**: Toggle to automatically update collaboration status
- **Model Status**: Green dot indicates active models
- **File Browser**: Click models to see their collaboration files
- **File Viewer**: Click files to read their content
- **Real-time Updates**: Watch AI team work together live

## 📁 Project Structure

```
gliksbot/
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── auth.py                 # Authentication
│   ├── requirements.txt        # Python dependencies
│   └── dexter_brain/
│       ├── config.py          # Configuration management
│       ├── collaboration.py   # AI collaboration system
│       ├── campaigns.py       # Campaign management
│       └── llm.py            # LLM integration
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Models.jsx     # Enhanced model configuration
│   │   │   ├── Normal.jsx     # Enhanced chat interface
│   │   │   └── ...
│   │   └── components/
│   └── package.json
├── collaboration/              # AI collaboration files
│   ├── dexter/
│   ├── analyst/
│   ├── engineer/
│   └── ...
├── config.json               # Main configuration
├── start.ps1                 # Startup script
└── README.md
```

## 🔐 Security Features

- **JWT Authentication**: Secure API access
- **API Key Management**: Environment variable based key storage
- **Input Validation**: Comprehensive request validation
- **CORS Protection**: Configured for known origins
- **Error Handling**: Robust error handling throughout

## 🚧 Advanced Features

### Skill Creation & Validation
- **Automated Skill Generation**: AI team creates executable skills
- **VM Testing**: Skills tested in isolated virtual machines
- **Skill Promotion**: Validated skills added to capability library

### Campaign Management
- **Objective Tracking**: Monitor long-term goals
- **Progress Analysis**: Detailed campaign analytics
- **Team Coordination**: AI models work together on campaigns

### Income Generation Focus
- **Revenue Optimization**: AI team focuses on income-generating activities
- **Business Development**: Automated opportunity identification
- **Service Automation**: Create and sell AI-powered services

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is proprietary software owned by Jeffrey Gliksman.

## 🆘 Support

For support, configuration help, or feature requests:
- Check the API documentation at http://localhost:8080/docs
- Review collaboration files for AI team insights
- Monitor the console for detailed error messages

## 🔮 Future Roadmap

- **Voice Interface**: Natural language voice commands
- **Mobile App**: iOS/Android applications
- **Marketplace**: Skill and template sharing
- **Enterprise Features**: Multi-tenant support
- **Advanced Analytics**: Performance and revenue tracking
- **Integration APIs**: Connect with external services

---

**GliksBot - Where AI Collaboration Drives Results**
