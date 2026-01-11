"""Slide content management service."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from loguru import logger

from ..config import SLIDES_PATH
from ..models.messages import SlideContent


class SlideService:
    """Manages slide content and navigation state."""
    
    def __init__(self, slides_path: Optional[str] = None):
        """Initialize the slide service.
        
        Args:
            slides_path: Path to the slides JSON file
        """
        self.slides_path = Path(slides_path or SLIDES_PATH)
        self.slides: List[Dict[str, Any]] = []
        self.current_index: int = 0
        self._load_slides()
    
    def _load_slides(self) -> None:
        """Load slides from JSON file."""
        try:
            if self.slides_path.exists():
                with open(self.slides_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.slides = data.get("slides", [])
                logger.info(f"📊 Loaded {len(self.slides)} slides from {self.slides_path}")
            else:
                logger.warning(f"⚠️ Slides file not found: {self.slides_path}")
                # Create default slide
                self.slides = [
                    {
                        "number": 1,
                        "title": "Welcome",
                        "content": "No presentation loaded. Please add slides to presentation.json",
                        "notes": ""
                    }
                ]
        except Exception as e:
            logger.error(f"❌ Error loading slides: {e}")
            self.slides = []
    
    @property
    def total_slides(self) -> int:
        """Get total number of slides."""
        return len(self.slides)
    
    @property
    def current_slide_number(self) -> int:
        """Get current slide number (1-based)."""
        return self.current_index + 1
    
    def get_slide(self, number: int) -> Optional[Dict[str, Any]]:
        """Get a slide by its number (1-based).
        
        Args:
            number: Slide number (1-based)
            
        Returns:
            Slide data or None if not found
        """
        index = number - 1
        if 0 <= index < len(self.slides):
            return self.slides[index]
        return None
    
    def get_current_slide(self) -> Dict[str, Any]:
        """Get the current slide info.
        
        Returns:
            Dictionary with slide info and navigation status
        """
        if not self.slides:
            return {
                "error": "No slides loaded",
                "slide_number": 0,
                "total_slides": 0,
            }
        
        slide = self.slides[self.current_index]
        return {
            "slide_number": self.current_slide_number,
            "total_slides": self.total_slides,
            "title": slide.get("title", f"Slide {self.current_slide_number}"),
            "content": slide.get("content", ""),
            "notes": slide.get("notes", ""),
            "has_next": self.current_index < len(self.slides) - 1,
            "has_previous": self.current_index > 0,
        }
    
    def next_slide(self) -> Dict[str, Any]:
        """Move to the next slide.
        
        Returns:
            New slide info or error if at end
        """
        if self.current_index < len(self.slides) - 1:
            self.current_index += 1
            logger.info(f"📊 Advanced to slide {self.current_slide_number}")
            return self.get_current_slide()
        else:
            logger.info("📊 Already at last slide")
            return {
                **self.get_current_slide(),
                "message": "Already at the last slide"
            }
    
    def previous_slide(self) -> Dict[str, Any]:
        """Move to the previous slide.
        
        Returns:
            New slide info or error if at beginning
        """
        if self.current_index > 0:
            self.current_index -= 1
            logger.info(f"📊 Moved back to slide {self.current_slide_number}")
            return self.get_current_slide()
        else:
            logger.info("📊 Already at first slide")
            return {
                **self.get_current_slide(),
                "message": "Already at the first slide"
            }
    
    def goto_slide(self, number: int) -> Dict[str, Any]:
        """Jump to a specific slide.
        
        Args:
            number: Slide number (1-based)
            
        Returns:
            New slide info or error if invalid
        """
        if 1 <= number <= len(self.slides):
            self.current_index = number - 1
            logger.info(f"📊 Jumped to slide {number}")
            return self.get_current_slide()
        else:
            logger.warning(f"⚠️ Invalid slide number: {number}")
            return {
                "error": f"Invalid slide number: {number}. Valid range: 1-{len(self.slides)}",
                **self.get_current_slide()
            }
    
    def reset(self) -> None:
        """Reset to the first slide."""
        self.current_index = 0
        logger.info("📊 Reset to first slide")
