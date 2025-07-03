# Observer Agent MVP

## Files

- `recording.py` - Core screen recording functionality
- `summary.py` - Content analysis and text extraction
  - OCR for text extraction (pytesseract, easyocr, trocr)
  - Vision LLM integration for intelligent analysis
- `bootstrap.py` - Automated setup and dependency management
- `requirements.txt` - Python package dependencies

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd observer-agent-mvp
   ```

2. **Run the bootstrap installer**:
   ```bash
   python bootstrap.py install
   ```

   This will:
   - Create a virtual environment automatically
   - Install all required Python dependencies
   - Handle system-specific setup (e.g., Wayland dependencies)
   - Install wf-recorder for Linux Wayland users
