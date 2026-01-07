"""Voice agent main entry point - FIXED VERSION."""

import asyncio
import os
from datetime import datetime

from loguru import logger
from dotenv import load_dotenv
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.openai.realtime.llm import OpenAIRealtimeLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.frames.frames import LLMRunFrame
from pipecat.services.openai.realtime.events import (
    AudioConfiguration,
    AudioInput,
    InputAudioTranscription,
    SemanticTurnDetection,
    SessionProperties,
)

load_dotenv()


# Fixed function signatures to use FunctionCallParams
async def show_toast(params: FunctionCallParams) -> None:
    """Display a toast notification to the user.
    
    Args:
        params: Function call parameters containing arguments and result callback.
    """
    message = params.arguments.get("message", "")
    toast_type = params.arguments.get("toast_type", "info")
    
    logger.info(f"🍞 TOAST NOTIFICATION [{toast_type.upper()}]: {message}")
    
    # Display the toast
    print("\n" + "="*60)
    print(f"🔔 TOAST NOTIFICATION")
    print(f"Type: {toast_type.upper()}")
    print(f"Message: {message}")
    print("="*60 + "\n")
    
    # Use result_callback to return the result
    await params.result_callback({
        "status": "shown",
        "type": toast_type,
        "message": message
    })


async def get_time(params: FunctionCallParams) -> None:
    """Get the current time.
    
    Args:
        params: Function call parameters containing result callback.
    """
    current_time = datetime.now().strftime("%I:%M %p")
    logger.info(f"⏰ Time requested: {current_time}")
    
    await params.result_callback({"time": current_time})


async def get_weather(params: FunctionCallParams) -> None:
    """Get the current weather.
    
    Args:
        params: Function call parameters containing result callback.
    """
    logger.info(f"☀️ Weather requested: Sunny")
    
    await params.result_callback({"weather": "sunny", "temperature": "72°F"})


async def main() -> None:
    """Main entry point for the voice agent."""
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("Missing OPENAI_API_KEY in .env file")
        logger.info("Get your API key from: https://platform.openai.com/api-keys")
        return

    logger.info("🎤 Initializing local microphone transport...")
    
    # Use local audio transport (connects to your PC mic and speakers)
    transport = LocalAudioTransport(
        params=LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        )
    )

    logger.info("🤖 Initializing OpenAI Realtime Service...")
    
    # Define function schemas
    show_toast_function = FunctionSchema(
        name="show_toast",
        description="Display a toast notification to the user",
        properties={
            "message": {
                "type": "string",
                "description": "The message to display in the toast notification",
            },
            "toast_type": {
                "type": "string",
                "enum": ["success", "error", "warning", "info"],
                "description": "Type of toast notification",
            },
        },
        required=["message"],
    )
    
    get_time_function = FunctionSchema(
        name="get_time",
        description="Get the current time",
        properties={},
        required=[],
    )
    
    get_weather_function = FunctionSchema(
        name="get_weather",
        description="Get the current weather",
        properties={},
        required=[],
    )
    
    # Create tools schema
    tools = ToolsSchema(
        standard_tools=[show_toast_function, get_time_function, get_weather_function]
    )
    
    # Set up session properties with instructions
    session_properties = SessionProperties(
        audio=AudioConfiguration(
            input=AudioInput(
                transcription=InputAudioTranscription(),
                turn_detection=SemanticTurnDetection(),
            )
        ),
        instructions="""You are a helpful voice assistant with the ability to show toast notifications.

When the user asks you to show a notification or toast, use the show_toast function.
Choose the appropriate toast type based on the context:
- success: For positive outcomes, completions, confirmations
- error: For errors, failures, problems
- warning: For warnings, cautions, alerts
- info: For general information, neutral messages

You can also tell the user the current time using the get_time function.
You can tell the user the weather using the get_weather function.

Be conversational and helpful. Keep responses concise since this is a voice interface.
Start by greeting the user and letting them know what you can do."""
    )
    
    # Initialize OpenAI Realtime Service with session properties
    realtime = OpenAIRealtimeLLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-realtime-preview-2024-12-17",
        voice="alloy",
        session_properties=session_properties,
    )

    # Register the functions with their handlers
    realtime.register_function("show_toast", show_toast)
    realtime.register_function("get_time", get_time)
    realtime.register_function("get_weather", get_weather)
    
    # Create LLM context with tools
    context = LLMContext(
        messages=[],
        tools=tools,
    )
    
    # Create context aggregator
    context_aggregator = LLMContextAggregatorPair(context)

    # Create the pipeline with context aggregators
    pipeline = Pipeline([
        transport.input(),
        context_aggregator.user(),
        realtime,
        transport.output(),
        context_aggregator.assistant(),
    ])

    # Create and run the task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        )
    )
    
    # Event handler for when transport is ready
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected - starting conversation")
        await task.queue_frames([LLMRunFrame()])
    
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    logger.info("✅ Voice agent ready!")
    logger.info("🎤 Listening on your microphone...")
    logger.info("💡 Try saying: 'Show me a success toast that says hello world'")
    logger.info("💡 Or: 'What time is it?'")
    logger.info("💡 Or: 'What's the weather?'")
    logger.info("🛑 Press Ctrl+C to stop")
    print()

    runner = PipelineRunner()
    await runner.run(task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down voice agent...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")