# Observer Agent MVP


[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/) 


## 📁 Project Structure

- `auto.py` — Main automation script for screen capture, screenshot, and logging
- `bootstrap.py` — Automated setup and dependency management
- `config.py` — Central configuration and environment variable loading
- `.env_exmaple` — Example environment variable file
- `requirements.txt` — Python package dependencies
- `README.md` — Project documentation
- `logs/` — Stores extracted relevant information and session logs
- `recordings/` — Output directory for saved recordings and screenshots
- `scripts/` — Helper scripts:
  - `recording.py` — Core screen recording functionality
  - `screenshot_take.py` — Take a screenshot (used in screenshot mode)
  - `extract_multiple_frames.py` — Extract frames from a video recording
  - `summarize_and_insert_logs.py` — Summarize screenshots and insert logs
  - `extract_image_from_video.py` — Extract a single frame from a video
  - `recall/` — Modular recall assistant system:
    - `__main__.py` — Main entry point for recall queries
    - `tools.py` — Tool implementations (search logs, read files, etc.)
    - `tool_schema.py` — Tool schema definitions for LLM function calling
    - `system_prompt.py` — System prompt for the recall assistant
    - `preprocess.py` — Natural language query preprocessing
  - Other supporting scripts
- `observer_agent_mvp_recorder.egg-info/` — Package metadata (if installed as a package)
- `__pycache__/` — Python bytecode cache
- `.gitignore` — Git ignore rules
- `.venv/` — Python virtual environment (if created)

### 📋 ToDo's

- `summarize_and_insert_logs.py` — Use text LLM to summarize the recording and insert the logs

---

## ⚡ Quickstart

### 1. Clone the Repository

```bash
git clone <repository-url>
cd observer-agent-mvp
```

### 2. Run the Bootstrap Installer

```bash
python bootstrap.py install
```

This will:
- Create a virtual environment automatically
- Install all required Python dependencies
- Handle system-specific setup (e.g., Wayland dependencies)
- Install `wf-recorder` for Linux Wayland users

---

## 🚀 Automation Usage (`auto.py`)

### Modes
- **CAPTURE_MODE**: Set in `.env` or environment. Options:
  - `recording`: Full screen recording workflow (default)
  - `screenshot`: Take a single screenshot and log it

### Continual Mode
- Run the workflow repeatedly with a delay:
  ```bash
  python auto.py --continually
  ```
- Delay is set by `AUTO_LOOP_DELAY` (seconds) in `.env` (default: 60)

### Session Log
- In continual mode, all logs for a session are saved in a single file (e.g., `logs/session_YYYYMMDD_HHMMSS.json`).
- Each log entry includes a `session_id` and `capture_mode` field.

---

## 🧠 Recall Assistant

The recall assistant is an AI-powered system that helps you search and analyze your activity logs using natural language queries.

### Usage

Run the recall assistant:
```bash
cd scripts
python -m recall
```

### Features

- **Natural Language Processing**: Ask questions like "what did I do today?", "show my activity yesterday", or "what happened in the last 3 hours?"
- **Smart Time Windows**: Understands relative time expressions like "yesterday", "last week", "past few hours", "before one day"
- **Multiple Search Tools**:
  - Search all logs by content
  - Search logs within specific time windows
  - Read specific log files
  - Search code files
  - Get current date/time
- **LLM-Powered Summarization**: Provides comprehensive summaries of your activities

### Example Queries

```
> what did I do today?
> show my activity yesterday
> what happened in the last 3 hours?
> find logs about automation
> what was I working on before one day?
> show recent activity
```

### Architecture

The recall system is modular with separate components:
- **Tools**: Implements search and file operations
- **Preprocessing**: Handles natural language time expressions
- **LLM Integration**: Uses Groq API for function calling and summarization
- **Schema**: Defines tool capabilities for the LLM

### Example `.env` settings
```
GROQ_API_KEY=your_groq_api_key_here
USE_MOCK_SUMMARY=False
SCREENSHOT_WAIT_TIME=0
CAPTURE_MODE=recording
AUTO_LOOP_DELAY=5
```