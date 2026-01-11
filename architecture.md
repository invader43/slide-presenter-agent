# Voice-Enabled Slides Presenter - Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Communication Flow](#communication-flow)
5. [Docker Setup](#docker-setup)
6. [Technology Stack](#technology-stack)
7. [Message Protocol](#message-protocol)
8. [Deployment](#deployment)

---

## Overview

The Voice-Enabled Slides Presenter is a full-stack web application that combines voice interaction with slide presentation capabilities. Users can navigate slides using voice commands or manual controls, with real-time audio communication powered by Pipecat.

### Key Features
- Voice-controlled slide navigation
- Real-time audio streaming (bidirectional)
- Manual slide controls (keyboard/buttons)
- WebRTC/WebSocket transport options
- Containerized deployment with Docker

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT BROWSER                          │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              React Frontend Application                │     │
│  │                                                         │     │
│  │  ┌──────────────────┐    ┌──────────────────────┐     │     │
│  │  │ Slide Display    │    │ Control Panel        │     │     │
│  │  │ Component        │    │ - Next/Prev Buttons  │     │     │
│  │  │ - Current Slide  │    │ - Keyboard Controls  │     │     │
│  │  │ - Progress Bar   │    │ - Voice Indicator    │     │     │
│  │  └──────────────────┘    └──────────────────────┘     │     │
│  │                                                         │     │
│  │  ┌─────────────────────────────────────────────────┐   │     │
│  │  │         PipecatClient (@pipecat-ai)            │   │     │
│  │  │  - Audio streaming (mic → speaker)             │   │     │
│  │  │  - RTVI message handling                       │   │     │
│  │  │  - Transport layer (WebRTC/WebSocket)          │   │     │
│  │  └─────────────────────────────────────────────────┘   │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ HTTPS/WSS
                       │ Port 3000 (Dev) / 80,443 (Prod)
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                      NGINX (Optional)                           │
│                   Reverse Proxy / SSL                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌───────────────────┐         ┌───────────────────┐
│  Frontend         │         │  Backend          │
│  Container        │         │  Container        │
│  (Node.js)        │         │  (Python/FastAPI) │
│  Port: 3000       │         │  Port: 8000       │
└───────────────────┘         └───────────────────┘
                                      │
                                      │
                    ┌─────────────────┴──────────────────┐
                    │                                    │
                    ▼                                    ▼
            ┌──────────────┐                   ┌──────────────┐
            │ Pipecat      │                   │ External     │
            │ Pipeline     │                   │ Services     │
            │              │                   │              │
            │ - Transport  │                   │ - STT API    │
            │ - RTVIProc   │                   │ - LLM API    │
            │ - STT        │                   │ - TTS API    │
            │ - LLM        │                   │ - Daily.co   │
            │ - TTS        │                   │              │
            │ - Slide Ctrl │                   └──────────────┘
            └──────────────┘
```

---

## Component Details

### 1. Frontend Container (React + Vite)

**Purpose**: Serves the web-based slide presentation interface with voice controls.

**Responsibilities**:
- Render slides with animations and transitions
- Handle user interactions (buttons, keyboard)
- Manage PipecatClient connection
- Stream audio to/from user's microphone and speakers
- Display real-time slide updates from backend
- Show voice activity indicators

**Key Files**:
```
frontend/
├── src/
│   ├── components/
│   │   ├── SlideDisplay.jsx       # Main slide renderer
│   │   ├── ControlPanel.jsx       # Navigation controls
│   │   ├── VoiceIndicator.jsx     # Mic/speaker status
│   │   └── SlideProgress.jsx      # Progress bar
│   ├── hooks/
│   │   ├── usePipecat.js          # Pipecat client hook
│   │   └── useSlideControl.js     # Slide state management
│   ├── App.jsx
│   └── main.jsx
├── Dockerfile
├── package.json
└── vite.config.js
```

**Environment Variables**:
- `VITE_BACKEND_URL`: Backend API endpoint
- `VITE_WS_URL`: WebSocket endpoint (if using WebSocket transport)
- `VITE_DAILY_URL`: Daily.co room URL (if using Daily transport)

---

### 2. Backend Container (Python + FastAPI)

**Purpose**: Runs the Pipecat voice agent pipeline and manages slide state.

**Responsibilities**:
- Process incoming audio streams
- Run STT (Speech-to-Text) on voice input
- Send transcriptions to LLM for intent detection
- Generate TTS (Text-to-Speech) responses
- Manage slide state (current slide, total slides, content)
- Send slide updates via RTVI messages
- Handle custom client messages (manual navigation)

**Key Files**:
```
backend/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── pipeline.py                # Pipecat pipeline setup
│   ├── processors/
│   │   ├── slide_control.py       # Custom slide processor
│   │   └── intent_detector.py     # Detect slide commands
│   ├── services/
│   │   ├── slide_service.py       # Slide content management
│   │   └── transport_service.py   # Transport initialization
│   ├── models/
│   │   └── messages.py            # RTVI message schemas
│   └── config.py                  # Configuration
├── slides/
│   └── presentation.json          # Slide content data
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

**Environment Variables**:
- `OPENAI_API_KEY`: For LLM/STT/TTS
- `DEEPGRAM_API_KEY`: Alternative STT provider
- `DAILY_API_KEY`: For Daily.co transport
- `TRANSPORT_TYPE`: 'daily' or 'websocket'
- `LOG_LEVEL`: Logging verbosity

---

### 3. Pipecat Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipecat Pipeline                         │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Transport  │◄────►│ RTVIProcessor│                    │
│  │ (Daily/WS)   │      │              │                    │
│  └──────┬───────┘      └──────┬───────┘                    │
│         │                     │                            │
│         │ Audio In            │ Custom Messages            │
│         ▼                     ▼                            │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │     STT      │      │ Message      │                    │
│  │  Processor   │      │ Handler      │                    │
│  └──────┬───────┘      └──────┬───────┘                    │
│         │                     │                            │
│         │ Text                │                            │
│         ▼                     │                            │
│  ┌──────────────┐             │                            │
│  │    LLM       │             │                            │
│  │  Processor   │             │                            │
│  └──────┬───────┘             │                            │
│         │                     │                            │
│         │ Response            │                            │
│         ▼                     ▼                            │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ Slide Control│      │ Send RTVI    │                    │
│  │  Processor   │─────►│ Messages     │                    │
│  └──────┬───────┘      └──────────────┘                    │
│         │                                                  │
│         │ Updated Text                                     │
│         ▼                                                  │
│  ┌──────────────┐                                          │
│  │     TTS      │                                          │
│  │  Processor   │                                          │
│  └──────┬───────┘                                          │
│         │                                                  │
│         │ Audio Out                                        │
│         ▼                                                  │
│  ┌──────────────┐                                          │
│  │   Transport  │                                          │
│  │   (Output)   │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Communication Flow

### Voice-Triggered Slide Change

```
User speaks "next slide"
         │
         ▼
┌─────────────────────┐
│  Browser captures   │
│  microphone audio   │
└──────────┬──────────┘
           │ Audio stream
           ▼
┌─────────────────────┐
│  PipecatClient      │
│  sends audio via    │
│  WebRTC/WebSocket   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Backend receives   │
│  audio frames       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  STT converts to    │
│  text: "next slide" │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  LLM processes &    │
│  confirms intent    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ SlideControl        │
│ Processor detects   │
│ command             │
└──────────┬──────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌─────────────────────┐   ┌─────────────────────┐
│ Send RTVI message   │   │ Generate TTS reply  │
│ with slide update   │   │ "Moving to slide 2" │
└──────────┬──────────┘   └──────────┬──────────┘
           │                         │
           │                         │ Audio stream
           │                         ▼
           │              ┌─────────────────────┐
           │              │  Speaker plays      │
           │              │  audio response     │
           │              └─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Browser receives   │
│  RTVI message       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  React updates UI   │
│  with new slide     │
└─────────────────────┘
```

### Manual Slide Navigation

```
User clicks "Next" button
         │
         ▼
┌─────────────────────┐
│  onClick handler    │
│  triggered          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  pcClient.send      │
│  Message({          │
│   type: "next-slide"│
│  })                 │
└──────────┬──────────┘
           │ RTVI message
           ▼
┌─────────────────────┐
│  Backend receives   │
│  client message     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Message handler    │
│  processes request  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Update slide state │
│  & send RTVI reply  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Browser updates UI │
└─────────────────────┘
```

---

## Docker Setup

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf for Frontend**:
```nginx
server {
    listen 3000;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing - redirect all requests to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to backend
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: slides-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_BACKEND_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000/ws
    depends_on:
      - backend
    networks:
      - slides-network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: slides-backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - DAILY_API_KEY=${DAILY_API_KEY}
      - TRANSPORT_TYPE=websocket
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=http://localhost:3000
    volumes:
      - ./backend/slides:/app/slides:ro
      - backend-logs:/app/logs
    networks:
      - slides-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  slides-network:
    driver: bridge

volumes:
  backend-logs:
    driver: local
```

---

### Environment Configuration

Create a `.env` file in the project root:

```bash
# .env
# API Keys
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
DAILY_API_KEY=...

# Transport Configuration
TRANSPORT_TYPE=websocket  # or 'daily'

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:80

# Logging
LOG_LEVEL=INFO
```

---

## Technology Stack

### Frontend
- **Framework**: React 18+ with Vite
- **Voice Client**: `@pipecat-ai/client-js`
- **Transport**: `@pipecat-ai/daily-transport` or `@pipecat-ai/websocket-transport`
- **UI Library**: TailwindCSS or Material-UI
- **State Management**: React Hooks (useState, useContext)
- **HTTP Client**: Axios or Fetch API

### Backend
- **Framework**: FastAPI
- **Voice Pipeline**: Pipecat
- **Transport**: DailyTransport or FastAPIWebsocketTransport
- **STT**: OpenAI Whisper, Deepgram, or AssemblyAI
- **LLM**: OpenAI GPT-4, Anthropic Claude
- **TTS**: OpenAI TTS, ElevenLabs, or Cartesia
- **ASGI Server**: Uvicorn

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (for frontend static files)
- **Reverse Proxy**: Nginx or Traefik (optional, for SSL/routing)

---

## Message Protocol

### RTVI Message Types

#### 1. Slide Update (Server → Client)

```json
{
  "type": "slide-update",
  "payload": {
    "slideNumber": 2,
    "totalSlides": 10,
    "slideContent": {
      "title": "Architecture Overview",
      "content": "System design and components...",
      "imageUrl": "/slides/img/architecture.png",
      "notes": "Discuss each component in detail"
    },
    "timestamp": "2026-01-11T10:30:00Z"
  }
}
```

#### 2. Next Slide Command (Client → Server)

```json
{
  "type": "next-slide",
  "payload": {}
}
```

#### 3. Previous Slide Command (Client → Server)

```json
{
  "type": "prev-slide",
  "payload": {}
}
```

#### 4. Go To Slide (Client → Server)

```json
{
  "type": "goto-slide",
  "payload": {
    "slideNumber": 5
  }
}
```

#### 5. Presentation Status (Server → Client)

```json
{
  "type": "presentation-status",
  "payload": {
    "currentSlide": 2,
    "totalSlides": 10,
    "isPlaying": true,
    "voiceEnabled": true
  }
}
```

---

## Deployment

### Development

```bash
# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Production Deployment

#### 1. Build Production Images

```bash
# Build with production tags
docker-compose -f docker-compose.prod.yml build

# Tag images
docker tag slides-frontend:latest your-registry/slides-frontend:v1.0.0
docker tag slides-backend:latest your-registry/slides-backend:v1.0.0

# Push to registry
docker push your-registry/slides-frontend:v1.0.0
docker push your-registry/slides-backend:v1.0.0
```

#### 2. Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - certbot-etc:/etc/letsencrypt
      - certbot-var:/var/lib/letsencrypt
    depends_on:
      - frontend
      - backend
    networks:
      - slides-network
    restart: always

  frontend:
    image: your-registry/slides-frontend:v1.0.0
    environment:
      - VITE_BACKEND_URL=https://api.yourdomain.com
      - VITE_WS_URL=wss://api.yourdomain.com/ws
    networks:
      - slides-network
    restart: always

  backend:
    image: your-registry/slides-backend:v1.0.0
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TRANSPORT_TYPE=daily
      - LOG_LEVEL=WARNING
      - CORS_ORIGINS=https://yourdomain.com
    networks:
      - slides-network
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

networks:
  slides-network:
    driver: bridge

volumes:
  certbot-etc:
  certbot-var:
```

#### 3. SSL Configuration with Let's Encrypt

```nginx
# nginx/nginx.conf (production)
upstream frontend {
    server frontend:3000;
}

upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

---

## Monitoring and Logging

### Health Checks

Both containers include health check endpoints:

**Frontend**: Served by Nginx, always returns 200 if running
**Backend**: `GET /health` endpoint

```python
# app/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

### Logging

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Export logs
docker-compose logs backend > backend.log
```

---

## Security Considerations

1. **API Keys**: Never commit API keys to version control. Use environment variables.
2. **CORS**: Configure appropriate CORS origins in production.
3. **SSL/TLS**: Always use HTTPS in production.
4. **Rate Limiting**: Implement rate limiting on backend endpoints.
5. **Input Validation**: Validate all client messages before processing.
6. **Authentication**: Add user authentication if needed (JWT, OAuth).

---

## Performance Optimization

1. **Frontend**:
   - Code splitting and lazy loading
   - Asset optimization (images, fonts)
   - CDN for static assets
   - Service worker for offline capability

2. **Backend**:
   - Connection pooling for external APIs
   - Caching frequently accessed slides
   - Async processing for non-blocking operations
   - Load balancing for multiple instances

---

## Future Enhancements

- Multi-user presentations (collaborative mode)
- Slide annotations and drawing tools
- Recording and playback capabilities
- Real-time audience Q&A
- Analytics and engagement tracking
- Mobile app (React Native)
- Offline mode with slide caching

---

## Troubleshooting

### Common Issues

**Issue**: WebSocket connection fails
**Solution**: Check CORS settings, verify WebSocket endpoint URL, ensure proper proxy configuration

**Issue**: No audio output
**Solution**: Check browser permissions, verify TTS API key, check audio device settings

**Issue**: Slides not updating
**Solution**: Check RTVI message handler, verify slide service is running, check browser console for errors

**Issue**: High latency
**Solution**: Use Daily.co transport instead of WebSocket, optimize pipeline processors, check network conditions

---

## Contact and Support

For issues and feature requests, please refer to:
- Pipecat Documentation: https://docs.pipecat.ai