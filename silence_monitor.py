"""Silence monitoring for auto-advance functionality."""

import asyncio
from typing import Optional

from loguru import logger

from pipecat.pipeline.task import PipelineTask
from pipecat.frames.frames import LLMMessagesAppendFrame, LLMFullResponseEndFrame


class SilenceMonitor:
    """Monitors for extended silence and triggers auto-advance.
    
    This class manages a timer that starts when the AI finishes speaking.
    If the user doesn't respond within the timeout period, it injects
    a message into the LLM context to trigger automatic slide advancement.
    """
    
    def __init__(
        self,
        timeout_seconds: float = 10.0,
        auto_advance_message: str = "[Continue to next slide]",
        enabled: bool = True
    ):
        """Initialize the silence monitor.
        
        Args:
            timeout_seconds: Seconds of silence before auto-advancing
            auto_advance_message: Message to inject when timeout occurs
            enabled: Whether auto-advance is enabled
        """
        self.timeout = timeout_seconds
        self.auto_advance_message = auto_advance_message
        self.enabled = enabled
        
        self._task: Optional[PipelineTask] = None
        self._timer_task: Optional[asyncio.Task] = None
        self._is_ai_speaking: bool = False
        self._last_slide_reached: bool = False
    
    def set_pipeline_task(self, task: PipelineTask) -> None:
        """Set the pipeline task for frame injection.
        
        Args:
            task: The PipelineTask to queue frames to
        """
        self._task = task
        logger.info(f"🔇 SilenceMonitor initialized (timeout: {self.timeout}s, enabled: {self.enabled})")
    
    def set_last_slide_reached(self, reached: bool) -> None:
        """Update whether we're on the last slide.
        
        Args:
            reached: True if on the last slide
        """
        self._last_slide_reached = reached
        if reached:
            logger.debug("📊 Last slide reached - auto-advance will conclude instead")
    
    def on_ai_started_speaking(self) -> None:
        """Called when AI begins TTS output."""
        self._is_ai_speaking = True
        self._cancel_timer()
        logger.debug("🔊 AI started speaking - silence timer cancelled")
    
    def on_ai_stopped_speaking(self) -> None:
        """Called when AI finishes TTS output."""
        self._is_ai_speaking = False
        if self.enabled:
            self._start_timer()
            logger.debug(f"🔇 AI stopped speaking - starting {self.timeout}s silence timer")
    
    def on_user_speech_detected(self) -> None:
        """Called when user voice activity is detected."""
        self._cancel_timer()
        logger.debug("🎤 User speech detected - silence timer cancelled")
    
    def on_user_speech_ended(self) -> None:
        """Called when user finishes speaking.
        
        Note: We don't restart the timer here. The timer only starts
        after the AI finishes its response to the user.
        """
        pass
    
    def _start_timer(self) -> None:
        """Start the silence countdown timer."""
        self._cancel_timer()
        self._timer_task = asyncio.create_task(self._timeout_handler())
    
    def _cancel_timer(self) -> None:
        """Cancel any running timer."""
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            self._timer_task = None
    
    async def _timeout_handler(self) -> None:
        """Handle silence timeout - inject auto-advance message."""
        try:
            await asyncio.sleep(self.timeout)
            
            if self._task is None:
                logger.error("❌ Cannot auto-advance: Pipeline task not set")
                return
            
            if self._is_ai_speaking:
                logger.debug("⏰ Timeout reached but AI is speaking - skipping")
                return
            
            logger.info("⏰ Silence timeout reached - triggering auto-advance")
            
            # Determine the appropriate message
            if self._last_slide_reached:
                message = "[SYSTEM: No user response detected. This is the last slide. Please thank the audience and conclude the presentation gracefully.]"
            else:
                message = self.auto_advance_message
            
            # Inject message into LLM context and trigger response
            message_frame = LLMMessagesAppendFrame([
                {
                    "role": "user",
                    "content": message
                }
            ])
            
            # Queue frames to trigger LLM response
            # Using LLMFullResponseEndFrame to signal completion and trigger new response
            from pipecat.frames.frames import LLMMessagesFrame
            await self._task.queue_frames([message_frame])
            
        except asyncio.CancelledError:
            # Timer was cancelled (user spoke or AI started speaking)
            logger.debug("⏰ Silence timer was cancelled")
        except Exception as e:
            logger.error(f"❌ Error in silence timeout handler: {e}")
    
    def disable(self) -> None:
        """Temporarily disable auto-advance."""
        self.enabled = False
        self._cancel_timer()
        logger.info("🔇 Auto-advance disabled")
    
    def enable(self) -> None:
        """Re-enable auto-advance."""
        self.enabled = True
        logger.info("🔇 Auto-advance enabled")
