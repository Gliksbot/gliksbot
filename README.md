# Dexter v3

Dexter v3 is an autonomous AI skill-building platform that combines a FastAPI backend with a React-based frontend. The backend provides APIs for skill management, collaboration, and system health monitoring, while the frontend offers a responsive interface built with Vite.

## Quick Start

Use the helper script to install dependencies and launch both the backend and frontend:

```bash
python install_and_run.py
```

The script creates a virtual environment, installs Python packages, installs npm packages for the React app and then starts the backend on <http://127.0.0.1:8080> with the frontend served by Vite on <http://127.0.0.1:5173>.

## Requirements

* Python 3.8+
* Node.js 18+

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Install frontend dependencies:
```bash
cd frontend
npm install
```

## Running the Backend

```bash
uvicorn backend.main:app --reload
```

## Running Tests

```bash
pytest
```
