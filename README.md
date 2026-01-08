# 🎤 Slide Presenter Agent

A voice-controlled PowerPoint presentation tool powered by OpenAI's Realtime Voice API and Pipecat framework.

## ✨ Features

- **Voice Navigation**: Navigate slides using natural voice commands
- **AI Narration**: AI presents slide content in a conversational manner  
- **Q&A Support**: Ask questions about slide content anytime
- **Visual Display**: Tkinter-based slide viewer with content display
- **Real-time Interaction**: Low-latency voice-to-voice communication
- **🆕 Auto-Advance**: Automatically moves to the next slide if you don't respond (configurable)

## 📋 Prerequisites

- **Python**: 3.12+
- **OpenAI API Key**: With access to the Realtime API
- **Audio Hardware**: Working microphone and speakers
- **Windows/macOS/Linux**: Tested on Windows

## 🚀 Installation

### 1. Clone the Repository

```bash
cd slide-presenter-agent
```

### 2. Create Virtual Environment (Recommended)

Using `uv` (recommended):
```bash
uv venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/macOS
```

Or using `venv`:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/macOS
```

### 3. Install Dependencies

Using `uv`:
```bash
uv sync
```

Or using `pip`:
```bash
pip install -e .
```

### 4. Configure Environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### 5. Add Your Slides

Place your PowerPoint file as `slides.pptx` in the project root, or modify `config.py` to point to your file:

```python
DEFAULT_SLIDES_PATH = "./your-presentation.pptx"
```

## 🎮 Running the Agent

```bash
python main.py
```

### What Happens on Start:

1. **Slide Viewer Window** opens showing the first slide
2. **Voice Agent** starts listening on your microphone
3. **AI begins presenting** the first slide automatically
4. After presenting, AI asks: *"Do you have any questions?"*
5. **If you stay silent** for 10 seconds, AI automatically advances to the next slide

## 🗣️ Voice Commands

| Command | Action |
|---------|--------|
| "Next slide" or "Next" | Move to next slide |
| "Previous slide" or "Go back" | Move to previous slide |
| "Go to slide 3" | Jump to slide 3 |
| Ask any question | AI answers based on slide content |

## ⏰ Auto-Advance Feature

The agent will automatically advance to the next slide if you don't respond within a configurable timeout period (default: 10 seconds).

### How It Works:
1. AI finishes presenting a slide and asks for questions
2. A silence timer starts (10 seconds by default)
3. If you speak, the timer resets
4. If you stay silent, AI smoothly transitions to the next slide
5. On the last slide, AI concludes the presentation instead

### Configuration

Edit `config.py` to customize auto-advance behavior:

```python
# Enable/disable auto-advance
AUTO_ADVANCE_ENABLED = True

# Seconds of silence before auto-advancing
AUTO_ADVANCE_TIMEOUT_SECONDS = 10.0
```

## ⌨️ Controls

- **Ctrl+C**: Stop the voice agent
- **UI Buttons**: Click Previous/Next for manual navigation

## 📁 Project Structure

```
slide-presenter-agent/
├── main.py              # Entry point
├── agent.py             # Voice agent pipeline
├── config.py            # Configuration
├── handlers.py          # Slide navigation handlers
├── tools.py             # Function schemas
├── ui.py                # Tkinter slide viewer
├── models.py            # Data models
├── silence_monitor.py   # Auto-advance timer logic
├── processors.py        # Speech event detection
├── slides.pptx          # Your presentation
└── .env                 # API key (create this)
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
OPENAI_MODEL = "gpt-4o-realtime-preview-2024-12-17"  # Model version
OPENAI_VOICE = "alloy"  # Voice: alloy, echo, fable, onyx, nova, shimmer
DEFAULT_SLIDES_PATH = "./slides.pptx"  # Slides file path

# Auto-advance settings
AUTO_ADVANCE_ENABLED = True
AUTO_ADVANCE_TIMEOUT_SECONDS = 10.0
```

## 📖 Documentation

- [Architecture Documentation](./ARCHITECTURE.md) - Detailed flow and component breakdown
- [Auto-Advance Ideas](./AUTO_ADVANCE_IDEAS.md) - Design decisions and alternatives

## 🐛 Troubleshooting

### "Missing OPENAI_API_KEY"
Ensure your `.env` file exists and contains a valid API key.

### No Audio Input/Output
- Check your default microphone and speaker settings
- Ensure no other application is using the microphone

### "No slides loaded"
- Verify `slides.pptx` exists in the project root
- Check the file path in `config.py`

### Auto-advance not working
- Verify `AUTO_ADVANCE_ENABLED = True` in `config.py`
- Check logs for "Silence timer" messages

## 📄 License

MIT License