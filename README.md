# Dexter v3

Dexter v3 is an autonomous AI skill-building platform that combines a FastAPI backend with a React-based frontend. The backend provides APIs for skill management, collaboration, and system health monitoring, while the frontend offers a responsive interface built with Vite.

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
