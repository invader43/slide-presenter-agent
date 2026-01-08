"""Data models for the slide presenter agent."""

from dataclasses import dataclass


@dataclass
class SlideData:
    """Container for slide information."""
    
    slide_number: int
    title: str
    content: str
    raw_text: str
