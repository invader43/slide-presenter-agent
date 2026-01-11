"""RTVI message schemas for client-server communication."""

from typing import Optional
from pydantic import BaseModel


class SlideContent(BaseModel):
    """Content of a single slide."""
    title: str
    content: str
    notes: Optional[str] = None
    image_url: Optional[str] = None


class SlideUpdateMessage(BaseModel):
    """Server → Client: Slide update message."""
    type: str = "slide-update"
    slide_number: int
    total_slides: int
    slide_content: SlideContent
    has_next: bool
    has_previous: bool


class PresentationStatusMessage(BaseModel):
    """Server → Client: Presentation status message."""
    type: str = "presentation-status"
    current_slide: int
    total_slides: int
    is_playing: bool = True
    voice_enabled: bool = True


# Client → Server Commands (for reference, handled via WebSocket)
class NextSlideCommand(BaseModel):
    """Client → Server: Move to next slide."""
    type: str = "next-slide"


class PrevSlideCommand(BaseModel):
    """Client → Server: Move to previous slide."""
    type: str = "prev-slide"


class GotoSlideCommand(BaseModel):
    """Client → Server: Jump to specific slide."""
    type: str = "goto-slide"
    slide_number: int
