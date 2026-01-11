"""Pipecat pipeline setup for WebSocket transport."""

from typing import Dict, Any

from loguru import logger
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.openai.realtime.llm import OpenAIRealtimeLLMService
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.openai.realtime.events import (
    AudioConfiguration,
    AudioInput,
    InputAudioTranscription,
    SemanticTurnDetection,
    SessionProperties,
)

from .config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_VOICE,
    AGENT_INSTRUCTIONS,
)
from .services.slide_service import SlideService
from .handlers.slide_handlers import create_slide_handlers, create_tools_schema


async def create_pipeline(
    transport: FastAPIWebsocketTransport,
    slide_service: SlideService,
) -> PipelineTask:
    """Create the Pipecat pipeline for a WebSocket connection.
    
    Args:
        transport: The WebSocket transport for this connection
        slide_service: The slide service instance for this session
        
    Returns:
        PipelineTask ready to run
    """
    logger.info("🔧 Creating Pipecat pipeline...")
    
    # Create session properties
    session_properties = SessionProperties(
        audio=AudioConfiguration(
            input=AudioInput(
                transcription=InputAudioTranscription(),
                turn_detection=SemanticTurnDetection(),
            )
        ),
        instructions=AGENT_INSTRUCTIONS
    )
    
    # Create OpenAI Realtime service
    realtime = OpenAIRealtimeLLMService(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        voice=OPENAI_VOICE,
        session_properties=session_properties,
        start_audio_paused=False,
    )
    
    # Register function handlers
    handlers = create_slide_handlers(slide_service)
    for name, handler in handlers.items():
        realtime.register_function(name, handler)
    
    # Create initial context
    initial_slide = slide_service.get_current_slide()
    context = LLMContext(
        messages=[
            {
                "role": "user",
                "content": f"Please start the presentation. The first slide is titled '{initial_slide['title']}'. Here's the content: {initial_slide['content']}"
            }
        ],
        tools=create_tools_schema(),
    )
    
    # Create context aggregator
    context_aggregator = LLMContextAggregatorPair(context)
    
    # Create pipeline
    pipeline = Pipeline([
        transport.input(),
        context_aggregator.user(),
        realtime,
        transport.output(),
        context_aggregator.assistant(),
    ])
    
    # Create task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        )
    )
    
    logger.info("✅ Pipeline created successfully")
    return task
