"""Tool/function schema definitions for the voice agent."""

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema


def create_function_schemas() -> dict:
    """Create and return all function schemas for slide navigation."""
    
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
    
    return {
        "next_slide": next_slide_function,
        "previous_slide": previous_slide_function,
        "goto_slide": goto_slide_function,
        "get_current_slide_content": get_current_slide_content_function,
    }


def create_tools_schema() -> ToolsSchema:
    """Create the ToolsSchema with all registered functions."""
    schemas = create_function_schemas()
    
    return ToolsSchema(
        standard_tools=list(schemas.values())
    )
