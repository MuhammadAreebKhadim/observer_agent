import os
import sys
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now import config
from config import GROQ_API_KEY, USE_MOCK_SUMMARY, CAPTURE_MODE
import json
from groq import Groq
import base64
import mimetypes

# Ensure logs directory exists
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Helper to encode image as data URL
def image_to_data_url(image_path):
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        raise ValueError(f"Could not determine MIME type for {image_path}")
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

# Read system prompt from external file
with open(os.path.join(SCRIPT_DIR, "system_prompt.txt"), "r") as f:
    SYSTEM_PROMPT = f.read()

def main(image_path, session_log_path=None, session_id=None):
    import re
    import json
    from datetime import datetime, timedelta
    # Extract frame number and start time from filename
    base = os.path.splitext(os.path.basename(image_path))[0]
    match = re.search(r'recording_(\d{8})_(\d{6})_frame_(\d+)$', base)
    frame_number = None
    frame_timestamp = None
    if match:
        date_str, time_str, frame_str = match.groups()
        frame_number = int(frame_str)
        start_time = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        FPS = 20  # Default FPS, adjust if needed
        frame_offset = timedelta(seconds=frame_number / FPS)
        frame_timestamp = (start_time + frame_offset).isoformat()

    if USE_MOCK_SUMMARY:
        # Use mock summary data
        parsed = [{
            "timestamp": frame_timestamp or datetime.now().isoformat(),
            "duration": "1 frame",
            "summary": f"Mock summary for frame {frame_number}",
            "type": "screenshot",
            "frame": frame_number,
            "context": {
                "active_window": "MockApp",
                "intent": "Testing mock summary",
                "environment": "mock"
            }
        }]
        print(json.dumps(parsed, indent=2))
    else:
        if not GROQ_API_KEY:
            print("[ERROR] GROQ_API_KEY not set in environment or .env file.")
            sys.exit(1)
        data_url = image_to_data_url(image_path)
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ""},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        output = ""
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            print(content, end="")
            output += content
        # Try to save output as JSON
        try:
            # Remove any leading/trailing whitespace
            output = output.strip()
            # Parse to ensure it's valid JSON
            parsed = json.loads(output)
            # Add type, correct duration, frame number, and timestamp for each entry
            for entry in parsed:
                entry["type"] = "screenshot"
                entry["duration"] = "1 frame"
                if frame_number is not None:
                    entry["frame"] = frame_number
                if frame_timestamp is not None:
                    entry["timestamp"] = frame_timestamp
                entry["capture_mode"] = CAPTURE_MODE
                if session_id:
                    entry["session_id"] = session_id
        except Exception as e:
            print(f"\n[WARNING] Could not save output as JSON: {e}")
            return

    # Save to logs directory
    if session_log_path:
        # Append to session log file as a JSON array
        if os.path.exists(session_log_path):
            with open(session_log_path, "r") as f:
                try:
                    session_data = json.load(f)
                except Exception:
                    session_data = []
        else:
            session_data = []
        # Add session_id to each entry if provided
        if session_id:
            for entry in parsed:
                entry["session_id"] = session_id
        session_data.extend(parsed)
        with open(session_log_path, "w") as f:
            json.dump(session_data, f, indent=2)
        print(f"\n[INFO] Appended summary to session log {session_log_path}")
    else:
        out_path = os.path.join(LOGS_DIR, f"{base}.json")
        with open(out_path, "w") as f:
            json.dump(parsed, f, indent=2)
        print(f"\n[INFO] Saved summary to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print(f"Usage: python {os.path.basename(__file__)} <screenshot_image_path> [session_log_path] [session_id]")
        sys.exit(1)
