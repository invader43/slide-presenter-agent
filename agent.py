"""Voice agent pipeline setup and configuration."""

import os
import asyncio
from typing import Dict, Any

from loguru import logger
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.openai.realtime.llm import OpenAIRealtimeLLMService
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
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

from config import (
    OPENAI_MODEL,
    OPENAI_VOICE,
    AGENT_INSTRUCTIONS,
    AUTO_ADVANCE_ENABLED,
    AUTO_ADVANCE_TIMEOUT_SECONDS,
    AUTO_ADVANCE_MESSAGE,
)
from tools import create_tools_schema
from handlers import (
    next_slide,
    previous_slide,
    goto_slide,
    get_current_slide_content,
    set_silence_monitor,
)
from silence_monitor import SilenceMonitor
from processors import SpeechEventProcessor


class VoiceAgent:
    """Voice agent for presenting PowerPoint slides."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.transport = None
        self.realtime = None
        self.task = None
        
        # Initialize silence monitor for auto-advance
        self.silence_monitor = SilenceMonitor(
            timeout_seconds=AUTO_ADVANCE_TIMEOUT_SECONDS,
            auto_advance_message=AUTO_ADVANCE_MESSAGE,
            enabled=AUTO_ADVANCE_ENABLED,
        )
        
        # Set the global silence monitor reference for handlers
        set_silence_monitor(self.silence_monitor)
    
    def _create_transport(self) -> LocalAudioTransport:
        """Create the audio transport."""
        return LocalAudioTransport(
            params=LocalAudioTransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            )
        )
    
    def _create_session_properties(self) -> SessionProperties:
        """Create session properties with instructions."""
        return SessionProperties(
            audio=AudioConfiguration(
                input=AudioInput(
                    transcription=InputAudioTranscription(),
                    turn_detection=SemanticTurnDetection(),
                )
            ),
            instructions=AGENT_INSTRUCTIONS
        )
    
    def _create_realtime_service(self) -> OpenAIRealtimeLLMService:
        """Create the OpenAI Realtime service."""
        realtime = OpenAIRealtimeLLMService(
            api_key=self.api_key,
            model=OPENAI_MODEL,
            voice=OPENAI_VOICE,
            session_properties=self._create_session_properties(),
            start_audio_paused=False,
        )
        
        # Register function handlers
        realtime.register_function("next_slide", next_slide)
        realtime.register_function("previous_slide", previous_slide)
        realtime.register_function("goto_slide", goto_slide)
        realtime.register_function("get_current_slide_content", get_current_slide_content)
        
        return realtime
    
    def _create_context(self, initial_slide: Dict[str, Any]) -> LLMContext:
        """Create LLM context with initial slide information."""
        return LLMContext(
            messages=[
                {
                    "role": "user",
                    "content": f"Please start the presentation. The first slide is titled '{initial_slide['title']}'. Here's the content: {initial_slide['content']}"
                }
            ],
            tools=create_tools_schema(),
        )
    
    def _create_speech_event_processor(self) -> SpeechEventProcessor:
        """Create processor to detect speech events for silence monitoring."""
        return SpeechEventProcessor(
            on_ai_started=self.silence_monitor.on_ai_started_speaking,
            on_ai_stopped=self.silence_monitor.on_ai_stopped_speaking,
            on_user_started=self.silence_monitor.on_user_speech_detected,
            on_user_stopped=self.silence_monitor.on_user_speech_ended,
        )
    
    def _create_pipeline(
        self,
        transport: LocalAudioTransport,
        realtime: OpenAIRealtimeLLMService,
        context_aggregator: LLMContextAggregatorPair,
        speech_processor: SpeechEventProcessor,
    ) -> Pipeline:
        """Create the processing pipeline."""
        return Pipeline([
            transport.input(),
            speech_processor,  # Detect speech events for auto-advance
            context_aggregator.user(),
            realtime,
            transport.output(),
            context_aggregator.assistant(),
        ])
    
    async def run(self, initial_slide: Dict[str, Any]) -> None:
        """Run the voice agent."""
        logger.info("🎤 Initializing local microphone transport...")
        self.transport = self._create_transport()
        
        logger.info("🤖 Initializing OpenAI Realtime Service...")
        self.realtime = self._create_realtime_service()
        
        # Create context and aggregator
        context = self._create_context(initial_slide)
        context_aggregator = LLMContextAggregatorPair(context)
        
        # Create speech event processor for silence monitoring
        speech_processor = self._create_speech_event_processor()
        
        # Create pipeline
        pipeline = self._create_pipeline(
            self.transport,
            self.realtime,
            context_aggregator,
            speech_processor,
        )
        
        # Create task
        self.task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
            )
        )
        
        # Set the pipeline task for silence monitor (needed for frame injection)
        self.silence_monitor.set_pipeline_task(self.task)
        
        # Initialize last slide state
        if not initial_slide.get('has_next', True):
            self.silence_monitor.set_last_slide_reached(True)
        
        self._log_startup_info()
        
        # Run the pipeline with initial message trigger
        runner = PipelineRunner()
        
        # Queue the initial LLM run to trigger the first response
        # We use asyncio.create_task to queue immediately after pipeline starts
        async def trigger_initial_response():
            await asyncio.sleep(0.5)  # Brief delay to ensure pipeline is ready
            logger.info("🎙️ Triggering initial presentation...")
            from pipecat.frames.frames import LLMRunFrame
            # Queue LLMRunFrame to trigger LLM response based on current context
            await self.task.queue_frames([LLMRunFrame()])
        
        asyncio.create_task(trigger_initial_response())
        
        await runner.run(self.task)
    
    def _log_startup_info(self) -> None:
        """Log startup information."""
        logger.info("✅ Voice agent ready!")
        logger.info("📊 PowerPoint viewer window should be open")
        logger.info("🎤 Listening on your microphone...")
        logger.info("💡 The AI will present each slide and ask for questions")
        logger.info("💡 Say 'next slide' to move forward")
        logger.info("💡 Say 'previous slide' to go back")
        logger.info("💡 Ask questions about the content anytime")
        logger.info("🛑 Press Ctrl+C to stop")
        print()
