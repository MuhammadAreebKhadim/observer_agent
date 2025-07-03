# Observer Agent MVP


[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/) 


## 📁 Project Structure

- `bootstrap.py` — Automated setup and dependency management
- `recording.py` — Core screen recording functionality
- `recordings/` — Output directory for saved recordings
- `requirements.txt` — Python package dependencies

### 📋 ToDo's

- `summarize.py` — Use text LLM to summarize the recording
- `recall.py` — Use text LLM to recall the recording

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
