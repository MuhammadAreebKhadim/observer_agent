import os
import sys

# ── Make the project root visible so `import config` works from inside scripts/ ──
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Now it’s safe to import your top-level modules ──
import re
import json
import base64
import mimetypes
from datetime import datetime, timedelta

from groq import Groq
from config import GROQ_API_KEY, USE_MOCK_SUMMARY, CAPTURE_MODE

# ── Rest of your setup ──
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

def image_to_data_url(image_path):
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        raise ValueError(f"Could not determine MIME type for {image_path}")
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

with open(os.path.join(SCRIPT_DIR, "system_prompt.txt"), "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

def main(image_path, session_log_path=None, session_id=None):
    # extract frame timestamp
    base = os.path.splitext(os.path.basename(image_path))[0]
    match = re.search(r'recording_(\d{8})_(\d{6})_frame_(\d+)$', base)
    frame_number = None
    frame_timestamp = None
    if match:
        date_str, time_str, frame_str = match.groups()
        frame_number = int(frame_str)
        start_time = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        FPS = 20
        frame_offset = timedelta(seconds=frame_number / FPS)
        frame_timestamp = (start_time + frame_offset).isoformat()

    if USE_MOCK_SUMMARY:
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
    else:
        if not GROQ_API_KEY:
            print("[ERROR] GROQ_API_KEY not set in environment or .env file.")
            sys.exit(1)
        data_url = image_to_data_url(image_path)
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": ""},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]}
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
        )
        output = ""
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            print(content, end="")
            output += content

        # Try to save output as JSON
        try:
            output = output.strip()
            parsed = json.loads(output)
        except (ValueError, json.JSONDecodeError) as e:
            # Fallback: wrap the entire raw output in a JSON object
            print(f"\n[INFO] Output wasn’t valid JSON, saving raw under 'raw_summary'. Error: {e}")
            parsed = [{
                "raw_summary": output,
                "capture_mode": CAPTURE_MODE,
            }]

    # Post-process each entry
    for entry in parsed:
        entry.setdefault("type", "screenshot")
        entry.setdefault("duration", "1 frame")
        if frame_number is not None:
            entry["frame"] = frame_number
        if frame_timestamp is not None:
            entry["timestamp"] = frame_timestamp
        entry["capture_mode"] = CAPTURE_MODE
        if session_id:
            entry["session_id"] = session_id

    # Save to logs
    if session_log_path:
        if os.path.exists(session_log_path):
            with open(session_log_path, "r", encoding="utf-8") as f:
                try:
                    session_data = json.load(f)
                except Exception:
                    session_data = []
        else:
            session_data = []
        session_data.extend(parsed)
        with open(session_log_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)
        print(f"\n[INFO] Appended summary to session log {session_log_path}")
    else:
        out_path = os.path.join(LOGS_DIR, f"{base}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)
        print(f"\n[INFO] Saved summary to {out_path}")

if __name__ == "__main__":
    argc = len(sys.argv)
    if argc == 2:
        main(sys.argv[1])
    elif argc == 3:
        main(sys.argv[1], sys.argv[2])
    elif argc == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print(f"Usage: python {os.path.basename(__file__)} <image_path> [session_log_path] [session_id]")
        sys.exit(1)
