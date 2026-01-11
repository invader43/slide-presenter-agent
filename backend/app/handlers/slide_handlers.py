"""LLM function handlers for slide navigation."""

from typing import Callable, Dict, Any

from loguru import logger
from pipecat.services.llm_service import FunctionCallParams
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

from ..services.slide_service import SlideService


def create_slide_handlers(slide_service: SlideService) -> Dict[str, Callable]:
    """Create function handlers bound to a slide service instance.
    
    Args:
        slide_service: The slide service instance to use
        
    Returns:
        Dictionary of handler name to handler function
    """
    
    async def next_slide(params: FunctionCallParams) -> None:
        """Navigate to the next slide and return its content."""
        info = slide_service.next_slide()
        logger.info(f"📊 Next slide: {info.get('title', 'N/A')}")
        await params.result_callback(info)
    
    async def previous_slide(params: FunctionCallParams) -> None:
        """Navigate to the previous slide and return its content."""
        info = slide_service.previous_slide()
        logger.info(f"📊 Previous slide: {info.get('title', 'N/A')}")
        await params.result_callback(info)
    
    async def goto_slide(params: FunctionCallParams) -> None:
        """Go to a specific slide by number and return its content."""
        slide_number = params.arguments.get("slide_number", 1)
        info = slide_service.goto_slide(slide_number)
        logger.info(f"📊 Go to slide {slide_number}: {info.get('title', 'N/A')}")
        await params.result_callback(info)
    
    async def get_current_slide_content(params: FunctionCallParams) -> None:
        """Get the full content of the current slide for speaking."""
        info = slide_service.get_current_slide()
        logger.info(f"📊 Current slide content requested: {info.get('title', 'N/A')}")
        await params.result_callback(info)
    
    return {
        "next_slide": next_slide,
        "previous_slide": previous_slide,
        "goto_slide": goto_slide,
        "get_current_slide_content": get_current_slide_content,
    }


def create_tools_schema() -> ToolsSchema:
    """Create the ToolsSchema with all registered functions."""
    
    next_slide_function = FunctionSchema(
        name="next_slide",
        description="Navigate to the next slide and get its content",
        properties={},
        required=[],
    )
    
    previous_slide_function = FunctionSchema(
        name="previous_slide",
        description="Navigate to the previous slide and get its content",
        properties={},
        required=[],
    )
    
    goto_slide_function = FunctionSchema(
        name="goto_slide",
        description="Go to a specific slide by its number (1-based index)",
        properties={
            "slide_number": {
                "type": "integer",
                "description": "The slide number to navigate to (1 for first slide, 2 for second, etc.)",
            }
        },
        required=["slide_number"],
    )
    
    get_current_slide_content_function = FunctionSchema(
        name="get_current_slide_content",
        description="Get the complete content and information about the currently displayed slide",
        properties={},
        required=[],
    )
    
    return ToolsSchema(
        standard_tools=[
            next_slide_function,
            previous_slide_function,
            goto_slide_function,
            get_current_slide_content_function,
        ]
    )
