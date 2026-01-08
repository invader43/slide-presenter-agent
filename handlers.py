"""Function handlers for slide navigation."""

from typing import Optional, TYPE_CHECKING

from loguru import logger
from pipecat.services.llm_service import FunctionCallParams

from ui import PowerPointViewerUI

if TYPE_CHECKING:
    from silence_monitor import SilenceMonitor


# Global viewer instance - will be set by the agent
slide_viewer: Optional[PowerPointViewerUI] = None

# Global silence monitor reference - will be set by the agent
silence_monitor: Optional['SilenceMonitor'] = None


def set_viewer(viewer: PowerPointViewerUI) -> None:
    """Set the global slide viewer instance."""
    global slide_viewer
    slide_viewer = viewer


def set_silence_monitor(monitor: 'SilenceMonitor') -> None:
    """Set the global silence monitor reference."""
    global silence_monitor
    silence_monitor = monitor


def get_viewer() -> Optional[PowerPointViewerUI]:
    """Get the global slide viewer instance."""
    return slide_viewer


async def next_slide(params: FunctionCallParams) -> None:
    """Navigate to the next slide and return its content."""
    if slide_viewer:
        info = slide_viewer.next_slide()
        logger.info(f"📊 Next slide: {info.get('title', 'N/A')}")
        
        # Update silence monitor with last slide status
        if silence_monitor:
            is_last = not info.get('has_next', True)
            silence_monitor.set_last_slide_reached(is_last)
        
        await params.result_callback(info)
    else:
        await params.result_callback({"error": "Slide viewer not initialized"})


async def previous_slide(params: FunctionCallParams) -> None:
    """Navigate to the previous slide and return its content."""
    if slide_viewer:
        info = slide_viewer.previous_slide()
        logger.info(f"📊 Previous slide: {info.get('title', 'N/A')}")
        await params.result_callback(info)
    else:
        await params.result_callback({"error": "Slide viewer not initialized"})


async def goto_slide(params: FunctionCallParams) -> None:
    """Go to a specific slide by number and return its content."""
    slide_number = params.arguments.get("slide_number", 1)
    
    if slide_viewer:
        info = slide_viewer.goto_slide(slide_number)
        logger.info(f"📊 Go to slide {slide_number}: {info.get('title', 'N/A')}")
        
        # Update silence monitor with last slide status
        if silence_monitor and not info.get('error'):
            is_last = not info.get('has_next', True)
            silence_monitor.set_last_slide_reached(is_last)
        
        await params.result_callback(info)
    else:
        await params.result_callback({"error": "Slide viewer not initialized"})


async def get_current_slide_content(params: FunctionCallParams) -> None:
    """Get the full content of the current slide for speaking."""
    if slide_viewer:
        info = slide_viewer.get_current_slide_info()
        logger.info(f"📊 Current slide content requested: {info.get('title', 'N/A')}")
        await params.result_callback(info)
    else:
        await params.result_callback({"error": "Slide viewer not initialized"})
