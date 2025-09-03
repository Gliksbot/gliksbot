#!/bin/bash
# Dexter v3 Installer Script for Linux/macOS
# This script sets up the complete Dexter v3 environment

set -e  # Exit on any error

echo "============================================"
echo "  🤖 Dexter v3 - Autonomous AI System"
echo "============================================"
echo "Installing dependencies and setting up environment..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

if [ "$MACHINE" = "UNKNOWN:${OS}" ]; then
    print_error "Unsupported operating system: ${OS}"
    print_error "This installer supports Linux and macOS only."
    print_error "For Windows, please use install.bat"
    exit 1
fi

print_status "Detected OS: $MACHINE"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    print_error "Please install Python 3.8+ before running this installer"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Python version: $PYTHON_VERSION"

# Check Node.js installation
if ! command -v node &> /dev/null; then
    print_warning "Node.js is not installed"
    print_status "Installing Node.js via package manager..."
    
    case "${MACHINE}" in
        Linux)
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y nodejs npm
            elif command -v yum &> /dev/null; then
                sudo yum install -y nodejs npm
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y nodejs npm
            else
                print_error "Could not install Node.js automatically"
                print_error "Please install Node.js manually from https://nodejs.org/"
                exit 1
            fi
            ;;
        Mac)
            if command -v brew &> /dev/null; then
                brew install node
            else
                print_error "Homebrew not found. Please install Node.js manually from https://nodejs.org/"
                exit 1
            fi
            ;;
    esac
fi

NODE_VERSION=$(node --version)
print_status "Node.js version: $NODE_VERSION"

# Install Python dependencies
print_status "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    python3 -m pip install -r requirements.txt
fi
print_success "Python dependencies installed"

# Install frontend dependencies
print_status "Installing frontend dependencies..."
cd frontend
npm install
print_success "Frontend dependencies installed"

# Build frontend
print_status "Building frontend for production..."
npm run build
print_success "Frontend built successfully"
cd ..

# Check Docker installation for sandbox
if command -v docker &> /dev/null; then
    print_status "Docker found - sandbox mode available"
    print_status "Building Docker sandbox image..."
    docker build -f Dockerfile.sandbox -t dexter-sandbox .
    print_success "Docker sandbox ready"
else
    print_warning "Docker not found - sandbox mode will be limited"
    print_warning "Install Docker for full sandbox capabilities"
fi

# Create logs directory
mkdir -p logs
print_status "Created logs directory"

# Set up configuration
if [ ! -f .env ]; then
    if [ -f .env.template ]; then
        cp .env.template .env
        print_status "Created .env file from template"
        print_warning "Please edit .env file with your API keys and configuration"
    fi
fi

# Make launch script executable
chmod +x launch.sh 2>/dev/null || true

echo ""
print_success "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys (optional)"
echo "2. Run './launch.sh' to start the system"
echo "3. Open http://localhost:3000 for the web interface"
echo "4. Backend API will be available at http://localhost:8000"
echo ""
echo "For testing without dependencies, run: python3 demo_system.py"
echo ""