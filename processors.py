"""Custom frame processors for the slide presenter agent."""

from typing import Optional, Callable

from loguru import logger

from pipecat.frames.frames import (
    Frame,
    TTSStartedFrame,
    TTSStoppedFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection


class SpeechEventProcessor(FrameProcessor):
    """Processor that detects speech events and notifies callbacks.
    
    This processor sits in the pipeline and watches for TTS and VAD
    frames, calling the appropriate callbacks when speech starts/stops.
    Used to notify the SilenceMonitor about speech activity.
    """
    
    def __init__(
        self,
        on_ai_started: Optional[Callable[[], None]] = None,
        on_ai_stopped: Optional[Callable[[], None]] = None,
        on_user_started: Optional[Callable[[], None]] = None,
        on_user_stopped: Optional[Callable[[], None]] = None,
        name: str = "SpeechEventProcessor",
    ):
        """Initialize the speech event processor.
        
        Args:
            on_ai_started: Callback when AI starts speaking (TTS)
            on_ai_stopped: Callback when AI stops speaking
            on_user_started: Callback when user starts speaking (VAD)
            on_user_stopped: Callback when user stops speaking
            name: Processor name for logging
        """
        super().__init__(name=name)
        self._on_ai_started = on_ai_started
        self._on_ai_stopped = on_ai_stopped
        self._on_user_started = on_user_started
        self._on_user_stopped = on_user_stopped
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames and detect speech events.
        
        Args:
            frame: The frame to process
            direction: Direction of frame flow
        """
        await super().process_frame(frame, direction)
        
        # Detect AI TTS events
        if isinstance(frame, TTSStartedFrame):
            logger.debug(f"🔊 [SpeechEventProcessor] TTS started")
            if self._on_ai_started:
                self._on_ai_started()
        
        elif isinstance(frame, TTSStoppedFrame):
            logger.debug(f"🔇 [SpeechEventProcessor] TTS stopped")
            if self._on_ai_stopped:
                self._on_ai_stopped()
        
        # Detect user speech events (VAD-based)
        elif isinstance(frame, UserStartedSpeakingFrame):
            logger.debug(f"🎤 [SpeechEventProcessor] User started speaking")
            if self._on_user_started:
                self._on_user_started()
        
        elif isinstance(frame, UserStoppedSpeakingFrame):
            logger.debug(f"🎤 [SpeechEventProcessor] User stopped speaking")
            if self._on_user_stopped:
                self._on_user_stopped()
        
        # Also catch transcription as speech indicator (backup)
        elif isinstance(frame, TranscriptionFrame):
            logger.debug(f"📝 [SpeechEventProcessor] Transcription received")
            if self._on_user_started:
                self._on_user_started()
        
        # Pass frame through unchanged
        await self.push_frame(frame, direction)
