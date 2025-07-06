import os
import sys
import shutil

# ─── Project Path Setup ────────────────────────────────────
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT  = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─── Clear Out Old Screenshots ─────────────────────────────
RECORDINGS_DIR   = os.path.join(PROJECT_ROOT, 'recordings')
SCREENSHOTS_DIR  = os.path.join(RECORDINGS_DIR, 'screenshots')
shutil.rmtree(SCREENSHOTS_DIR, ignore_errors=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ─── Imports for Frame Extraction ──────────────────────────
from extract_image_from_video import extract_frame, get_total_frames

# ─── Configuration ─────────────────────────────────────────
NUM_FRAMES = 5  # how many frames to grab

def extract_frames_from_video(video_path: str, out_dir: str, num_frames: int = NUM_FRAMES):
    total = get_total_frames(video_path)
    if total <= 0:
        print(f"[ERROR] Could not open video: {video_path}")
        return

    # pick evenly spaced frame indices
    if total < num_frames:
        indices = list(range(total))
    else:
        indices = [int(i * total / num_frames) for i in range(num_frames)]

    base = os.path.splitext(os.path.basename(video_path))[0]
    for frame_num in indices:
        out_path = os.path.join(out_dir, f"{base}_frame_{frame_num}.jpg")
        extract_frame(video_path, out_path, frame_num)

def main():
    # Find all .mp4s in recordings/ and pick the newest one
    mp4s = [
        os.path.join(RECORDINGS_DIR, f)
        for f in os.listdir(RECORDINGS_DIR)
        if f.lower().endswith('.mp4')
    ]
    if not mp4s:
        print("[INFO] No recordings found.")
        return

    latest_video = max(mp4s, key=os.path.getctime)
    print(f"[INFO] Extracting frames from latest recording: {latest_video}")
    extract_frames_from_video(latest_video, SCREENSHOTS_DIR, NUM_FRAMES)

if __name__ == "__main__":
    main()
