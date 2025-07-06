import os
import sys
import re
import json
import base64
import mimetypes
from datetime import datetime, timedelta

# ensure project root is on PYTHONPATH so imports work
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from groq import Groq
from config import GROQ_API_KEY, USE_MOCK_SUMMARY, CAPTURE_MODE
from snowflake_db import insert_logs

# prepare logs directory
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
    # --- extract frame timestamp from filename ---
    base = os.path.splitext(os.path.basename(image_path))[0]
    match = re.search(r'recording_(\d{8})_(\d{6})_frame_(\d+)$', base)
    frame_number = frame_timestamp = None
    if match:
        date_str, time_str, frame_str = match.groups()
        frame_number = int(frame_str)
        start_time = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        FPS = 20
        frame_timestamp = (start_time + timedelta(seconds=frame_number/FPS)).isoformat()

    # --- call LLM or mock summary ---
    if USE_MOCK_SUMMARY:
        parsed = [{
            "timestamp": frame_timestamp or datetime.now().isoformat(),
            "duration": "1 frame",
            "raw_summary": f"Mock summary for frame {frame_number}",
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
            print("[ERROR] GROQ_API_KEY not set.")
            sys.exit(1)
        data_url = image_to_data_url(image_path)
        client = Groq(api_key=GROQ_API_KEY)
        # → Non‐streaming call for clean JSON output
        response = client.chat.completions.create(
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
            stream=False,  # turn off streaming
        )
        # Grab the full JSON response
        output = response.choices[0].message.content or ""
        print(output)    # still print it for debugging


        # ── 1) Strip out any <|…|> tokens ──
        output = re.sub(r'<\|header_start\|>.*?<\|header_end\|>', '', output, flags=re.DOTALL)
        output = re.sub(r'<\|[^\|]+\|>', '', output)

        # ── 2) Normalize malformed timestamps ──
        output = re.sub(
            r'(\d{4}-\d{2}-\d{2})\s*([0-2]\d:[0-5]\d)(?::[0-5]\d(?:\.\d+)?)?',
            r'\1T\2:00',
            output
        )

        # ── 3) Extract the JSON array ──
        start = output.find('[')
        end   = output.rfind(']')
        if start != -1 and end > start:
            json_text = output[start:end+1]
        else:
            json_text = output

        # ── 4) Parse or fallback ──
        try:
            parsed = json.loads(json_text)
            if not isinstance(parsed, list):
                parsed = [parsed]
        except json.JSONDecodeError as e:
            print(f"\n[INFO] Could not parse JSON payload: {e}")
            cleaned = output.replace('\n', ' ').strip()
            parsed = [{"raw_summary": cleaned}]

    # --- post‐process each entry ---
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
        # ── flatten raw_summary for Snowflake ──
        if "raw_summary" in entry:
            entry["raw_summary"] = entry["raw_summary"].replace('\n', ' ').strip()

    # --- insert into Snowflake ---
    try:
        insert_logs(parsed)
        print(f"[INFO] Inserted {len(parsed)} rows into Snowflake.")
    except Exception as e:
        print(f"[WARNING] Snowflake insert failed: {e}")

    # --- then save locally as before ---
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
    args = sys.argv[1:]
    if len(args) in (1, 2, 3):
        main(*args)
    else:
        print(f"Usage: python {os.path.basename(__file__)} <image_path> [session_log_path] [session_id]")
        sys.exit(1)
