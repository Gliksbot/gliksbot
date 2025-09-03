#!/bin/bash
# Dexter v3 Launch Script for Linux/macOS
# This script starts both frontend and backend services

set -e

echo "============================================"
echo "  🚀 Launching Dexter v3 System"
echo "============================================"

# Colors for output
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

# Check if dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    print_warning "Frontend dependencies not found. Installing..."
    cd frontend
    npm install
    cd ..
fi

if [ ! -d "frontend/dist" ]; then
    print_warning "Frontend not built. Building..."
    cd frontend
    npm run build
    cd ..
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to cleanup background processes
cleanup() {
    print_status "Shutting down services..."
    
    # Kill background processes if they exist
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        print_status "Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        print_status "Frontend stopped"
    fi
    
    print_success "All services stopped"
    exit 0
}

# Setup signal handlers
trap cleanup SIGINT SIGTERM

print_status "Starting backend server..."
cd backend
python3 main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

print_status "Starting frontend development server..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

print_success "Dexter v3 is now running!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📄 Logs are saved in the logs/ directory"
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Show status of services
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "Backend is running (PID: $BACKEND_PID)"
else
    print_warning "Backend may have failed to start - check logs/backend.log"
fi

if kill -0 $FRONTEND_PID 2>/dev/null; then
    print_success "Frontend is running (PID: $FRONTEND_PID)"
else
    print_warning "Frontend may have failed to start - check logs/frontend.log"
fi

# Keep script running and monitor processes
echo ""
print_status "Monitoring services... (Ctrl+C to stop)"

while true; do
    sleep 5
    
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_warning "Backend process stopped unexpectedly"
        break
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_warning "Frontend process stopped unexpectedly"
        break
    fi
done

cleanup