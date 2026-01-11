"""FastAPI application for the Voice-Enabled Slides Presenter."""

import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)

from .config import CORS_ORIGINS, OPENAI_API_KEY, SLIDES_PATH
from .services.slide_service import SlideService
from .pipeline import create_pipeline


# Global slide service for persistence across requests
_slide_service: SlideService = None


def get_slide_service() -> SlideService:
    """Get or create the global slide service."""
    global _slide_service
    if _slide_service is None:
        _slide_service = SlideService()
    return _slide_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🚀 Starting Voice-Enabled Slides Presenter Backend")
    
    if not OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not set in environment")
    else:
        logger.info("✅ OpenAI API key configured")
    
    # Initialize slide service
    get_slide_service()
    
    yield
    
    logger.info("👋 Shutting down backend")


app = FastAPI(
    title="Voice-Enabled Slides Presenter",
    description="Backend API for voice-controlled slide presentations",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "openai_configured": bool(OPENAI_API_KEY),
    }


@app.get("/api/slides")
async def get_slides():
    """Get all slides for the presentation."""
    slide_service = get_slide_service()
    slides = []
    for i in range(1, slide_service.total_slides + 1):
        slide = slide_service.get_slide(i)
        if slide:
            slides.append(slide)
    return {"slides": slides, "total": slide_service.total_slides}


@app.post("/api/slides/upload")
async def upload_slides(file: UploadFile = File(...)):
    """Upload slides from a PDF or JSON file."""
    global _slide_service
    
    filename = file.filename.lower()
    
    if not (filename.endswith('.json') or filename.endswith('.pdf')):
        raise HTTPException(status_code=400, detail="Only PDF and JSON files are supported")
    
    try:
        content = await file.read()
        
        if filename.endswith('.pdf'):
            # Parse PDF file
            import fitz  # pymupdf
            
            pdf_doc = fitz.open(stream=content, filetype="pdf")
            slides = []
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                text = page.get_text().strip()
                
                # Extract title (first line) and content (rest)
                lines = text.split('\n')
                title = lines[0] if lines else f"Slide {page_num + 1}"
                content_text = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                
                slides.append({
                    "number": page_num + 1,
                    "title": title[:100],  # Limit title length
                    "content": content_text[:1000],  # Limit content length
                    "notes": ""
                })
            
            pdf_doc.close()
            
            if not slides:
                raise HTTPException(status_code=400, detail="PDF has no pages")
            
            data = {"slides": slides}
            
        else:
            # Parse JSON file
            data = json.loads(content.decode('utf-8'))
            
            if 'slides' not in data:
                raise HTTPException(status_code=400, detail="JSON must contain 'slides' array")
            
            slides = data['slides']
            if not isinstance(slides, list) or len(slides) == 0:
                raise HTTPException(status_code=400, detail="'slides' must be a non-empty array")
        
        # Save to presentation.json
        slides_path = Path(SLIDES_PATH)
        slides_path.parent.mkdir(parents=True, exist_ok=True)
        with open(slides_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Reload slide service
        _slide_service = SlideService()
        
        logger.info(f"📊 Uploaded {len(data['slides'])} slides from {file.filename}")
        return {
            "message": f"Successfully uploaded {len(data['slides'])} slides",
            "total": len(data['slides']),
            "slides": data['slides']
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Pipecat voice streaming."""
    await websocket.accept()
    logger.info("🔌 WebSocket connection established")
    
    # Create a new slide service for this session
    slide_service = SlideService()
    
    try:
        # Create WebSocket transport
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
            )
        )
        
        # Create and run pipeline
        task = await create_pipeline(transport, slide_service)
        runner = PipelineRunner()
        
        logger.info("🎤 Starting voice pipeline...")
        await runner.run(task)
        
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected by client")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        raise
    finally:
        logger.info("🔌 WebSocket session ended")


if __name__ == "__main__":
    import uvicorn
    from .config import HOST, PORT
    
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=True,
    )
