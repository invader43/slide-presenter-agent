"""Voice agent with PDF slide viewer and content speaker.

This is the main entry point for the slide presenter agent.
The agent uses voice commands to navigate through PDF slides
and presents the content using OpenAI's realtime voice API.
"""

import asyncio
import os

from dotenv import load_dotenv
from loguru import logger

from config import DEFAULT_SLIDES_PATH, PDF_RENDER_DPI
from pdf_viewer import PDFSlideViewer
from handlers import set_viewer
from agent import VoiceAgent


load_dotenv()


async def main() -> None:
    """Main entry point for the voice agent."""
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Missing OPENAI_API_KEY in .env file")
        logger.info("Get your API key from: https://platform.openai.com/api-keys")
        return

    # Initialize and start PDF slide viewer UI
    logger.info("📊 Initializing PDF slide viewer UI...")
    viewer = PDFSlideViewer(DEFAULT_SLIDES_PATH, dpi=PDF_RENDER_DPI)
    
    if not viewer.slides:
        logger.error("No slides loaded! Please ensure slides.pdf exists.")
        return
    
    # Set the global viewer for handlers
    set_viewer(viewer)
    
    # Start the UI
    viewer.start()
    
    # Give UI time to initialize
    await asyncio.sleep(1)
    
    # Get initial slide info
    initial_slide = viewer.get_current_slide_info()
    
    # Create and run the voice agent
    voice_agent = VoiceAgent(api_key)
    await voice_agent.run(initial_slide)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down voice agent...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")