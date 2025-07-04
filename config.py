import os
from dotenv import load_dotenv

# Load environment variables from .env file at the root of the project
load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Note: GROQ_API_KEY check moved to runtime for serverless compatibility

# USE_MOCK_SUMMARY controls whether to use mock summary data for logs instead of calling the real API.
USE_MOCK_SUMMARY = os.getenv("USE_MOCK_SUMMARY", "False").lower() in ("1", "true", "yes")

# SCREENSHOT_WAIT_TIME controls the delay (in seconds) before taking a screenshot
SCREENSHOT_WAIT_TIME = float(os.getenv("SCREENSHOT_WAIT_TIME", "0"))

# CAPTURE_MODE controls whether automation runs in 'screenshot' or 'recording' mode
CAPTURE_MODE = os.getenv("CAPTURE_MODE", "recording").lower()

# AUTO_LOOP_DELAY controls the delay (in seconds) between runs in continual mode
AUTO_LOOP_DELAY = float(os.getenv("AUTO_LOOP_DELAY", "60"))