# Voice-Enabled Slides Presenter

A full-stack web application that combines voice interaction with slide presentation capabilities. Navigate slides using voice commands or manual controls, with real-time audio communication powered by Pipecat.

## Features

- 🎤 Voice-controlled slide navigation
- 🔊 Real-time audio streaming (bidirectional)
- ⌨️ Manual slide controls (keyboard/buttons)
- 🐳 Containerized deployment with Docker
- 🎨 Modern, responsive UI

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose (optional)
- OpenAI API key

### Development Setup

1. **Clone and configure:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start the backend:**
   ```bash
   cd backend
   uv sync
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Start the frontend (in a new terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Open in browser:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Docker Deployment

```bash
# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## Usage

- **Voice Commands:** Say "next slide", "previous slide", or "go to slide 3"
- **Keyboard:** Use arrow keys (← →) or N/P keys
- **Mouse:** Click the navigation buttons

## Project Structure

```
├── backend/           # FastAPI + Pipecat backend
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── pipeline.py       # Pipecat pipeline
│   │   ├── config.py         # Configuration
│   │   ├── handlers/         # LLM function handlers
│   │   ├── models/           # Pydantic schemas
│   │   └── services/         # Business logic
│   └── slides/               # Presentation data
├── frontend/          # React + Vite frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   └── hooks/            # Custom hooks
│   └── nginx.conf            # Production server config
└── docker-compose.yml
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `AUTO_ADVANCE_ENABLED` | Enable auto-advance | `true` |
| `AUTO_ADVANCE_TIMEOUT_SECONDS` | Silence timeout | `3.0` |

## Technology Stack

- **Frontend:** React 18, Vite, @pipecat-ai/client-js
- **Backend:** FastAPI, Pipecat, OpenAI Realtime API
- **Infrastructure:** Docker, Nginx

## License

MIT